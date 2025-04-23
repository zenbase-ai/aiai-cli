from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Literal, TypedDict

import instructor
import litellm
from pydantic import BaseModel, Field, computed_field

from aiai.optimizer.contextualizer import AgentContext

if TYPE_CHECKING:
    from aiai.app.models import SyntheticEval


class AbstractEval(BaseModel):
    instructions: str = Field(description="Instructions for the evaluator.")
    always: list[str] = Field(description="A good output must always do the following")
    never: list[str] = Field(description="A good output must never do the following")
    tips: list[str] = Field(description="A list of tips for the evaluator to consider.")
    background_context: str = Field(description="The context of the evaluation.")

    def __str__(self) -> str:
        tips = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(self.tips))
        always = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(self.always))
        never = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(self.never))
        return dedent(
            """\
            <context>
            {context}
            </context>
            <instructions>
            {instructions}
            </instructions>
            <tips>
            {tips}
            </tips>
            <always>
            {always}
            </always>
            <never>
            {never}
            </never>
            """
        ).format(
            context=self.background_context,
            instructions=self.instructions,
            tips=tips,
            always=always,
            never=never,
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
    agent_context: AgentContext
    model: str = "openai/o4-mini"

    def __post_init__(self):
        self.lm = instructor.from_litellm(litellm.completion)

    def rules(
        self,
        examples: list | None = None,
    ) -> RulesEval:
        return self.lm.create(
            model=self.model,
            response_model=RulesEval,
            max_retries=3,
            messages=[
                {
                    "role": "system",
                    "content": dedent(
                        f"""\
                        {self.agent_context.analysis.expert_persona}

                        Your job is to generate a prompt for an LLM judge.
                        Tips and rules must only specifiy knowledge that is available to the LLM.
                        """
                    ),
                },
                {
                    "role": "user",
                    "content": dedent(
                        f"""\
                        Here is the source code for the agent:

                        <agent>
                            <source_code>
                                {self.agent_context.source_code}
                            </source_code>
                            <analysis>
                                <what>{self.agent_context.analysis.what}</what>
                                <how>{self.agent_context.analysis.how}</how>
                            </analysis>
                        </agent>

                        And some examples of input data:
                        <examples>
                            {examples}
                        </examples>
                        """
                    ),
                },
            ],
        )

    def head_to_head(
        self,
        examples: list | None = None,
    ) -> HeadToHeadEval:
        return self.lm.create(
            model=self.model,
            response_model=HeadToHeadEval,
            max_retries=3,
            messages=[
                {
                    "role": "system",
                    "content": dedent(
                        f"""\
                        {self.agent_context.analysis.expert_persona}

                        Your job is to generate a prompt for an LLM judge.
                        Tips and rules must only specifiy knowledge that is available to the LLM.
                        """
                    ),
                },
                {
                    "role": "user",
                    "content": dedent(
                        f"""\
                        Here is the source code for the agent:

                        <agent>
                            <source_code>
                                {self.agent_context.source_code}
                            </source_code>
                            <analysis>
                                <what>{self.agent_context.analysis.what}</what>
                                <how>{self.agent_context.analysis.how}</how>
                            </analysis>
                        </agent>

                        And some examples of input data:
                        <examples>
                            {examples}
                        </examples>
                        """
                    ),
                },
            ],
        )

    def perform(self, examples: list | None = None):
        from aiai.app.models import SyntheticEval

        # Run rules and head_to_head evaluations in parallel
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures: list[Future[RulesEval | HeadToHeadEval]] = [
                pool.submit(self.rules, examples),
                pool.submit(self.head_to_head, examples),
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
    model: str = "openai/o4-mini"

    def __post_init__(self):
        self.lm = instructor.from_litellm(litellm.completion)

        if self.eval.kind == "rules":
            self.response_model = RulesEval.Result
        elif self.eval.kind == "head_to_head":
            self.response_model = HeadToHeadEval.Result
        else:
            raise ValueError(f"Unknown eval kind: {self.eval.kind}")

    def __call__(self, agent_output: Any) -> EvalResult:
        user_message = f"Here is the agent's output: <output>\n{agent_output}\n</output>"
        result: RulesEval.Result | HeadToHeadEval.Result = self.lm.create(
            model=self.model,
            response_model=self.response_model,
            max_retries=3,
            messages=[
                {"role": "system", "content": self.eval.prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return result.model_dump()
