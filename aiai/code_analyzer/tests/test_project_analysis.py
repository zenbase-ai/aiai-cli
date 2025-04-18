#!/usr/bin/env python
"""
Test script for the comprehensive project analysis functionality.
This tests the analyze_project method which handles both code and data file analysis.
"""

import json
import os
import shutil
import tempfile

import pytest
import yaml


@pytest.fixture
def test_project_directory():
    """
    Create a temporary directory with a sample project structure for testing.
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    try:
        # Create a project structure with Python files and data files

        # Main entrypoint file
        entrypoint_code = """
def main():
    \"\"\"Main function that orchestrates everything.\"\"\"
    config = load_config()
    prompt = load_prompt()
    result = process_data(config, prompt)
    return result

def load_config():
    \"\"\"Load configuration from a YAML file.\"\"\"
    import yaml
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def load_prompt():
    \"\"\"Load a prompt from a JSON file.\"\"\"
    import json
    with open('prompts/system_prompt.json', 'r') as f:
        return json.load(f)

def process_data(config, prompt):
    \"\"\"Process data using configuration and prompt.\"\"\"
    from .utils import format_prompt
    formatted = format_prompt(prompt, config['parameters'])
    return formatted
"""
        # Utils module with helper functions
        utils_code = """
def format_prompt(prompt_template, parameters):
    \"\"\"Format a prompt template with given parameters.\"\"\"
    formatted = prompt_template['template'].format(**parameters)
    return {
        "formatted_prompt": formatted,
        "system_message": prompt_template.get("system", "")
    }
"""
        # Create directory structure
        os.makedirs(os.path.join(temp_dir, "prompts"), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, "utils"), exist_ok=True)

        # Write Python files
        with open(os.path.join(temp_dir, "main.py"), "w") as f:
            f.write(entrypoint_code)

        with open(os.path.join(temp_dir, "utils", "__init__.py"), "w") as f:
            f.write("")

        with open(os.path.join(temp_dir, "utils", "formatting.py"), "w") as f:
            f.write(utils_code)

        # Create config YAML file
        config_data = {
            "model": "gpt-4",
            "temperature": 0.7,
            "parameters": {"user_name": "Test User", "task": "code analysis"},
        }
        with open(os.path.join(temp_dir, "config.yaml"), "w") as f:
            yaml.dump(config_data, f)

        # Create prompt JSON file
        prompt_data = {
            "system": "You are a helpful assistant specialized in code analysis.",
            "template": "Hello {user_name}, I'll help you with {task}.",
        }
        with open(os.path.join(temp_dir, "prompts", "system_prompt.json"), "w") as f:
            json.dump(prompt_data, f, indent=2)

        # Create a file that shouldn't be analyzed (package.json)
        package_data = {"name": "test-project", "version": "1.0.0"}
        with open(os.path.join(temp_dir, "package.json"), "w") as f:
            json.dump(package_data, f, indent=2)

        yield temp_dir
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir)


@pytest.mark.django_db
def test_analyze_project(test_project_directory):
    """Test the comprehensive project analysis functionality."""
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

    # Get the entrypoint file path
    entrypoint_file = os.path.join(test_project_directory, "main.py")

    # Run the comprehensive analysis
    results = analyzer.analyze_project(entrypoint_file, save_to_db=True)

    # Check the results
    assert "code_graph" in results, "Results should contain code_graph"
    assert "data_files" in results, "Results should contain data_files"

    # Check if functions were found and saved
    code_graph = results["code_graph"]
    assert len(code_graph.functions) >= 4, f"Expected at least 4 functions, found {len(code_graph.functions)}"

    # Check function database records
    assert FunctionInfo.objects.count() >= 4, (
        f"Expected at least 4 functions in database, found {FunctionInfo.objects.count()}"
    )

    # Check for specific functions
    function_names = [func.name for _, func in code_graph.functions.items()]
    assert "main" in function_names, "Main function not found"
    assert "load_config" in function_names, "load_config function not found"
    assert "load_prompt" in function_names, "load_prompt function not found"

    # Check if data files were found and saved
    data_files = results["data_files"]
    assert len(data_files) >= 2, f"Expected at least 2 data files, found {len(data_files)}"

    # Check data file database records
    assert DataFileInfo.objects.count() >= 2, (
        f"Expected at least 2 data files in database, found {DataFileInfo.objects.count()}"
    )

    # Check for specific data files
    data_file_paths = DataFileInfo.objects.values_list("file_path", flat=True)
    data_file_basenames = [os.path.basename(path) for path in data_file_paths]

    assert "config.yaml" in data_file_basenames, "config.yaml not found"
    assert "system_prompt.json" in data_file_basenames, "system_prompt.json not found"
    assert "package.json" not in data_file_basenames, "package.json should be excluded"

    # Check for references to data files in functions
    json_file = DataFileInfo.objects.filter(file_type="json").first()
    assert json_file is not None, "JSON file not found in database"
    assert json_file.referenced_by.count() > 0, (
        f"Expected references to JSON file, found {json_file.referenced_by.count()}"
    )

    yaml_file = DataFileInfo.objects.filter(file_type="yaml").first()
    assert yaml_file is not None, "YAML file not found in database"
    assert yaml_file.referenced_by.count() > 0, (
        f"Expected references to YAML file, found {yaml_file.referenced_by.count()}"
    )

    # Check specific references
    load_prompt_func = FunctionInfo.objects.filter(name="load_prompt").first()
    assert load_prompt_func is not None, "load_prompt function not found in database"

    load_config_func = FunctionInfo.objects.filter(name="load_config").first()
    assert load_config_func is not None, "load_config function not found in database"

    # Verify that the correct functions reference the data files
    assert load_prompt_func in json_file.referenced_by.all(), "JSON file should be referenced by load_prompt"
    assert load_config_func in yaml_file.referenced_by.all(), "YAML file should be referenced by load_config"
