import asyncio
import json
import random
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

import instructor
import litellm
import rich
from aiolimiter import AsyncLimiter
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from sorcery import dict_of
from tqdm import tqdm

from aiai.async_typer import AsyncTyper
from aiai.utils import setup_django

if TYPE_CHECKING:
    from aiai.app.models import FunctionInfo


class SynPrompt(BaseModel):
    prompt: str = Field(
        description="A highly detailed and thoughtful prompt for generating a single synthetic datum."
    )


async def generate_synthetic_prompt(
    fns: list["FunctionInfo"],
    examples: list[str] | None = None,
) -> str:
    source_code = "\n".join([fn.source_code for fn in fns])
    lm = instructor.from_litellm(litellm.acompletion)
    syn_prompt = await lm.create(
        model="openai/o4-mini",
        response_model=SynPrompt,
        messages=[
            {
                "role": "system",
                "content": "You're an expert AI engineer looking at source code for an agent. Your task is to "
                           "generate a highly detailed and thoughtful prompt for generating synthetic data to be used "
                           "for testing the agent.",
            },
            {
                "role": "user",
                "content": f"Here is my source code: <source_code>\n{source_code}\n</source_code>",
            },
            *(
                [
                    {
                        "role": "user",
                        "content": f"Here are some examples of my input data: <examples>\n{examples}\n</examples>",
                    }
                ]
                if examples
                else []
            ),
            {
                "role": "system",
                "content": "You're an expert AI engineer looking at source code for an agent. Your task is to "
                           "generate a highly detailed and thoughtful prompt for generating synthetic data to be used "
                           "for testing the agent.",
            },
        ],
    )
    return syn_prompt.prompt


async def generate_synthetic_data(
    prompt: str,
    min_n: int = 64,
    max_concurrency: int = 24,
) -> list[str]:
    lm = instructor.from_litellm(litellm.acompletion)
    limiter = AsyncLimiter(max_concurrency)

    async def generate_datum() -> str:
        async with limiter:
            return await lm.create(
                model="openai/gpt-4.1-mini",
                messages=[{"role": "system", "content": prompt}],
                temperature=1,
                seed=random.randint(0, 1_000_000),
                response_model=str,
            )

    tasks = [generate_datum() for _ in range(min_n)]
    data = "\n".join([await t for t in tqdm(asyncio.as_completed(tasks), total=min_n)])
    return await lm.create(
        model="openai/gpt-4.1-mini",
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


cli = AsyncTyper()


@cli.command()
async def main(
    output: Path = Path("./synthetic_data.json"),
    min_n: int = 64,
    max_concurrency: int = 24,
    seed: int = 42,
):
    from aiai.app.models import FunctionInfo

    config = dict_of(min_n, max_concurrency)
    random.seed(seed)

    rich.print("Loading function info...", end=" ")
    fns = [fn async for fn in FunctionInfo.objects.all()]
    rich.print(f"{len(fns)} functions loaded.")

    rich.print("Generating synthetic prompt...", end=" ")
    prompt = await generate_synthetic_prompt(fns)
    rich.print("done.")
    rich.print("<prompt>")
    rich.print(prompt)
    rich.print("</prompt>")

    rich.print("Generating synthetic data with config:", end=" ")
    rich.print_json(data=config, indent=None)
    data = await generate_synthetic_data(prompt, **config)
    rich.print(f"Generated {len(data)} synthetic examples.")

    rich.print("Saving synthetic data...", end=" ")
    with output.open("w", encoding="utf-8") as f:
        json.dump({"prompt": prompt, "data": data}, f, indent=2, ensure_ascii=False)
    rich.print(f"done.\nSaved {len(data)} synthetic examples to {output}")


if __name__ == "__main__":
    load_dotenv()
    setup_django()
    cli()
