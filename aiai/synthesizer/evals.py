from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from textwrap import dedent
from typing import TYPE_CHECKING

import instructor
import litellm
from pydantic import BaseModel, Field

from aiai.synthesizer.utils import get_examples, prepare_messages

if TYPE_CHECKING:
    from aiai.app.models import FunctionInfo, SyntheticEval


class AbstractEval(BaseModel):
    context: str = Field(description="The context of the evaluation.")
    instructions: str = Field(description="Instructions for the evaluator.")
    always: list[str] = Field(description="A good output must always do the following")
    never: list[str] = Field(description="A good output must never do the following")
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
            <always>
            {self.always}
            </always>
            <never>
            {self.never}
            </never>
            <tips>
            {self.tips}
            </tips>\
            """
        )


class RulesEval(AbstractEval):
    """
    A prompt for an LLM judge to evaluate the outputs of
    a single agent and pass/fail based on the rules.
    """

    def to_db_model(self) -> "SyntheticEval":
        from aiai.app.models import SyntheticEval

        return SyntheticEval(
            kind="rules",
            prompt=str(self),
            fields=self.model_dump(),
        )


class HeadToHeadEval(AbstractEval):
    """
    A prompt for the head-to-head evaluation of the outputs
    of two agents to determine which has the better output.

    Must return a single output:
    0 (first output is better)
    0.5 (outputs are tied for quality)
    1 (second output is better)
    """

    def to_db_model(self) -> "SyntheticEval":
        from aiai.app.models import SyntheticEval

        return SyntheticEval(
            kind="head_to_head",
            prompt=str(self),
            fields=self.model_dump(),
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
        self.lm = instructor.from_litellm(litellm.completion)

    def rules(
        self,
        fns: list["FunctionInfo"],
        examples: list[str] | None = None,
    ) -> RulesEval:
        messages = prepare_messages(self.sys_prompt, fns, examples)
        return self.lm.create(
            model=self.prompt_model,
            response_model=RulesEval,
            messages=messages,
        )

    def head_to_head(
        self,
        fns: list["FunctionInfo"],
        examples: list[str] | None = None,
    ) -> HeadToHeadEval:
        messages = prepare_messages(self.sys_prompt, fns, examples)
        return self.lm.create(
            model=self.prompt_model,
            response_model=HeadToHeadEval,
            messages=messages,
        )

    def perform(self):
        from aiai.app.models import FunctionInfo, SyntheticEval

        fns = list(FunctionInfo.objects.all())
        examples = get_examples(fns)

        # Run rules and head_to_head evaluations in parallel
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(self.rules, fns, examples),
                pool.submit(self.head_to_head, fns, examples),
            ]
            rules_eval, head_to_head_eval = SyntheticEval.objects.bulk_create(
                [f.result().to_db_model() for f in futures],
            )

        return rules_eval, head_to_head_eval
