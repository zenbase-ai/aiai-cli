#!/usr/bin/env python
"""
Script to test database saving functionality of the code analyzer.
This script tests the ability to analyze Python files and save function information to the database.
"""

import os
from pathlib import Path

import pytest


# This enables the script to be run either as a standalone or via pytest
def analyze_and_save_functions():
    """
    Analyze Python files and save functions to the database.
    Returns a summary of saved functions.
    """
    # Set up Django first
    from aiai.utils import setup_django

    setup_django()

    # Import after Django is set up
    from aiai.app.models import FunctionInfo
    from aiai.code_analyzer import CodeAnalyzer

    # Clear any existing function data for clean testing
    FunctionInfo.objects.all().delete()
    print("Database cleared")

    # Initialize the analyzer
    analyzer = CodeAnalyzer()

    # Get the tests directory path
    tests_dir = Path(__file__).parent

    # Analyze sample_entrypoint.py file which has multiple functions
    sample_file = tests_dir / "sample_entrypoint.py"
    if sample_file.exists():
        print(f"Analyzing {sample_file.name}")
        analyzer.analyze_from_file(str(sample_file), save_to_db=True)

    # Verify that functions were saved to the database
    function_count = FunctionInfo.objects.count()
    print(f"Total functions saved to database: {function_count}")

    # Print some basic stats about the functions
    print("\nFunctions by file:")
    file_counts = {}
    for func in FunctionInfo.objects.all():
        file_name = os.path.basename(func.file_path)
        if file_name not in file_counts:
            file_counts[file_name] = 0
        file_counts[file_name] += 1

    for file_name, count in sorted(file_counts.items()):
        print(f"  {file_name}: {count} functions")

    # Report on function details for one file
    if file_counts:
        sample_file_name = list(file_counts.keys())[0]
        print(f"\nFunctions in {sample_file_name}:")
        for func in FunctionInfo.objects.filter(file_path__endswith=sample_file_name)[:5]:
            print(f"  {func.name} ({func.line_start}-{func.line_end}): {func.signature}")

    print("\nTest completed successfully!")

    return {"function_count": function_count, "files": file_counts}


# This function can be called by pytest
@pytest.mark.django_db
def test_function_saving():
    """
    Simple test function for pytest that analyzes files and saves to DB.
    """
    # When running as a pytest test, we'll just check if the function runs without error
    results = analyze_and_save_functions()
    assert results["function_count"] > 0, "No functions were saved to the database"


if __name__ == "__main__":
    # Run as a script
    analyze_and_save_functions()
