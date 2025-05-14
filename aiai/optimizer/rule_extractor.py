import json
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from textwrap import dedent

import pydash
from docetl.api import ClusterOp, Dataset, MapOp, Pipeline, PipelineOutput, PipelineStep, ReduceOp, UnnestOp

from aiai.optimizer.contextualizer import AgentContext
from aiai.utils import setup_django

cwd = Path(__file__).parent


def build_pipeline(context: AgentContext, **kwargs) -> Pipeline:
    """
    Build a pipeline for extracting rules from traces.

    Args:
        reward: The reward type to analyze ("success", "failure", etc.)
        **kwargs: Additional arguments to pass to the Pipeline constructor

    Returns:
        Pipeline: A configured pipeline instance
    """
    operations = [
        MapOp(
            name="reward_reasoning",
            type="map",
            litellm_completion_kwargs={"temperature": 1},
            prompt=dedent(
                f"""\
                <instructions>
                    {context.analysis.expert_persona}

                    You are approximating a reward function for an agent based on their outputs.
                    You are given the source code of the agent, an analysis of the agent,
                    an execution trace, and the earned reward.

                    Put yourself in the shoes of the agent and generate a hypothetical reasoning trace that
                    leads to the reward.

                    Consider the goal of the agent and what the user is trying to achieve with the agent.
                    Ensure that the reasoning trace's logically leads to the specified reward.

                    {context.optimizer_prompts.reward_reasoning}
                </instructions>

                <agent>
                    <source_code>
                        {context.source_code}
                    </source_code>
                    <analysis>
                        {context.analysis.model_dump_json()}
                    </analysis>
                </agent>
                """
                + """\
                <trace id="{{input.trace_id}}">
                    {% for span in input.trace %}
                        <span id="{{span.span_id}}">
                            <prompt>{{span.prompt}}</prompt>
                            <completion>{{span.completion}}</completion>
                        </span>
                    {% endfor %}
                </trace>

                <reward>
                    <value>{{input.reward}}</value>
                </reward>

                <output>
                    reward_reasoning_iterations: Iterate on the reward reasoning until you are confident
                    that the reasoning is correct.
                    reward_reasoning: The final reward reasoning.
                </output>
                """
            ),
            output={
                "schema": {
                    "reward_reasoning_iterations": "list[string]",
                    "reward_reasoning": "string",
                }
            },
            optimize=False,
        ),
        MapOp(
            name="traces_to_patterns",
            type="map",
            prompt=dedent(
                f"""\
                <instructions>
                    {context.analysis.expert_persona}

                    Analyze the following LLM trace to identify patterns that resulted in the agent
                    receiving the reward. You will be given the agent source code, the trace, and the reward.

                    Make sure the patterns you identify are specific and detailed. We will then be clustering
                    these patterns to identify groups and then formulate rules to improve outcomes.

                    {context.optimizer_prompts.traces_to_patterns}
                </instructions>

                <agent>
                    <source_code>
                        {context.source_code}
                    </source_code>
                    <analysis>
                        <what>{context.analysis.what}</what>
                        <how>{context.analysis.how}</how>
                    </analysis>
                </agent>
                """
                + """\
                <trace id="{{input.trace_id}}">
                    {% for span in input.trace %}
                        <span id="{{span.span_id}}">
                            <prompt>{{span.prompt}}</prompt>
                            <completion>{{span.completion}}</completion>
                        </span>
                    {% endfor %}
                </trace>

                <reward>
                    <hypothetical_reasoning>{{input.reward_reasoning}}</hypothetical_reasoning>
                    <value>{{input.reward}}</value>
                </reward>
                """
            ),
            output={
                "schema": {
                    "patterns": "list[string]",
                }
            },
            optimize=True,
        ),
        ClusterOp(
            name="patterns_to_insights",
            type="cluster",
            embedding_keys=[
                "patterns",
            ],
            output_key="cluster_patterns",
            summary_prompt=dedent(
                f"""\
                <instructions>
                    {context.analysis.expert_persona}

                    We've identified patterns in LLM traces that result in varying outcomes.
                    Now, your job is to analyze and derive insights from these patterns to inform future runs.
                    Focus on identifying insights that will help the agent earn greater rewards.

                    {context.optimizer_prompts.patterns_to_insights}
                </instructions>

                <agent>
                    <source_code>
                        {context.source_code}
                    </source_code>
                    <analysis>
                        <what>{context.analysis.what}</what>
                        <how>{context.analysis.how}</how>
                    </analysis>
                </agent>
                """
                + """\
                <patterns>
                    {% for input in inputs %}
                        {% if input.patterns %}
                            {{input.patterns}}
                        {% endif %}
                    {% endfor %}
                </patterns>

                <output>
                    Insights MUST BE be a list of strings. Each insight should be specific and detailed.
                    If no insight is found, return an empty list.
                </output>
                """
            ),
            summary_schema={
                "analysis": "string",
                "insights": "list[string]",
            },
            optimize=True,
        ),
        UnnestOp(
            name="unnest_patterns_from_clusters",
            type="unnest",
            unnest_key="cluster_patterns",
        ),
        UnnestOp(
            name="unnest_insights_from_patterns",
            type="unnest",
            unnest_key="cluster_patterns",
            expand_fields=["insights"],
            output_key="insights",
        ),
        ReduceOp(
            name="insights_to_rules",
            type="reduce",
            reduce_key="insights",
            prompt=dedent(
                f"""\
                <instructions>
                    {context.analysis.expert_persona}

                    You are an expert in analyzing model outputs and task performance. We have analyzed traces
                    that have earned rewards. We have also derived insights from the patterns in these traces.

                    Your job is to suggest changes to the prompts to improve the agent's performance. These changes
                    are in the form of rules and tips for the LLM to follow. These rules and tips should be specific,
                    detailed, simple, and actionable for the LLM without any code changes.

                    For each rule and tip you generate, provide a reasoning that explains why this rule is important
                    based on the insights and patterns observed in the trace data.

                    {context.optimizer_prompts.insights_to_rules}
                </instructions>

                <agent>
                    <source_code>
                        {context.source_code}
                    </source_code>
                    <analysis>
                        <what>{context.analysis.what}</what>
                        <how>{context.analysis.how}</how>
                    </analysis>
                </agent>
                """
                + """\
                <insights>
                    {% for input in inputs %}
                        {% if input.insights %}
                            {{input.insights}}
                        {% endif %}
                    {% endfor %}
                </insights>

                <output>
                    Return:
                    1. Rules (in always/never format):
                    • Always: ONLY include rules that are absolutely clear-cut requirements
                      (format as direct actions: "Include complete information")
                    • Never: ONLY include rules that are absolutely clear-cut prohibitions
                      (format as direct actions, NOT as avoidance statements: "Return incorrect information"
                      NOT "Avoid returning incorrect information")

                    IMPORTANT: Format "never" rules as positive statements of what not to do,
                    NOT negative avoidance statements.

                    CORRECT FORMAT for "never" rules:
                    - "Return invalid results"
                    - "Use misleading information"
                    - "Ignore key requirements"

                    INCORRECT FORMAT for "never" rules (DO NOT USE THESE):
                    - "Avoid returning invalid results"
                    - "Do not use misleading information"
                    - "Don't ignore key requirements"

                    2. Tips (positive factors that contribute to success):
                    Format each tip as a clear, direct statement about what to look for or consider.
                    Include ANY rule that is not a strict ALWAYS or NEVER requirement here.

                    IMPORTANT: Only include rules in the "always" or "never" sections if they are
                    absolutely clear-cut, binary requirements. If a rule is not a strict ALWAYS or NEVER
                    requirement, or if it's more nuanced, place it in the "tips" section instead.

                    3. For each rule and tip, provide a reasoning that explains why it's important based
                    on the insights and patterns observed in the trace data.

                    Format your response as a JSON with the following structure:
                    - "always": a list of dictionaries, each with "rule" and "reasoning" fields
                    - "never": a list of dictionaries, each with "rule" and "reasoning" fields
                    - "tips": a list of dictionaries, each with "rule" and "reasoning" fields
                </output>
                """
            ),
            output={
                "schema": {
                    "always": "list[{rule: string, reasoning: string}]",
                    "never": "list[{rule: string, reasoning: string}]",
                    "tips": "list[{rule: string, reasoning: string}]",
                }
            },
            optimize=True,
        ),
        ReduceOp(
            name="synthesize_rules",
            type="reduce",
            reduce_key="_all",
            output={
                "schema": {
                    "always": "list[{rule: string, reasoning: string}]",
                    "never": "list[{rule: string, reasoning: string}]",
                    "tips": "list[{rule: string, reasoning: string}]",
                }
            },
            prompt=dedent(
                f"""\
                <instructions>
                    {context.analysis.expert_persona}

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

                    {context.optimizer_prompts.synthesize_rules}
                </instructions>

                <agent>
                    <source_code>
                        {context.source_code}
                    </source_code>
                    <analysis>
                        {context.analysis.model_dump_json()}
                    </analysis>
                </agent>
                """
                + """\
                <suggestions>
                    <always>
                        {% for input in inputs %}
                            {% if input.always %}
                                {{input.always}}
                            {% endif %}
                        {% endfor %}
                    </always>

                    <never>
                        {% for input in inputs %}
                            {% if input.never %}
                                {{input.never}}
                            {% endif %}
                        {% endfor %}
                    </never>

                    <tips>
                        {% for input in inputs %}
                            {% if input.tips %}
                                {{input.tips}}
                            {% endif %}
                        {% endfor %}
                    </tips>
                </suggestions>

                <output>
                    Return:
                    1. Rules (in always/never format):
                    • Always: ONLY include rules that are absolutely clear-cut requirements
                      (format as direct actions: "Provide complete information")
                    • Never: ONLY include rules that are absolutely clear-cut prohibitions
                      (format as direct actions, NOT as avoidance statements: "Return invalid results"
                      NOT "Avoid returning invalid results"). Presume that the "Never" is prepended to the rule.

                    IMPORTANT: Format "never" rules as positive statements of what not to do,
                    NOT negative avoidance statements.

                    CORRECT FORMAT for "never" rules:
                    - "Return invalid results"
                    - "Use misleading information"
                    - "Ignore key requirements"

                    INCORRECT FORMAT for "never" rules (DO NOT USE THESE):
                    - "Avoid returning invalid results"
                    - "Do not use misleading information"
                    - "Don't ignore key requirements"
                    - "must not ..."

                    2. Tips (positive factors that contribute to success):
                    Format each tip as a clear, direct statement about what to look for or consider.
                    Include ANY rule that is not a strict ALWAYS or NEVER requirement here.

                    IMPORTANT: Only include rules in the "always" or "never" sections if they are
                    absolutely clear-cut, binary requirements. If a rule is not a strict ALWAYS or NEVER
                    requirement, or if it's more nuanced, place it in the "tips" section instead.

                    3. For each rule and tip, provide a reasoning that explains why it's important based
                    on the insights and patterns observed in the trace data. Ensure the reasoning is 
                    specific, evidence-based, and explains the impact on the agent's performance.

                    Format your response as a JSON with the following structure:
                    - "always": a list of dictionaries, each with "rule" and "reasoning" fields
                    - "never": a list of dictionaries, each with "rule" and "reasoning" fields
                    - "tips": a list of dictionaries, each with "rule" and "reasoning" fields
                </output>
                """
            ),
        ),
    ]

    steps = [
        PipelineStep(
            name="inverse_rl",
            input="tasks",
            operations=[
                "reward_reasoning",
                "traces_to_patterns",
                "patterns_to_insights",
                "unnest_patterns_from_clusters",
                "unnest_insights_from_patterns",
                "insights_to_rules",
                "synthesize_rules",
            ],
        ),
    ]

    return Pipeline(
        name="rule-extractor-pipeline",
        operations=operations,
        steps=steps,
        **kwargs,
    )


def generate_rules_and_tips(context: AgentContext, model="openai/o4-mini") -> dict:
    """
    Extract rules from a collection of traces.

    Args:
        traces: A collection of log objects with input_data and output_data attributes
        reward: The reward type to analyze ("success", "failure", etc.)
        model: The model to use for the analysis

    Returns:
        dict: A dictionary containing always/never rules and tips, each as a list of dictionaries with 'rule' and
        'reasoning' fields
    """
    from aiai.app.models import EvalRun, OtelSpan

    evals = list(EvalRun.objects.all())
    if not evals:
        return {
            "always": [],
            "never": [],
            "tips": [],
        }

    trace_ids = [e.trace_id for e in evals]
    spans = defaultdict[str, list[OtelSpan]](list)
    for span in OtelSpan.objects.filter(trace_id__in=trace_ids).order_by("start_time").all():
        spans[span.trace_id].append(span)

    if not spans:
        return {
            "always": [],
            "never": [],
            "tips": [],
        }

    runs = []
    for run in evals:
        runs.append(
            {
                "trace_id": run.trace_id,
                "trace": [
                    {
                        "prompt": span.prompt,
                        "completion": span.completion,
                        "attributes": span.attributes,
                        "trace_id": span.trace_id,
                        "span_id": span.span_id,
                    }
                    for span in spans[run.trace_id]
                ],
                "reward": run.reward,
            }
        )

    # Filter and join traces into one string
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(runs, f)
        in_path = f.name

    # Reserve a temp file for the pipeline output
    out_fd, out_path = tempfile.mkstemp(suffix=".json")
    os.close(out_fd)

    try:
        datasets = {
            "tasks": Dataset(
                type="file",
                path=in_path,
            )
        }
        pipeline = build_pipeline(
            context=context,
            datasets=datasets,
            output=PipelineOutput(type="file", path=out_path),
            default_model=model,
        )
        pipeline.run()

        # Read back your always/never/tips
        with open(out_path) as f:
            results = json.load(f)

        return pydash.pick(results[0], "always", "never", "tips")

    finally:
        # Clean up temp files
        if os.path.exists(in_path):
            os.remove(in_path)
        if os.path.exists(out_path):
            os.remove(out_path)


if __name__ == "__main__":
    setup_django()
    from aiai.app.models import OtelSpan

    traces = list(OtelSpan.objects.all())
    rules = generate_rules_and_tips(traces)
    print(rules)
