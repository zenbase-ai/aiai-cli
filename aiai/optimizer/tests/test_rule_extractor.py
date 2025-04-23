import pytest

from aiai.optimizer.contextualizer import AgentAnalysis, AgentContext, OptimizerPrompts
from aiai.optimizer.rule_extractor import build_pipeline


@pytest.fixture(scope="module")
def agent_context() -> AgentContext:
    # Create a mock AgentContext with necessary attributes
    return AgentContext(
        source_code="print('Hello, world!')",
        analysis=AgentAnalysis(
            expert_persona="You are a sales expert.",
            what="Generate professional sales emails",
            how="Use persuasive language and clear call to actions",
            success_modes=["mock success_modes"],
            failure_modes=["mock failure_modes"],
            considerations=["mock considerations"],
        ),
        optimizer_prompts=OptimizerPrompts(
            synthetic_data="mock synthetic_data",
            reward_reasoning="mock reward_reasoning",
            traces_to_patterns="mock traces_to_patterns",
            patterns_to_insights="mock patterns_to_insights",
            insights_to_rules="mock insights_to_rules",
            synthesize_rules="mock synthesize_rules",
            rule_merger="mock rule_merger",
        ),
    )


def test_build_rules_pipeline(agent_context: AgentContext):
    # Mock the necessary parameters
    import tempfile

    from docetl.api import Dataset, PipelineOutput

    # Create a temp file for output
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp_file:
        # Create test datasets and output
        datasets = {"tasks": Dataset(type="file", path=tmp_file.name)}
        output = PipelineOutput(type="file", path=tmp_file.name)

        # Test that the pipeline is built correctly with all required kwargs
        pipeline = build_pipeline(
            context=agent_context,
            datasets=datasets,
            output=output,
            default_model="openai/gpt-4.1-nano",
        )

        # Basic assertions about the pipeline structure
        assert pipeline.name == "rule-extractor-pipeline"
        assert len(pipeline.operations) > 0
        assert len(pipeline.steps) > 0

        # Check for specific operations that should be present
        operation_names = [op.name for op in pipeline.operations]
        assert "reward_reasoning" in operation_names
        assert "traces_to_patterns" in operation_names
        assert "insights_to_rules" in operation_names
        assert "synthesize_rules" in operation_names

        # Verify the kwargs were properly set
        assert pipeline.datasets == datasets
        assert pipeline.output == output
        assert pipeline.default_model == "openai/gpt-4.1-nano"
