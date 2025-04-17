import asyncio
from dataclasses import dataclass
from textwrap import dedent
from typing import TYPE_CHECKING

import instructor
import litellm
import rich
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from aiai.utils import prepare_messages, setup_django

if TYPE_CHECKING:
    from aiai.app.models import FunctionInfo


class RulesEval(BaseModel):
    context: str = Field(description="The context of the evaluation.")
    instructions: str = Field(description="Instructions for the evaluator.")
    always: list[str] = Field(description="A good output must always do the following")
    never: list[str] = Field(description="A good output must never do the following")


class HeadToHeadEval(BaseModel):
    """
    A prompt for the head-to-head evaluation of the outputs
    of two agents to determine which has the better output.

    Must return a single output:
    0 (first output is better)
    0.5 (outputs are tied for quality)
    1 (second output is better)
    """

    context: str = Field(description="The context of the evaluation.")
    instructions: str = Field(description="Instructions for the evaluator.")
    tips: list[str] = Field(description="A list of tips for the evaluator to consider.")


@dataclass
class SynEvalGenerator:
    prompt_model: str = "openai/o4-mini"
    sys_prompt: str = dedent(
        """\
        You are an expert AI engineer looking at source code for an agent.
        Your task is to generate the prompt for an LLM judge that will be used to
        evaluate a single final output of the agent.

        Rules must only specify knowledge that is available in the source code and
        context.
        """
    )

    def __post_init__(self):
        self.lm = instructor.from_litellm(litellm.acompletion)

    async def rules(
        self,
        fns: list["FunctionInfo"],
        examples: list[str] | None = None,
    ) -> RulesEval:
        messages = prepare_messages(self.sys_prompt, fns, examples)
        return await self.lm.create(
            model=self.prompt_model,
            response_model=RulesEval,
            messages=messages,
        )

    async def head_to_head(
        self,
        fns: list["FunctionInfo"],
        examples: list[str] | None = None,
    ) -> HeadToHeadEval:
        messages = prepare_messages(self.sys_prompt, fns, examples)
        return await self.lm.create(
            model=self.prompt_model,
            response_model=HeadToHeadEval,
            messages=messages,
        )


async def _cli():
    generator = SynEvalGenerator()
    rich.print("Loading function info...", end=" ")
    from aiai.app.models import FunctionInfo

    fns = [fn async for fn in FunctionInfo.objects.all()]
    rich.print(f"{len(fns)} functions loaded.")

    rich.print("Generating rules prompt...", end=" ")
    rules = await generator.rules(fns)
    rich.print("done.")
    rich.print("<rules>")
    rich.print_json(rules.model_dump_json())
    rich.print("</rules>")

    rich.print("Generating head-to-head prompt...", end=" ")
    head_to_head = await generator.head_to_head(fns)
    rich.print("done.")
    rich.print("<head-to-head>")
    rich.print_json(head_to_head.model_dump_json())
    rich.print("</head-to-head>")


def cli():
    load_dotenv()
    setup_django()
    asyncio.run(_cli())


if __name__ == "__main__":
    cli()
