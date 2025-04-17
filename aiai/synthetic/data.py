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
from pydantic import BaseModel, Field
from tqdm import tqdm

from aiai.synthetic.utils import prepare_messages

if TYPE_CHECKING:
    from aiai.app.models import FunctionInfo


class SynPrompt(BaseModel):
    prompt: str = Field(
        description="A highly detailed and thoughtful prompt for generating a single synthetic datum."  # noqa: E501
    )


@dataclass
class DataGenerator:
    min_n: int = 64
    max_concurrency: int = 24
    seed: int = 42
    prompt_model: str = "openai/o4-mini"
    data_model: str = "openai/gpt-4.1-mini"
    sys_prompt: str = dedent(
        """\
        You're an expert AI engineer looking at source code for an agent.
        Your task is to generate a highly detailed and thoughtful prompt for
        generating synthetic data to be used for testing the agent.
        """
    )

    def __post_init__(self):
        self.lm = instructor.from_litellm(litellm.acompletion)
        self.limiter = AsyncLimiter(self.max_concurrency)

    async def prompt(
        self,
        fns: list["FunctionInfo"],
        examples: list[str] | None = None,
    ) -> str:
        messages = prepare_messages(self.sys_prompt, fns, examples)
        syn_prompt = await self.lm.create(
            model=self.prompt_model,
            response_model=SynPrompt,
            messages=messages,
        )
        return syn_prompt.prompt

    async def _datum(self, prompt: str) -> str:
        async with self.limiter:
            return await self.lm.create(
                model=self.data_model,
                messages=[{"role": "system", "content": prompt}],
                temperature=1,
                seed=random.randint(0, 1_000_000),
                response_model=str,
            )

    async def data(self, prompt: str) -> list[str]:
        tasks = [self._datum(prompt) for _ in range(self.min_n)]
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


async def cli(
    output: Path,
    min_n: int = 64,
    max_concurrency: int = 24,
    seed: int = 42,
):
    generator = DataGenerator(min_n, max_concurrency, seed)

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
