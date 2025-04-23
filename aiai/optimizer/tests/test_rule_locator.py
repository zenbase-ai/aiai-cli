import tempfile
from unittest.mock import MagicMock, patch

import pytest
from docetl.api import Dataset, PipelineOutput

from aiai.optimizer.rule_locator import RuleLocator


@pytest.fixture
def mock_functions():
    function1 = MagicMock()
    function1.name = "test_function1"
    function1.file_path = "test/path1.py"
    function1.line_start = 1
    function1.line_end = 10
    function1.signature = "def test_function1():"
    function1.source_code = "def test_function1():\n    prompt = 'Test prompt'\n    return prompt"
    function1.docstring = "Test docstring"

    function2 = MagicMock()
    function2.name = "test_function2"
    function2.file_path = "test/path2.py"
    function2.line_start = 1
    function2.line_end = 15
    function2.signature = "def test_function2():"
    function2.source_code = "def test_function2():\n    return 'No prompt here'"
    function2.docstring = "Another test docstring"

    return [function1, function2]


@pytest.fixture
def mock_prompt_functions():
    return [
        {
            "name": "test_function1",
            "file_path": "test/path1.py",
            "signature": "def test_function1():",
            "source_code": "def test_function1():\n    prompt = 'Test prompt'\n    return prompt",
            "docstring": "Test docstring",
            "contains_prompt": True,
            "prompt_type": "instruction_prompt",
            "prompt_segments": ["Test prompt"],
            "confidence": 90,
        }
    ]


@pytest.fixture
def mock_rules():
    return {
        "always": ["Always do this"],
        "never": ["Never do that"],
        "tips": ["Consider this"],
    }


def test_build_prompt_finder_pipeline():
    # Create a temp file for input/output
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp_file:
        # Create test datasets and output
        datasets = {"functions": Dataset(type="file", path=tmp_file.name)}
        output = PipelineOutput(type="file", path=tmp_file.name)

        # Test that the pipeline is built correctly with required parameters
        locator = RuleLocator(rules=[])
        pipeline = locator._build_prompt_finder_pipeline(
            datasets=datasets, output=output, default_model="openai/gpt-4.1-nano"
        )

        # Basic assertions about the pipeline structure
        assert pipeline.name == "prompt-finder-pipeline"
        assert len(pipeline.operations) > 0
        assert len(pipeline.steps) > 0

        # Check for specific operations that should be present
        operation_names = [op.name for op in pipeline.operations]
        assert "identify_prompt_functions" in operation_names


@pytest.mark.django_db
def test_find_prompt_functions(mock_functions):
    with (
        patch("aiai.optimizer.rule_locator.RuleLocator._build_prompt_finder_pipeline") as mock_build_pipeline,
        patch("aiai.optimizer.rule_locator.tempfile.NamedTemporaryFile") as mock_tempfile,
        patch("aiai.optimizer.rule_locator.tempfile.mkstemp") as mock_mkstemp,
        patch("aiai.optimizer.rule_locator.json.dump") as _,
        patch("aiai.optimizer.rule_locator.open", create=True) as mock_open,
        patch("aiai.optimizer.rule_locator.json.load") as mock_json_load,
        patch("aiai.optimizer.rule_locator.os.remove") as _,
        patch("aiai.optimizer.rule_locator.os.close") as _,
        patch("aiai.optimizer.rule_locator.os.path.exists") as mock_exists,
    ):
        # Setup mock temporary files
        mock_tempfile.return_value.__enter__.return_value.name = "/tmp/mock_input.json"
        mock_mkstemp.return_value = (5, "/tmp/mock_output.json")
        mock_exists.return_value = True

        # Mock file open and json load
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Mock the JSON data that would be read from the output file
        mock_json_load.return_value = [
            {
                "name": "test_function1",
                "file_path": "test/path1.py",
                "contains_prompt": True,
                "prompt_type": "instruction_prompt",
                "prompt_segments": ["Test prompt"],
                "confidence": 90,
            },
            {
                "name": "test_function2",
                "file_path": "test/path2.py",
                "contains_prompt": False,
                "confidence": 20,
            },
        ]

        # Setup mock pipeline
        mock_pipeline = MagicMock()
        mock_build_pipeline.return_value = mock_pipeline

        # Call the function under test
        locator = RuleLocator(rules={})
        result = locator._find_prompt_functions(mock_functions)

        # Assertions
        assert len(result) == 1
        assert result[0]["name"] == "test_function1"
        assert result[0]["contains_prompt"] is True
        assert result[0]["confidence"] == 90

        # Verify Pipeline was called
        mock_build_pipeline.assert_called_once()
        mock_pipeline.run.assert_called_once()
