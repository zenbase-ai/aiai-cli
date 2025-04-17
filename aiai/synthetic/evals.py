from dataclasses import dataclass
from textwrap import dedent
from typing import TYPE_CHECKING

import instructor
import litellm
import rich
from pydantic import BaseModel, Field

from aiai.synthetic.utils import get_examples, prepare_messages

if TYPE_CHECKING:
    from aiai.app.models import FunctionInfo


class RulesEval(BaseModel):
    context: str = Field(description="The context of the evaluation.")
    instructions: str = Field(description="Instructions for the evaluator.")
    always: list[str] = Field(description="A good output must always do the following")
    never: list[str] = Field(description="A good output must never do the following")

    def __str__(self) -> str:
        return dedent(
            f"""\
            <context>
            {self.context}
            </context>
            <instructions>
            {self.instructions}
            </instructions>
            <always>
            {self.always}
            </always>
            <never>
            {self.never}
            </never>\
            """
        )


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

    def __str__(self) -> str:
        return dedent(
            f"""\
            <context>
            {self.context}
            </context>
            <instructions>
            {self.instructions}
            </instructions>
            <tips>
            {self.tips}
            </tips>\
            """
        )


@dataclass
class EvalGenerator:
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


async def cli():
    generator = EvalGenerator()
    rich.print("Loading function info...", end=" ")
    from aiai.app.models import FunctionInfo

    fns = [fn async for fn in FunctionInfo.objects.all()]
    rich.print(f"{len(fns)} functions loaded.")

    if examples := get_examples(fns):
        rich.print("Found examples:")
        rich.print_json(data=examples)

    rich.print("Generating rules prompt...", end=" ")
    rules = await generator.rules(fns, examples)
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

    return rules, head_to_head
