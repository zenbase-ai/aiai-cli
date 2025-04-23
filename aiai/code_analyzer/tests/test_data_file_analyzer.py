#!/usr/bin/env python
"""
Test script for the DataFileAnalyzer class.
This is an integration test that uses actual LLM calls through docetl.
"""

import json
import os
import shutil
import tempfile

import pytest
import yaml


@pytest.fixture
def test_directory():
    """
    Create a temporary directory with sample data files for testing.
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    try:
        # Create sample JSON file (prompt template)
        prompt_data = {
            "system": "You are a helpful assistant.",
            "user_prefix": "User: ",
            "assistant_prefix": "Assistant: ",
        }
        with open(os.path.join(temp_dir, "prompt_template.json"), "w") as f:
            json.dump(prompt_data, f, indent=2)

        # Create sample YAML file (configuration)
        config_data = {"model": "gpt-4", "temperature": 0.7, "max_tokens": 1000}
        with open(os.path.join(temp_dir, "config.yaml"), "w") as f:
            yaml.dump(config_data, f)

        # Create a sample data file (generic data)
        data_file = {
            "entries": [
                {
                    "id": 1,
                    "name": "Amir Mehr",
                    "company": "Zenbase AI",
                    "role": "CTO",
                    "key_details": "Optimizing LLM workflows",
                },
                {
                    "id": 2,
                    "name": "Sarah Johnson",
                    "company": "Tech Solutions Inc.",
                    "role": "Lead Developer",
                    "key_details": "Prompt engineering and model selection",
                },
            ]
        }
        with open(os.path.join(temp_dir, "data.json"), "w") as f:
            json.dump(data_file, f, indent=2)

        yield temp_dir
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir)


@pytest.fixture
def setup_database(test_directory):
    """
    Set up the database with sample data files and reference contexts.
    """
    # Set up Django
    from aiai.utils import setup_django

    setup_django()

    from aiai.app.models import DataFileAnalysis, DataFileInfo, FunctionInfo

    # Clear existing data
    DataFileInfo.objects.all().delete()
    DataFileAnalysis.objects.all().delete()

    # Create function references
    prompt_func = FunctionInfo.objects.create(
        name="load_prompt",
        file_path="/app/prompts.py",
        line_start=1,
        line_end=3,
        signature="def load_prompt()",
        source_code="def load_prompt(): return json.load(open('prompt_template.json'))",
    )

    config_func = FunctionInfo.objects.create(
        name="load_config",
        file_path="/app/config.py",
        line_start=1,
        line_end=3,
        signature="def load_config()",
        source_code="def load_config(): return yaml.safe_load(open('config.yaml'))",
    )

    # Create DataFileInfo objects
    prompt_file = DataFileInfo.objects.create(
        file_path=os.path.join(test_directory, "prompt_template.json"),
        file_type="json",
        content=json.dumps(
            {
                "system": "You are a helpful assistant.",
                "user_prefix": "User: ",
                "assistant_prefix": "Assistant: ",
            }
        ),
        reference_contexts=[
            {
                "function_name": "load_prompt",
                "function_path": "/app/prompts.py",
                "line": 3,
                "content": "return json.load(open('prompt_template.json'))",
            }
        ],
    )
    prompt_file.referenced_by.add(prompt_func)

    config_file = DataFileInfo.objects.create(
        file_path=os.path.join(test_directory, "config.yaml"),
        file_type="yaml",
        content=yaml.dump({"model": "gpt-4", "temperature": 0.7, "max_tokens": 1000}),
        reference_contexts=[
            {
                "function_name": "load_config",
                "function_path": "/app/config.py",
                "line": 3,
                "content": "return yaml.safe_load(open('config.yaml'))",
            }
        ],
    )
    config_file.referenced_by.add(config_func)

    # Create a data file with no analysis yet
    data_file = DataFileInfo.objects.create(
        file_path=os.path.join(test_directory, "data.json"),
        file_type="json",
        content=json.dumps(
            {
                "entries": [
                    {
                        "id": 1,
                        "name": "Amir Mehr",
                        "company": "Zenbase AI",
                        "role": "CTO",
                        "key_details": "Optimizing LLM workflows",
                    },
                    {
                        "id": 2,
                        "name": "Sarah Johnson",
                        "company": "Tech Solutions Inc.",
                        "role": "Lead Developer",
                        "key_details": "Prompt engineering and model selection",
                    },
                ]
            }
        ),
        reference_contexts=[],
    )

    return {
        "prompt_file": prompt_file,
        "config_file": config_file,
        "data_file": data_file,
    }


@pytest.mark.django_db
def test_analyze_all_files(setup_database):
    """Test analyzing all files that need analysis using actual LLM."""
    from aiai.app.models import DataFileAnalysis
    from aiai.code_analyzer.data_file_analyzer import DataFileAnalyzer

    # Create the analyzer with explicit model choice
    analyzer = DataFileAnalyzer(model="openai/gpt-4.1-nano")

    # Run analysis on all files
    result_count = analyzer.analyze()

    # Should have analyzed 3 files
    assert result_count == 3, f"Expected 3 files analyzed, got {result_count}"

    # Check that analyses were saved to the database
    analyses = DataFileAnalysis.objects.all()
    assert analyses.count() == 3, f"Expected 3 analyses in DB, got {analyses.count()}"

    # Check file categorization specifically for each file
    prompt_file = DataFileAnalysis.objects.filter(data_file__file_path__contains="prompt_template.json").first()
    assert prompt_file is not None, "Prompt file not found"
    assert prompt_file.content_category == "prompt", f"Expected 'prompt', got '{prompt_file.content_category}'"

    config_file = DataFileAnalysis.objects.filter(data_file__file_path__contains="config.yaml").first()
    assert config_file is not None, "Config file not found"
    assert config_file.content_category == "configuration", (
        f"Expected 'configuration', got '{config_file.content_category}'"
    )

    data_file = DataFileAnalysis.objects.filter(data_file__file_path__contains="data.json").first()
    assert data_file is not None, "Data file not found"
    assert data_file.content_category == "data", f"Expected 'data', got '{data_file.content_category}'"

    # Verify results are reasonable
    # (we don't know exact outputs since we're using real LLM)
    for analysis in analyses:
        assert analysis.is_valid_reference in [True, False]
        assert analysis.file_purpose, "File purpose should not be empty"
        assert analysis.content_category in [
            "prompt",
            "configuration",
            "data",
            "other",
            "unknown",
        ]
        assert 0 <= analysis.confidence_score <= 1, "Confidence score should be between 0 and 1"


@pytest.mark.django_db
def test_analyze_specific_file(setup_database):
    """Test analyzing a specific file by path using actual LLM."""
    from aiai.app.models import DataFileAnalysis
    from aiai.code_analyzer.data_file_analyzer import DataFileAnalyzer

    # Get a specific file to analyze
    file_path = setup_database["prompt_file"].file_path

    # Create the analyzer and analyze the specific file
    analyzer = DataFileAnalyzer(model="openai/gpt-4.1-nano")
    result = analyzer.analyze(file_path=file_path)

    # Should have analyzed 1 file
    assert result == 1, f"Expected 1 file analyzed, got {result}"

    # Check the database entry
    analysis = DataFileAnalysis.objects.filter(data_file__file_path=file_path).first()
    assert analysis is not None, f"No analysis found for {file_path}"

    # Verify results are reasonable
    assert analysis.is_valid_reference in [True, False]
    assert analysis.file_purpose, "File purpose should not be empty"
    assert analysis.content_category in [
        "prompt",
        "configuration",
        "data",
        "other",
        "unknown",
    ]
    assert 0 <= analysis.confidence_score <= 1, "Confidence score should be between 0 and 1"


@pytest.mark.django_db
def test_analyze_with_return_results(setup_database):
    """Test analyzing files with return_results=True using actual LLM."""
    from aiai.app.models import DataFileAnalysis
    from aiai.code_analyzer.data_file_analyzer import DataFileAnalyzer

    # Clear any existing analyses
    DataFileAnalysis.objects.all().delete()

    # Create the analyzer
    analyzer = DataFileAnalyzer(model="openai/gpt-4.1-nano")

    # Test with a specific file
    file_path = setup_database["prompt_file"].file_path
    result = analyzer.analyze(file_path=file_path, return_results=True)

    # Check the result
    assert isinstance(result, dict), f"Expected dict result, got {type(result)}"
    assert "file_purpose" in result, "Result should have file_purpose"
    assert "content_category" in result, "Result should have content_category"
    assert "confidence_score" in result, "Result should have confidence_score"

    # Clear analyses again for the all-files test
    DataFileAnalysis.objects.all().delete()

    # Test with all files
    results = analyzer.analyze(return_results=True)

    # Check the results
    assert isinstance(results, list), f"Expected list results, got {type(results)}"
    assert len(results) > 0, "Should have at least some results"
    assert all(isinstance(r, dict) for r in results), "Not all results are dictionaries"
    for r in results:
        assert "file_purpose" in r, "Result should have file_purpose"
        assert "content_category" in r, "Result should have content_category"


@pytest.mark.django_db
def test_analyze_file_not_found(setup_database):
    """Test analyzing a file that doesn't exist."""
    from aiai.code_analyzer.data_file_analyzer import DataFileAnalyzer

    # Create the analyzer
    analyzer = DataFileAnalyzer(model="openai/gpt-4.1-nano")

    # Try to analyze a non-existent file
    result = analyzer.analyze(file_path="/nonexistent/file.json")

    # Should return 0 (no files analyzed)
    assert result == 0, f"Expected 0 files analyzed, got {result}"

    # Try with return_results
    result = analyzer.analyze(file_path="/nonexistent/file.json", return_results=True)

    # Should return an empty dict
    assert result == {}, f"Expected empty dict, got {result}"
