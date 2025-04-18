import json
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

import instructor
import litellm
import rich
from pydantic import BaseModel, Field

from aiai.synthetic.utils import get_examples, prepare_messages

if TYPE_CHECKING:
    from aiai.app.models import FunctionInfo, SyntheticDatum


class SynPrompt(BaseModel):
    prompt: str = Field(
        description="A highly detailed and thoughtful prompt for generating a single synthetic datum."  # noqa: E501
    )
    examples: list[str] = Field(description="A list of examples of the synthetic data to be generated.")

    def __str__(self):
        return dedent(
            f"""\
            <instructions>
            {self.prompt}
            </instructions>
            <examples>
            {self.examples}
            </examples>
            """
        )


@dataclass
class DataGenerator:
    examples: int
    seed: int
    prompt_model: str = "openai/o4-mini"
    data_model: str = "openai/gpt-4.1-mini"
    sys_prompt: str = dedent(
        """\
        You're an expert AI engineer looking at source code for an agent.
        Your task is to generate a highly detailed and thoughtful prompt for
        generating synthetic data to be used for testing the agent.
        """
    )

    def prompt(
        self,
        fns: list["FunctionInfo"],
        examples: list[str] | None = None,
    ) -> str:
        messages = prepare_messages(self.sys_prompt, fns, examples)
        syn_prompt = instructor.from_litellm(litellm.completion).create(
            model=self.prompt_model,
            response_model=SynPrompt,
            messages=messages,
        )
        return str(syn_prompt)

    def data(self, prompt: str) -> list["SyntheticDatum"]:
        from aiai.app.models import SyntheticDatum

        response = litellm.completion(
            model=self.data_model,
            messages=[{"role": "system", "content": prompt}],
            temperature=1,
            n=self.examples,
            seed=self.seed,
        )
        return [SyntheticDatum(input_data=r.message.content) for r in response.choices]


def cli(output: Path, examples: int, seed: int):
    generator = DataGenerator(examples, seed)

    rich.print("Loading function info...", end=" ")
    from aiai.app.models import FunctionInfo

    fns = list(FunctionInfo.objects.all())
    rich.print(f"{len(fns)} functions loaded.")

    if examples := get_examples(fns):
        rich.print("Found examples:")
        rich.print_json(data=examples)

    rich.print("Generating synthetic data prompt...", end=" ")
    prompt = generator.prompt(fns, examples)
    rich.print("done.")
    rich.print("<prompt>")
    rich.print(prompt)
    rich.print("</prompt>")

    rich.print("Generating synthetic data...", end=" ")
    data = generator.data(prompt)
    rich.print(f"Generated {len(data)} synthetic examples.")

    rich.print("Saving synthetic data...", end=" ")
    with output.open("w", encoding="utf-8") as f:
        json.dump({"prompt": prompt, "data": data}, f, indent=2, ensure_ascii=False)
    rich.print(f"done.\nSaved {len(data)} synthetic examples to {output}")

    return prompt, data
