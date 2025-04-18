from dataclasses import dataclass
from textwrap import dedent
from typing import TYPE_CHECKING

import instructor
import litellm
from pydantic import BaseModel, Field

from aiai.synthesizer.utils import get_examples, prepare_messages

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

    def perform(self):
        from aiai.app.models import FunctionInfo, SyntheticDatum

        fns = list(FunctionInfo.objects.all())
        examples = get_examples(fns)

        prompt = self.prompt(fns, examples)
        data = SyntheticDatum.objects.bulk_create(self.data(prompt))

        return prompt, data
