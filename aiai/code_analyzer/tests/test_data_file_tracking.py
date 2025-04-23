#!/usr/bin/env python
"""
Test script for the data file tracking functionality.
This script tests the ability to find JSON/YAML files and track their references in code.
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
    Create a temporary directory with sample code and data files for testing.
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    try:
        # Create sample Python file that references data files
        sample_code = """
def load_prompt():
    \"\"\"Load a prompt from a JSON file.\"\"\"
    import json
    with open('prompt_template.json', 'r') as f:
        return json.load(f)

def process_config():
    \"\"\"Process configuration from a YAML file.\"\"\"
    import yaml
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def unrelated_function():
    \"\"\"This function doesn't reference any data files.\"\"\"
    return "Hello World"
"""
        # Write the sample code file
        with open(os.path.join(temp_dir, "sample_code.py"), "w") as f:
            f.write(sample_code)

        # Create sample JSON file
        prompt_data = {
            "system": "You are a helpful assistant.",
            "user_prefix": "User: ",
            "assistant_prefix": "Assistant: ",
        }
        with open(os.path.join(temp_dir, "prompt_template.json"), "w") as f:
            json.dump(prompt_data, f, indent=2)

        # Create sample YAML file
        config_data = {"model": "gpt-4", "temperature": 0.7, "max_tokens": 1000}
        with open(os.path.join(temp_dir, "config.yaml"), "w") as f:
            yaml.dump(config_data, f)

        # Create a file that shouldn't be analyzed (package.json)
        package_data = {"name": "test-package", "version": "1.0.0"}
        with open(os.path.join(temp_dir, "package.json"), "w") as f:
            json.dump(package_data, f, indent=2)

        yield temp_dir
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir)


@pytest.mark.django_db
def test_find_data_files(test_directory):
    """Test the ability to find JSON and YAML files in a directory."""
    from aiai.code_analyzer import CodeAnalyzer

    # Initialize the analyzer
    analyzer = CodeAnalyzer()

    # Find data files
    data_files = analyzer.find_data_files(test_directory)

    # There should be 2 data files (prompt_template.json and config.yaml)
    # package.json should be excluded as it's a configuration file
    assert len(data_files) == 2, f"Expected 2 data files, found {len(data_files)}"

    # Check if the correct files were found
    file_names = [os.path.basename(f) for f in data_files]
    assert "prompt_template.json" in file_names, "Missing prompt_template.json"
    assert "config.yaml" in file_names, "Missing config.yaml"
    assert "package.json" not in file_names, "package.json should be excluded"


@pytest.mark.django_db
def test_find_file_references(test_directory):
    """Test the ability to find references to data files in code."""
    # Set up Django
    from aiai.utils import setup_django

    setup_django()

    from aiai.app.models import FunctionInfo
    from aiai.code_analyzer import CodeAnalyzer

    # Clear existing function data
    FunctionInfo.objects.all().delete()

    # Initialize the analyzer
    analyzer = CodeAnalyzer()

    # First, analyze the code file to populate the function database
    code_file = os.path.join(test_directory, "sample_code.py")
    analyzer.analyze_from_file(code_file, save_to_db=True)

    # Check if functions were saved to the database
    assert FunctionInfo.objects.count() == 3, f"Expected 3 functions, found {FunctionInfo.objects.count()}"

    # Now find references to the JSON file
    json_file = os.path.join(test_directory, "prompt_template.json")
    json_references = analyzer.find_file_references_in_code(json_file)

    # There should be 1 reference to the JSON file in the load_prompt function
    assert len(json_references) == 1, f"Expected 1 reference to JSON file, found {len(json_references)}"
    assert json_references[0]["function"].name == "load_prompt", (
        f"Expected reference in load_prompt, found in {json_references[0]['function'].name}"
    )

    # Find references to the YAML file
    yaml_file = os.path.join(test_directory, "config.yaml")
    yaml_references = analyzer.find_file_references_in_code(yaml_file)

    # There should be 1 reference to the YAML file in the process_config function
    assert len(yaml_references) == 1, f"Expected 1 reference to YAML file, found {len(yaml_references)}"
    assert yaml_references[0]["function"].name == "process_config", (
        f"Expected reference in process_config, found in {yaml_references[0]['function'].name}"
    )


@pytest.mark.django_db
def test_save_data_files_to_db(test_directory):
    """Test saving data files and their references to the database."""
    # Set up Django
    from aiai.utils import setup_django

    setup_django()

    from aiai.app.models import DataFileInfo, FunctionInfo
    from aiai.code_analyzer import CodeAnalyzer

    # Clear existing data
    FunctionInfo.objects.all().delete()
    DataFileInfo.objects.all().delete()

    # Initialize the analyzer
    analyzer = CodeAnalyzer()

    # First, analyze the code file to populate the function database
    code_file = os.path.join(test_directory, "sample_code.py")
    analyzer.analyze_from_file(code_file, save_to_db=True)

    # Now find and save data files
    analyzer.find_and_save_data_files(test_directory)

    # There should be 2 data files saved to the database
    assert DataFileInfo.objects.count() == 2, f"Expected 2 data files, found {DataFileInfo.objects.count()}"

    # Check if the JSON file was saved correctly
    json_file = DataFileInfo.objects.filter(file_type="json").first()
    assert json_file is not None, "JSON file not found in database"
    assert json_file.file_path.endswith("prompt_template.json"), f"Unexpected JSON file path: {json_file.file_path}"
    assert json_file.referenced_by.count() == 1, (
        f"Expected 1 reference to JSON file, found {json_file.referenced_by.count()}"
    )
    assert json_file.referenced_by.first().name == "load_prompt", (
        f"Expected reference from load_prompt, found {json_file.referenced_by.first().name}"
    )

    # Check if the YAML file was saved correctly
    yaml_file = DataFileInfo.objects.filter(file_type="yaml").first()
    assert yaml_file is not None, "YAML file not found in database"
    assert yaml_file.file_path.endswith("config.yaml"), f"Unexpected YAML file path: {yaml_file.file_path}"
    assert yaml_file.referenced_by.count() == 1, (
        f"Expected 1 reference to YAML file, found {yaml_file.referenced_by.count()}"
    )
    assert yaml_file.referenced_by.first().name == "process_config", (
        f"Expected reference from process_config, found {yaml_file.referenced_by.first().name}"
    )


@pytest.mark.django_db
def test_data_file_analyzer(test_directory):
    """Test the DataFileAnalyzer class for analyzing data files."""
    # Set up Django
    from aiai.utils import setup_django

    setup_django()

    from aiai.app.models import DataFileAnalysis, DataFileInfo, FunctionInfo
    from aiai.code_analyzer import CodeAnalyzer
    from aiai.code_analyzer.data_file_analyzer import DataFileAnalyzer

    # Clear existing data
    FunctionInfo.objects.all().delete()
    DataFileInfo.objects.all().delete()

    # Initialize the analyzer
    analyzer = CodeAnalyzer()

    # First, analyze the code file to populate the function database
    code_file = os.path.join(test_directory, "sample_code.py")
    analyzer.analyze_from_file(code_file, save_to_db=True)

    # Find and save data files
    analyzer.find_and_save_data_files(test_directory)

    # Now run the data file analyzer
    data_analyzer = DataFileAnalyzer()
    analyzed_count = data_analyzer.analyze()

    # There should be 2 data files analyzed
    assert analyzed_count == 2, f"Expected 2 data files analyzed, found {analyzed_count}"

    # Check if analysis records were created
    assert DataFileAnalysis.objects.count() == 2, (
        f"Expected 2 analysis records, found {DataFileAnalysis.objects.count()}"
    )

    # Check the JSON file analysis
    json_analysis = DataFileAnalysis.objects.filter(data_file__file_type="json").first()
    assert json_analysis is not None, "JSON file analysis not found"
    assert json_analysis.is_valid_reference, "JSON file should be marked as a valid reference"

    # Check the YAML file analysis
    yaml_analysis = DataFileAnalysis.objects.filter(data_file__file_type="yaml").first()
    assert yaml_analysis is not None, "YAML file analysis not found"
    assert yaml_analysis.is_valid_reference, "YAML file should be marked as a valid reference"


@pytest.mark.django_db
def test_save_data_files_to_db_crewai(test_directory):
    """Test saving data files and their references to the database."""
    # Set up Django
    from aiai.utils import setup_django

    setup_django()

    from pathlib import Path

    from aiai.app.models import DataFileAnalysis, DataFileInfo, FunctionInfo
    from aiai.code_analyzer import CodeAnalyzer
    from aiai.code_analyzer.data_file_analyzer import DataFileAnalyzer

    # Calculate the project root path
    project_root = Path(__file__).parent.parent.parent.parent
    crewai_path = project_root / "aiai" / "examples" / "crewai"

    # Ensure path exists
    assert crewai_path.exists(), f"CrewAI path does not exist: {crewai_path}"

    # Clear existing data
    FunctionInfo.objects.all().delete()
    DataFileInfo.objects.all().delete()
    DataFileAnalysis.objects.all().delete()

    # Initialize the analyzer
    analyzer = CodeAnalyzer()

    # First, analyze the code file to populate the function database
    code_file = str(crewai_path / "entrypoint.py")
    analyzer.analyze_from_file(code_file, save_to_db=True, recursive=True)

    # Assert functions were saved to the database
    assert FunctionInfo.objects.count() == 6, f"Expected 6 functions, found {FunctionInfo.objects.count()}"

    # Now find and save data files
    analyzer.find_and_save_data_files(str(crewai_path))

    # There should be 1 data file saved to the database (people_data.json)
    assert DataFileInfo.objects.count() == 1, f"Expected 1 data file, found {DataFileInfo.objects.count()}"

    # Check if the JSON file was saved correctly
    json_file = DataFileInfo.objects.filter(file_type="json").first()
    assert json_file is not None, "JSON file not found in database"
    assert json_file.file_path.endswith("people_data.json"), f"Unexpected JSON file path: {json_file.file_path}"

    # Check references to the JSON file
    # The file is referenced in extract_lead_profiles_task and at module level with file_read_tool
    reference_count = json_file.referenced_by.count()
    assert reference_count >= 1, f"Expected at least 1 reference to people_data.json, found {reference_count}"

    # At least one reference should be in the crew.py file
    crew_references = json_file.referenced_by.filter(file_path__contains="crew.py")
    assert crew_references.exists(), "Expected references from crew.py but found none"

    # Now analyze the data files using DataFileAnalyzer
    data_analyzer = DataFileAnalyzer(model="openai/gpt-4.1-nano")
    analyzed_count = data_analyzer.analyze()

    # Verify that the file was analyzed
    assert analyzed_count == 1, f"Expected 1 data file analyzed, found {analyzed_count}"

    # Verify the analysis results were saved to the database
    assert DataFileAnalysis.objects.count() == 1, (
        f"Expected 1 analysis record, found {DataFileAnalysis.objects.count()}"
    )

    # Get the analysis results
    analysis = DataFileAnalysis.objects.first()
    assert analysis is not None, "Analysis not found"
    assert analysis.is_valid_reference, "File should be marked as a valid reference"
    assert analysis.content_category == "data", f"Expected category 'data', found '{analysis.content_category}'"

    # Verify that the analysis has a file purpose
    assert analysis.file_purpose, "Analysis should have a file purpose"
    assert analysis.confidence_score > 0.5, f"Expected confidence score > 0.5, found {analysis.confidence_score}"
