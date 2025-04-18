import tempfile
from unittest.mock import MagicMock, patch

import pytest
from docetl.api import Dataset, PipelineOutput

from aiai.app.models import FunctionInfo
from aiai.rule_locator.rule_locator import (
    build_prompt_finder_pipeline,
    build_rule_locator_pipeline,
    find_prompt_functions,
    locate_rules,
    save_rule_placements,
)


@pytest.fixture
def mock_functions():
    function1 = MagicMock()
    function1.name = "test_function1"
    function1.file_path = "test/path1.py"
    function1.line_start = 1
    function1.line_end = 10
    function1.signature = "def test_function1():"
    function1.source_code = (
        "def test_function1():\n    prompt = 'Test prompt'\n    return prompt"
    )
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
            "line_start": 1,
            "line_end": 10,
            "signature": "def test_function1():",
            "source_code": "def test_function1():\n    prompt = 'Test prompt'\n    return prompt",
            "docstring": "Test docstring",
            "contains_prompt": True,
            "prompt_type": "instruction_prompt",
            "prompt_lines": "2-2",
            "prompt_segments": ["Test prompt"],
            "confidence": 90,
        }
    ]


@pytest.fixture
def mock_rules():
    return [
        {
            "always": ["Always do this"],
            "never": ["Never do that"],
            "tips": ["Consider this"],
        }
    ]


def test_build_prompt_finder_pipeline():
    # Create a temp file for input/output
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp_file:
        # Create test datasets and output
        datasets = {"functions": Dataset(type="file", path=tmp_file.name)}
        output = PipelineOutput(type="file", path=tmp_file.name)

        # Test that the pipeline is built correctly with required parameters
        pipeline = build_prompt_finder_pipeline(
            datasets=datasets, output=output, default_model="gpt-4o"
        )

        # Basic assertions about the pipeline structure
        assert pipeline.name == "prompt-finder-pipeline"
        assert len(pipeline.operations) > 0
        assert len(pipeline.steps) > 0

        # Check for specific operations that should be present
        operation_names = [op.name for op in pipeline.operations]
        assert "identify_prompt_functions" in operation_names


def test_build_rule_locator_pipeline():
    # Create a temp file for input/output
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp_file:
        # Create test datasets and output
        datasets = {
            "rules_with_prompt_functions": Dataset(type="file", path=tmp_file.name)
        }
        output = PipelineOutput(type="file", path=tmp_file.name)

        # Test that the pipeline is built correctly with required parameters
        pipeline = build_rule_locator_pipeline(
            datasets=datasets, output=output, default_model="gpt-4o"
        )

        # Basic assertions about the pipeline structure
        assert pipeline.name == "rule-locator-pipeline"
        assert len(pipeline.operations) > 0
        assert len(pipeline.steps) > 0

        # Check for specific operations that should be present
        operation_names = [op.name for op in pipeline.operations]
        assert "locate_rule_placement" in operation_names


@pytest.mark.django_db
def test_find_prompt_functions(mock_functions):
    with patch(
        "aiai.rule_locator.rule_locator.build_prompt_finder_pipeline"
    ) as mock_build_pipeline, patch(
        "aiai.rule_locator.rule_locator.tempfile.NamedTemporaryFile"
    ) as mock_tempfile, patch(
        "aiai.rule_locator.rule_locator.tempfile.mkstemp"
    ) as mock_mkstemp, patch(
        "aiai.rule_locator.rule_locator.json.dump"
    ) as mock_json_dump, patch(
        "aiai.rule_locator.rule_locator.open", create=True
    ) as mock_open, patch(
        "aiai.rule_locator.rule_locator.json.load"
    ) as mock_json_load, patch(
        "aiai.rule_locator.rule_locator.os.remove"
    ) as mock_remove, patch(
        "aiai.rule_locator.rule_locator.os.close"
    ) as mock_close, patch(
        "aiai.rule_locator.rule_locator.os.path.exists"
    ) as mock_exists:
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
                "prompt_lines": "2-2",
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
        result = find_prompt_functions(mock_functions, model="gpt-4o")

        # Assertions
        assert len(result) == 1
        assert result[0]["name"] == "test_function1"
        assert result[0]["contains_prompt"] is True
        assert result[0]["confidence"] == 90

        # Verify Pipeline was called
        mock_build_pipeline.assert_called_once()
        mock_pipeline.run.assert_called_once()


@pytest.mark.django_db
def test_locate_rules(mock_prompt_functions, mock_rules):
    with patch(
        "aiai.rule_locator.rule_locator.build_rule_locator_pipeline"
    ) as mock_build_pipeline, patch(
        "aiai.rule_locator.rule_locator.tempfile.NamedTemporaryFile"
    ) as mock_tempfile, patch(
        "aiai.rule_locator.rule_locator.tempfile.mkstemp"
    ) as mock_mkstemp, patch(
        "aiai.rule_locator.rule_locator.json.dump"
    ) as mock_json_dump, patch(
        "aiai.rule_locator.rule_locator.open", create=True
    ) as mock_open, patch(
        "aiai.rule_locator.rule_locator.json.load"
    ) as mock_json_load, patch(
        "aiai.rule_locator.rule_locator.os.remove"
    ) as mock_remove, patch(
        "aiai.rule_locator.rule_locator.os.close"
    ) as mock_close, patch(
        "aiai.rule_locator.rule_locator.os.path.exists"
    ) as mock_exists:
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
                "rule_type": "always",
                "rule_text": "Always do this",
                "placements": [
                    {
                        "function_id": 1,
                        "function_name": "test_function1",
                        "file_path": "test/path1.py",
                        "target_code_section": "prompt = 'Test prompt'",
                        "confidence": 85,
                        "reasoning": "This rule fits here because...",
                    }
                ],
            }
        ]

        # Setup mock pipeline
        mock_pipeline = MagicMock()
        mock_build_pipeline.return_value = mock_pipeline

        # Call the function under test
        result = locate_rules(mock_rules, mock_prompt_functions, model="gpt-4o")

        # Assertions
        assert len(result) == 1
        assert result[0]["function_name"] == "test_function1"
        assert result[0]["confidence"] == 85
        assert result[0]["rule_type"] == "always"
        assert result[0]["rule_text"] == "Always do this"

        # Verify Pipeline was called
        mock_build_pipeline.assert_called_once()
        mock_pipeline.run.assert_called_once()


@pytest.mark.django_db
def test_save_rule_placements():
    with patch(
        "aiai.app.models.DiscoveredRule.objects.get_or_create"
    ) as mock_get_or_create:
        # Setup the mock
        mock_get_or_create.return_value = (MagicMock(), True)

        # Create test placements
        placements = [
            {
                "rule_type": "always",
                "rule_text": "Always do this",
                "function_name": "test_function1",
                "file_path": "test/path1.py",
                "target_code_section": "prompt = 'Test prompt'",
                "confidence": 85,
                "reasoning": "This rule fits here because...",
            },
            {
                "rule_type": "never",
                "rule_text": "Never do that",
                "function_name": "test_function2",
                "file_path": "test/path2.py",
                "target_code_section": "another code section",
                "confidence": 60,  # Below threshold, should be ignored
                "reasoning": "Another reasoning",
            },
        ]

        # Call the function under test
        save_rule_placements(placements)

        # Verify get_or_create was called once (for the first placement with confidence >= 70)
        mock_get_or_create.assert_called_once()

        # Verify the arguments to get_or_create
        args, kwargs = mock_get_or_create.call_args
        assert kwargs["rule_text"] == "always: Always do this"
        assert kwargs["defaults"]["confidence"] == 85


@pytest.mark.django_db
def test_integration_with_db():
    # Create some test functions
    function1 = FunctionInfo.objects.create(
        name="test_function1",
        file_path="test/path1.py",
        line_start=1,
        line_end=10,
        signature="def test_function1():",
        source_code="def test_function1():\n    prompt = 'Test prompt'\n    return prompt",
        docstring="Test docstring",
    )

    # Define our test rules
    test_rules = [
        {
            "always": ["Always do this"],
            "never": ["Never do that"],
            "tips": ["Consider this"],
        }
    ]

    # Use this to properly mock the main function
    from aiai.rule_locator.rule_locator import main

    with patch(
        "aiai.rule_locator.rule_locator.find_prompt_functions"
    ) as mock_find_prompt, patch(
        "aiai.rule_locator.rule_locator.locate_rules"
    ) as mock_locate_rules, patch(
        "aiai.rule_locator.rule_locator.setup_django"
    ) as mock_setup_django, patch(
        "aiai.optimizer.rule_extractor.extract_rules"
    ) as mock_extract_rules:
        # Setup mock return values
        prompt_functions = [
            {
                "name": "test_function1",
                "file_path": "test/path1.py",
                "contains_prompt": True,
                "prompt_type": "instruction_prompt",
                "prompt_lines": "2-2",
                "prompt_segments": ["Test prompt"],
                "confidence": 90,
            }
        ]
        mock_find_prompt.return_value = prompt_functions

        # This will be returned by extract_rules in the main function
        mock_extract_rules.return_value = test_rules

        rule_placements = [
            {
                "rule_type": "always",
                "rule_text": "Always do this",
                "function_name": "test_function1",
                "file_path": "test/path1.py",
                "target_code_section": "prompt = 'Test prompt'",
                "confidence": 85,
                "reasoning": "This rule fits here because...",
            }
        ]
        mock_locate_rules.return_value = rule_placements

        # Call main function directly
        placements = main()

        # Verify the correct sequence of function calls
        mock_find_prompt.assert_called_once()
        mock_locate_rules.assert_called_once_with(test_rules, prompt_functions)

        # Verify the final result
        assert placements == rule_placements
