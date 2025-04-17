import asyncio
import json
import random
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

import instructor
import litellm
import rich
from aiolimiter import AsyncLimiter
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from tqdm import tqdm

from aiai.utils import setup_django

if TYPE_CHECKING:
    from aiai.app.models import FunctionInfo


class SynPrompt(BaseModel):
    prompt: str = Field(
        description="A highly detailed and thoughtful prompt for generating a single synthetic datum."  # noqa: E501
    )


@dataclass
class SynDataGenerator:
    min_n: int = 64
    max_concurrency: int = 24
    seed: int = 42
    prompt_model: str = "openai/o4-mini"
    data_model: str = "openai/gpt-4.1-mini"

    def __post_init__(self):
        self.lm = instructor.from_litellm(litellm.acompletion)
        self.limiter = AsyncLimiter(self.max_concurrency)

    async def prompt(
        self,
        fns: list["FunctionInfo"],
        examples: list[str] | None = None,
    ) -> str:
        sys_prompt = dedent(
            """\
            You're an expert AI engineer looking at source code for an agent.
            Your task is to generate a highly detailed and thoughtful prompt for generating
            synthetic data to be used for testing the agent.
            """
        )
        source_code = "\n".join([fn.source_code for fn in fns])
        source_code = dedent(
            f"""\
            Here is my source code:
            <source_code>
            {source_code}
            </source_code>
            """
        )
        examples = (
            f"Here are some examples of my input data: <examples>\n{examples}\n</examples>"
            if examples
            else ""
        )
        syn_prompt = await self.lm.create(
            model=self.prompt_model,
            response_model=SynPrompt,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": source_code},
                *([{"role": "user", "content": examples}] if examples else []),
                {"role": "system", "content": sys_prompt},
            ],
        )
        return syn_prompt.prompt

    async def datum(self, prompt: str) -> str:
        async with self.limiter:
            return await self.lm.create(
                model=self.data_model,
                messages=[{"role": "system", "content": prompt}],
                temperature=1,
                seed=random.randint(0, 1_000_000),
                response_model=str,
            )

    async def data(self, prompt: str) -> list[str]:
        tasks = [self.datum(prompt) for _ in range(self.min_n)]
        data = "\n".join(
            [await t for t in tqdm(asyncio.as_completed(tasks), total=self.min_n)]
        )
        return await self.lm.create(
            model=self.data_model,
            messages=[
                {
                    "role": "system",
                    "content": dedent(
                        f"""\
                        Combine the following data into a single list of data:
                        <data>
                        {data}
                        </data>
                        """
                    ),
                }
            ],
            response_model=list[str],
        )


async def _cli(
    output: Path = Path("./synthetic_data.json"),
    min_n: int = 64,
    max_concurrency: int = 24,
    seed: int = 42,
):
    generator = SynDataGenerator(min_n, max_concurrency, seed)

    rich.print("Loading function info...", end=" ")
    from aiai.app.models import FunctionInfo

    fns = [fn async for fn in FunctionInfo.objects.all()]
    rich.print(f"{len(fns)} functions loaded.")

    rich.print("Generating synthetic prompt...", end=" ")
    prompt = await generator.prompt(fns)
    rich.print("done.")
    rich.print("<prompt>")
    rich.print(prompt)
    rich.print("</prompt>")

    rich.print("Generating synthetic data with config:", end=" ")
    rich.print_json(vars(generator), indent=None)
    data = await generator.data(prompt)
    rich.print(f"Generated {len(data)} synthetic examples.")

    rich.print("Saving synthetic data...", end=" ")
    with output.open("w", encoding="utf-8") as f:
        json.dump({"prompt": prompt, "data": data}, f, indent=2, ensure_ascii=False)
    rich.print(f"done.\nSaved {len(data)} synthetic examples to {output}")


def cli(
    output: Path = Path("./synthetic_data.json"),
    min_n: int = 64,
    max_concurrency: int = 24,
    seed: int = 42,
):
    load_dotenv()
    setup_django()
    asyncio.run(_cli(output, min_n, max_concurrency, seed))
