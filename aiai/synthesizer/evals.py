from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from textwrap import dedent
from typing import TYPE_CHECKING, Literal, TypedDict

import instructor
import litellm
from pydantic import BaseModel, Field, computed_field

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

    class Result(BaseModel):
        reasoning: str
        result: Literal["pass", "fail"]

        @computed_field
        def reward(self) -> float:
            return 1 if self.result == "pass" else 0

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

    class Result(BaseModel):
        reasoning: str
        result: Literal["0", "0.5", "1"]

        @computed_field
        def reward(self) -> float:
            return float(self.result)

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


class EvalResult(TypedDict, total=False):
    reward: float


@dataclass
class SyntheticEvalRunner:
    eval: "SyntheticEval"
    prompt_model: str = "openai/o4-mini"

    def __post_init__(self):
        self.lm = instructor.from_litellm(litellm.acompletion)

        if self.eval.kind == "rules":
            self.result_model = RulesEval.Result
        elif self.eval.kind == "head_to_head":
            self.result_model = HeadToHeadEval.Result
        else:
            raise ValueError(f"Unknown eval kind: {self.eval.kind}")

    def __call__(self, agent_output: str) -> EvalResult:
        user_message = f"Here is the agent's output: <output>\n{agent_output}\n</output>"
        result: RulesEval.Result | HeadToHeadEval.Result = self.lm.create(
            model=self.prompt_model,
            messages=[
                {"role": "system", "content": self.eval.prompt},
                {"role": "user", "content": user_message},
            ],
            response_model=self.result_model,
        )
        return result.model_dump()
