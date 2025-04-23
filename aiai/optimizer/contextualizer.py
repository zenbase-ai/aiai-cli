from textwrap import dedent
from typing import NamedTuple

import instructor
import litellm
from pydantic import BaseModel, Field


class AgentAnalysis(BaseModel):
    """
    Only describe specifically what is LLM related. Do not describe code-related success/failure modes.
    """

    what: str = Field(description="Detailed, technical description of what the agent does")
    how: str = Field(description="Detailed, technical description of how the agent does it")
    success_modes: list[str] = Field(description="What does success look like for the agent?")
    failure_modes: list[str] = Field(description="What does failure look like for the agent?")
    expert_persona: str = Field(
        description=(
            "What personas have expertise in doing what the agent does? "
            "Return a response in the form of 'You are an expert in ...'"
        )
    )
    considerations: list[str] = Field(
        description="What would the expert consider when evaluating the quality of the agent's output?"
    )


class OptimizerPrompts(BaseModel):
    """
    Generate detailed, thoughtful, grounded, specific prompts to use for the optimizer.
    Only describe specifically what is LLM related.
    Do not describe code-related success/failure modes.
    """

    synthetic_data: str = Field(description="A prompt to generate realistic synthetic data.")
    reward_reasoning: str = Field(
        description=(
            "A prompt to generate hypothetical reasoning for a given reward given the execution trace of the agent."
        )
    )
    traces_to_patterns: str = Field(
        description=(
            "A prompt to deeply analyze identify patterns in the execution trace that led to the reward."
            "Should include considerations that are relevant to the task at hand, "
            "e.g. for email it should consider language patterns, structure, call-to-action, subject line, etc."
        )
    )
    patterns_to_insights: str = Field(
        description=(
            "A prompt to generate insights for the optimizer based on the analysis of the execution trace."
            "These insights will inform the optimizer on how to suggest improvements to the prompts."
        )
    )
    insights_to_rules: str = Field(
        description=(
            "A prompt to generate rules and tips for the optimizer based on the insights from the execution trace."
            "These rules and tips should be specific, detailed, simple, and actionable without any code changes."
        )
    )
    synthesize_rules: str = Field(
        description=(
            "A prompt to synthesize the rules and tips into a single, comprehensive set of rules."
            "These rules and tips will be directly injected into the prompt, so they should be "
            "specific, detailed, simple, and actionable without any code changes."
        )
    )
    rule_merger: str = Field(
        description=(
            "A prompt to merge two sets of (rules and tips) into a single semantically comprehensive set "
            "of the most important tips and rules to be injected directly into the prompts of the agent. "
            "The rules and tips should be specific, detailed, simple, and actionable for the LLM without "
            "any code changes."
        )
    )


class AgentContext(NamedTuple):
    source_code: str
    analysis: AgentAnalysis
    optimizer_prompts: OptimizerPrompts


def generate_context(source_code: str, model: str = "openai/o4-mini") -> AgentContext:
    lm = instructor.from_litellm(litellm.completion)
    analysis = lm.create(
        model=model,
        response_model=AgentAnalysis,
        max_retries=3,
        messages=[
            {
                "role": "system",
                "content": dedent(
                    """\
                    You are an expert AI engineer. You are given the source code of an agent and your job
                    is to analyze it and provide a detailed, technical description of what the agent does,
                    how it does it, what success looks like for the agent, and what failure looks like for
                    the agent. This output will be used to optimize the agent.
                    """
                ),
            },
            {
                "role": "user",
                "content": f"Here is the source code: <source_code>{source_code}</source_code>",
            },
        ],
    )
    prompts = lm.create(
        model=model,
        response_model=OptimizerPrompts,
        max_retries=3,
        messages=[
            {
                "role": "system",
                "content": dedent(
                    """\
                    You are an expert AI engineer. You are given the source code of an agent and an analysis of
                    the agent's behavior. Your job is to generate a set of prompts that will be used to optimize
                    the agent.
                    """
                ),
            },
            {
                "role": "user",
                "content": dedent(
                    f"""\
                    Here is the source code of the agent:
                    <source_code>
                        {source_code}
                    </source_code>

                    Here is the agent analysis:
                    <agent_analysis>
                        {analysis.model_dump_json()}
                    </agent_analysis>
                    """
                ),
            },
        ],
    )
    return AgentContext(source_code, analysis, prompts)
