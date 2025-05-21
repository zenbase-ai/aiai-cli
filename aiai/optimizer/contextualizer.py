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

    <always>
        Describe LLM-related code.
    </always>
    <never>
        Describe logic-related success/failure modes.
    </never>
    """

    synthetic_data: str = Field(
        description=(
            "A prompt to generate thoughtful, realistic synthetic inputs for the agent. "
            "Make sure it is generating just one data point."
        )
    )
    reward_reasoning: str = Field(
        description=dedent(
            """\
            A prompt to generate hypothetical reasoning for a given reward given the execution trace of the agent.
            The prompt will be used in the following context:

            <context>
            You are approximating a reward function for an agent based on their outputs.
            You are given the source code of the agent, an analysis of the agent,
            an execution trace, and the earned reward.

            Put yourself in the shoes of the agent and generate a hypothetical reasoning trace that
            leads to the reward.

            Consider the goal of the agent and what the user is trying to achieve with the agent.
            Ensure that the reasoning trace's logically leads to the specified reward.

            {reward_reasoning_prompt}
            </context>
            """
        )
    )
    traces_to_patterns: str = Field(
        description=dedent(
            """\
            A prompt to deeply analyze and identify patterns in the execution trace that led to the reward.
            Should include considerations that are relevant to the task at hand.
            The prompt will be used in the following context:

            <context>
            Analyze the following LLM trace to identify patterns that resulted in the agent
            receiving the reward. You will be given the agent source code, the trace, and the reward.

            Make sure the patterns you identify are specific and detailed. We will then be clustering
            these patterns to identify groups and then formulate rules to improve outcomes.

            {traces_to_patterns_prompt}
            </context>
            """
        )
    )
    patterns_to_insights: str = Field(
        description=dedent(
            """\
            A prompt to generate insights for the optimizer based on the analysis of the execution trace.
            These insights will inform the optimizer on how to suggest improvements to the prompts.
            The prompt will be used in the following context:

            <context>
            We've identified patterns in LLM traces that result in varying outcomes.
            Now, your job is to analyze and derive insights from these patterns to inform future runs.
            Focus on identifying insights that will help the agent earn greater rewards.

            {patterns_to_insights_prompt}
            </context>
            """
        )
    )
    insights_to_rules: str = Field(
        description=dedent(
            """\
            A prompt to generate rules and tips for the optimizer based on the insights from the execution trace.
            These rules and tips should be specific, detailed, simple, and actionable without any code changes.

            <context>
            You are an expert in analyzing model outputs and task performance. We have analyzed traces
            that have earned rewards. We have also derived insights from the patterns in these traces.

            Your job is to suggest changes to the prompts to improve the agent's performance. These changes
            are in the form of rules and tips for the LLM to follow. These rules and tips should be specific,
            detailed, simple, and actionable for the LLM without any code changes.

            For each rule and tip you generate, provide a reasoning that explains why this rule is important
            based on the insights and patterns observed in the trace data.

            {insights_to_rules_prompt}
            </context>
            """
        )
    )
    synthesize_rules: str = Field(
        description=dedent(
            """\
            A prompt to synthesize the rules and tips into a single, comprehensive set of rules.
            These rules and tips will be directly injected into the prompt, so they should be
            specific, detailed, simple, and actionable without any code changes.

            <context>
            We have analyzed a set of LLM traces that have earned rewards.
            We have also derived insights from the patterns in these traces,
            and now we have a set of rules and tips.

            Your job is to synthesize the suggestions into a single set of changes to the prompts to
            improve the agent's performance. Identify the most important changes and combine them into
            a single set of changes. Each group of changes should be specific, detailed, simple, and
            actionable for the LLM. Each group should have at most 5 items.

            For each rule and tip you include, provide a reasoning that explains why this rule is important
            based on the insights and patterns observed in the trace data.

            Rules must not be about code execution (e.g. environment variables, API keys, etc.)

            {synthesize_rules_prompt}
            </context>
            """
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
