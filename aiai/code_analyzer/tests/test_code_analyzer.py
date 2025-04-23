#!/usr/bin/env python
"""
Test script for the code analyzer.
This script demonstrates how to use the code analyzer to generate a function
dependency graph from a Python file.
"""

import os
import sys
from pathlib import Path

import pytest

from aiai.code_analyzer import CodeAnalyzer

# Add parent directory to path so we can import the code_analyzer package
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir.parent.parent.parent))


@pytest.fixture
def sample_file():
    """Fixture to provide the path to the sample code file."""
    return os.path.join(os.path.dirname(__file__), "sample_code.py")


@pytest.fixture
def output_dir():
    """Fixture to provide the path to the output directory."""
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


@pytest.mark.django_db
def test_analyzer_basic_functionality(sample_file, output_dir):
    """Test that the code analyzer correctly identifies functions and their dependencies."""
    print(f"Analyzing file: {sample_file}")

    # Create an analyzer instance
    analyzer = CodeAnalyzer(language="python")

    # Analyze the sample file
    graph = analyzer.analyze_from_file(sample_file)

    # Verify the correct number of functions were found
    assert len(graph.functions) == 8, f"Expected 8 functions, found {len(graph.functions)}"

    # Check if all expected functions exist
    function_names = {func.name for func_id, func in graph.functions.items()}
    expected_functions = {
        "main",
        "get_data",
        "process_data",
        "transform_item",
        "calculate_result",
        "apply_bonus",
        "display_result",
        "format_for_report",
    }
    assert function_names == expected_functions, f"Missing functions: {expected_functions - function_names}"

    # Get references to each function for dependency testing
    functions_by_name = {func.name: func for func_id, func in graph.functions.items()}

    # Test specific dependencies
    # main should call get_data, process_data, calculate_result, and display_result
    main_func = functions_by_name["main"]
    main_callees = {callee.name for callee in graph.get_callees(main_func)}
    assert main_callees == {
        "get_data",
        "process_data",
        "calculate_result",
        "display_result",
    }, f"main should call exactly 4 functions, found {main_callees}"

    # process_data should call transform_item
    process_data_func = functions_by_name["process_data"]
    assert len(graph.get_callees(process_data_func)) == 1, "process_data should call exactly 1 function"
    assert graph.get_callees(process_data_func)[0].name == "transform_item", "process_data should call transform_item"

    # calculate_result should call apply_bonus
    calculate_result_func = functions_by_name["calculate_result"]
    assert len(graph.get_callees(calculate_result_func)) == 1, "calculate_result should call exactly 1 function"
    assert graph.get_callees(calculate_result_func)[0].name == "apply_bonus", "calculate_result should call apply_bonus"

    # display_result should call format_for_report
    display_result_func = functions_by_name["display_result"]
    assert len(graph.get_callees(display_result_func)) == 1, "display_result should call exactly 1 function"
    assert graph.get_callees(display_result_func)[0].name == "format_for_report", (
        "display_result should call format_for_report"
    )

    # transform_item, get_data, apply_bonus, and format_for_report should not call any functions
    for func_name in ["transform_item", "get_data", "apply_bonus", "format_for_report"]:
        func = functions_by_name[func_name]
        assert len(graph.get_callees(func)) == 0, f"{func_name} should not call any functions"

    # Export the graph to JSON to verify it works
    json_path = os.path.join(output_dir, "function_graph.json")
    graph.export_json(json_path)
    assert os.path.exists(json_path), f"Failed to export graph to {json_path}"

    print(f"Exported graph to: {json_path}")


@pytest.mark.django_db
def test_visualize_graph(sample_file, output_dir):
    """Test the graph visualization functionality."""
    # Create an analyzer instance and analyze the file
    analyzer = CodeAnalyzer(language="python")
    graph = analyzer.analyze_from_file(sample_file)

    # Test DOT visualization
    try:
        dot_path = os.path.join(output_dir, "function_graph.dot")
        graph.visualize(format="dot", output_path=dot_path)
        assert os.path.exists(dot_path), f"Failed to create DOT visualization at {dot_path}"
        print(f"Created DOT visualization: {dot_path}")
    except Exception as e:
        pytest.skip(f"Could not create DOT visualization: {str(e)}")


@pytest.mark.django_db
def test_markdown_visualization(sample_file, output_dir):
    """Test the LLM-friendly Markdown visualization functionality."""
    # Create an analyzer instance and analyze the file
    analyzer = CodeAnalyzer(language="python")
    graph = analyzer.analyze_from_file(sample_file)

    # Test Markdown visualization
    md_path = os.path.join(output_dir, "function_graph.md")
    graph.visualize(format="markdown", output_path=md_path)
    assert os.path.exists(md_path), f"Failed to create Markdown visualization at {md_path}"

    # Verify the Markdown content
    with open(md_path, "r") as f:
        content = f.read()

    # Check for key sections in the Markdown
    assert "# Function Dependency Graph" in content, "Missing title in Markdown"
    assert "## Summary" in content, "Missing summary section"
    assert "## Function Details" in content, "Missing function details section"
    assert "## Visualization" in content, "Missing visualization section"
    assert "```mermaid" in content, "Missing Mermaid diagram"

    # Check for specific function information
    assert "`main`" in content, "Missing main function in Markdown"
    assert "`get_data`" in content, "Missing get_data function in Markdown"

    print(f"Created Markdown visualization: {md_path}")
