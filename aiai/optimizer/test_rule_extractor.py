import json
import pytest
from unittest.mock import patch, MagicMock

from aiai.app.models import OtelSpan
from aiai.optimizer.rule_extractor import build_rules_pipeline, extract_rules


@pytest.fixture
def mock_logs():
    log1 = MagicMock()
    log1.input_data = {"prompt": "Test prompt 1"}
    log1.output_data = {"response": "Test response 1"}

    log2 = MagicMock()
    log2.input_data = {"prompt": "Test prompt 2"}
    log2.output_data = {"response": "Test response 2"}

    return [log1, log2]


@pytest.mark.django_db
def test_extract_rules(mock_logs):
    with patch("aiai.optimizer.rule_extractor.Pipeline") as MockPipeline, patch(
        "tempfile.NamedTemporaryFile"
    ) as mock_tempfile, patch("tempfile.mkstemp") as mock_mkstemp, patch(
        "json.dump"
    ) as mock_json_dump, patch("builtins.open", create=True) as mock_open, patch(
        "json.load"
    ) as mock_json_load, patch("os.remove") as mock_remove:
        # Setup mock temporary files
        mock_tempfile.return_value.__enter__.return_value.name = "/tmp/mock_input.json"
        mock_mkstemp.return_value = (5, "/tmp/mock_output.json")

        # Mock file open and json load
        mock_open.return_value.__enter__.return_value = MagicMock()

        # Mock the JSON data that would be read from the output file
        mock_json_load.return_value = {
            "always": ["Always provide complete information"],
            "never": ["Return invalid results"],
            "tips": ["Balance completeness with conciseness"],
            "evaluation_guide": "Sample evaluation guide",
        }

        # Setup mock pipeline
        mock_pipeline_instance = MockPipeline.return_value
        mock_pipeline_instance.run.return_value = None

        # Call the function under test
        result = extract_rules(mock_logs, reward="success")

        # Assertions
        assert "always" in result
        assert "never" in result
        assert "tips" in result
        assert "evaluation_guide" in result

        # Verify Pipeline was called with correct arguments
        MockPipeline.assert_called_once()
        args, kwargs = MockPipeline.call_args

        # The reward parameter is passed to build_rules_pipeline, not directly to Pipeline
        # So we should check for the other expected parameters
        assert "datasets" in kwargs
        assert "output" in kwargs
        assert "name" in kwargs
        assert "operations" in kwargs
        assert "steps" in kwargs

        # Verify pipeline.run was called
        assert mock_pipeline_instance.run.called


def test_build_rules_pipeline():
    # Mock the necessary parameters
    from docetl.api import Dataset, PipelineOutput
    import tempfile

    # Create a temp file for output
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp_file:
        # Create test datasets and output
        datasets = {"tasks": Dataset(type="file", path=tmp_file.name)}
        output = PipelineOutput(type="file", path=tmp_file.name)

        # Test that the pipeline is built correctly with all required kwargs
        pipeline = build_rules_pipeline(
            reward="success", datasets=datasets, output=output, default_model="gpt-4o"
        )

        # Basic assertions about the pipeline structure
        assert pipeline.name == "rule-extractor-pipeline"
        assert len(pipeline.operations) > 0
        assert len(pipeline.steps) > 0

        # Check for specific operations that should be present
        operation_names = [op.name for op in pipeline.operations]
        assert "reward_reasoning" in operation_names
        assert "logs_to_patterns" in operation_names
        assert "insights_to_rules" in operation_names
        assert "synthesize_rules" in operation_names

        # Verify the kwargs were properly set
        assert pipeline.datasets == datasets
        assert pipeline.output == output
        assert pipeline.default_model == "gpt-4o"


@pytest.mark.django_db
def test_integration_with_db():
    # Create some test spans
    span1 = OtelSpan.objects.create(
        input_data={"prompt": "Test prompt 1"},
        output_data={"response": "Test response 1"},
    )
    span2 = OtelSpan.objects.create(
        input_data={"prompt": "Test prompt 2"},
        output_data={"response": "Test response 2"},
    )

    # Get all spans
    logs = OtelSpan.objects.all()

    with patch("aiai.optimizer.rule_extractor.Pipeline") as MockPipeline, patch(
        "tempfile.NamedTemporaryFile"
    ) as mock_tempfile, patch("tempfile.mkstemp") as mock_mkstemp, patch(
        "json.dump"
    ) as mock_json_dump, patch("builtins.open", create=True) as mock_open, patch(
        "json.load"
    ) as mock_json_load, patch("os.remove") as mock_remove:
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
            "evaluation_guide": "Test guide",
        }

        # Setup mock pipeline
        mock_pipeline_instance = MockPipeline.return_value
        mock_pipeline_instance.run.return_value = None

        # Call extract_rules with the database logs
        result = extract_rules(logs)

        # Verify the result
        assert isinstance(result, dict)
        assert "always" in result
        assert "never" in result
        assert "tips" in result
        assert "evaluation_guide" in result

        # Verify Pipeline was called correctly
        MockPipeline.assert_called_once()
        args, kwargs = MockPipeline.call_args

        # Check expected parameters
        assert "datasets" in kwargs
        assert "output" in kwargs
        assert "name" in kwargs
        assert "operations" in kwargs
        assert "steps" in kwargs
