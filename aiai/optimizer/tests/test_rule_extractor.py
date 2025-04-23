from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from pytz import UTC

from aiai.app.models import EvalRun, OtelSpan
from aiai.optimizer.rule_extractor import build_rules_pipeline, generate_rules


def test_build_rules_pipeline():
    # Mock the necessary parameters
    import tempfile

    from docetl.api import Dataset, PipelineOutput

    # Create a temp file for output
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp_file:
        # Create test datasets and output
        datasets = {"tasks": Dataset(type="file", path=tmp_file.name)}
        output = PipelineOutput(type="file", path=tmp_file.name)

        # Test that the pipeline is built correctly with all required kwargs
        pipeline = build_rules_pipeline(datasets=datasets, output=output, default_model="openai/gpt-4.1-nano")

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


@pytest.mark.django_db
def xtest_integration_with_db():
    # Create some test spans
    OtelSpan.objects.bulk_create(
        [
            OtelSpan(
                agent_run_id="test_rule_extractor",
                trace_id="test_trace_id",
                span_id="test_span_id_1",
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC),
                attributes={"test": "test"},
                prompt="Test prompt 1",
                completion="Test response 1",
            ),
            OtelSpan(
                agent_run_id="test_rule_extractor",
                trace_id="test_trace_id",
                span_id="test_span_id_2",
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC),
                attributes={"test": "test"},
                prompt="Test prompt 2",
                completion="Test response 2",
            ),
        ]
    )
    EvalRun.objects.bulk_create(
        [
            EvalRun(agent_run_id="test_rule_extractor", reward="good"),
            EvalRun(agent_run_id="test_rule_extractor", reward="bad"),
        ]
    )

    with (
        patch("aiai.optimizer.rule_extractor.Pipeline") as MockPipeline,
        patch("tempfile.NamedTemporaryFile") as mock_tempfile,
        patch("tempfile.mkstemp") as mock_mkstemp,
        patch("json.dump") as _,
        patch("builtins.open", create=True) as mock_open,
        patch("json.load") as mock_json_load,
        patch("os.remove") as _,
    ):
        # Setup mock temporary files
        mock_tempfile.return_value.__enter__.return_value.name = "/tmp/mock_input.json"
        mock_mkstemp.return_value = (5, "/tmp/mock_output.json")

        # Mock file open and json load
        mock_open.return_value.__enter__.return_value = MagicMock()

        # Mock the JSON data that would be read from the output file
        mock_json_load.return_value = {
            "always": ["Test always rule"],
            "never": ["Test never rule"],
            "tips": ["Test tip"],
        }

        # Setup mock pipeline
        mock_pipeline_instance = MockPipeline.return_value
        mock_pipeline_instance.run.return_value = None

        # Call extract_rules with the database logs
        result = generate_rules(model="openai/gpt-4.1-nano")

        # Verify the result
        assert isinstance(result, dict)
        assert "always" in result
        assert "never" in result
        assert "tips" in result

        # Verify Pipeline was called correctly
        args, kwargs = MockPipeline.call_args

        # Check expected parameters
        assert "datasets" in kwargs
        assert "output" in kwargs
        assert "name" in kwargs
        assert "operations" in kwargs
        assert "steps" in kwargs

        # Verify the run method was called on the instance
        mock_pipeline_instance.run.assert_called_once()
