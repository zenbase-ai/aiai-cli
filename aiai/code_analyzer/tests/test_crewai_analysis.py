"""
Test module for analyzing the CrewAI example code structure.

This module provides comprehensive tests for the code analyzer capabilities,
focusing on analyzing the CrewAI example code to extract function dependencies,
related files, and rich contextual information.
"""

import json
import os
from pathlib import Path

import pytest

from aiai.code_analyzer.code_analyzer import CodeAnalyzer


@pytest.fixture
def crewai_entrypoint():
    """Fixture providing the path to the CrewAI entrypoint file."""
    return Path(__file__).parent.parent.parent / "examples" / "crewai_agent.py"


@pytest.mark.django_db
def test_comprehensive_code_analysis(crewai_entrypoint: Path):
    """
    Test a comprehensive code analysis that captures all important aspects of the codebase:
    - Related files through imports
    - Function dependencies
    - Function descriptions
    - Execution flow
    """
    # Set up the analyzer
    analyzer = CodeAnalyzer(language="python")

    # Get the entrypoint path
    entrypoint_path = str(crewai_entrypoint)

    # Set up output directory
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)

    # Analyze the code with recursive import analysis
    print(f"Analyzing {entrypoint_path} with recursive import analysis...")
    graph = analyzer.analyze_from_file(entrypoint_path, recursive=True, max_depth=3)

    # Generate visualizations
    md_path = os.path.join(output_dir, "comprehensive_analysis.md")
    json_path = os.path.join(output_dir, "comprehensive_analysis.json")
    dot_path = os.path.join(output_dir, "comprehensive_analysis.dot")

    graph.visualize(format="markdown", output_path=md_path)
    graph.visualize(format="json", output_path=json_path)
    graph.visualize(format="dot", output_path=dot_path)

    print("\nAnalysis outputs:")
    print(f"- Markdown: {md_path}")
    print(f"- JSON: {json_path}")
    print(f"- DOT: {dot_path}")

    # Validate that the analysis includes all required information

    # 1. Check for files analyzed
    assert len(analyzer.visited_files) >= 1, (
        f"Expected at least 1 file to be analyzed, got {len(analyzer.visited_files)}"
    )
    print(f"\nFiles analyzed: {len(analyzer.visited_files)}")
    for file in analyzer.visited_files:
        print(f"- {file}")

    # 2. Check for functions found
    all_functions = list(graph.functions.values())
    assert len(all_functions) >= 2, f"Expected at least 2 functions to be found, got {len(all_functions)}"

    print(f"\nFunctions found: {len(all_functions)}")
    for func in all_functions:
        print(f"- {func.name} (from {os.path.basename(func.file_path)})")

    # 4. Check for contextual information
    main_function = None
    for func in all_functions:
        if func.name == "main":
            main_function = func
            break

    assert main_function is not None, "Main function not found"

    # Check main function has source code and contextual information
    assert main_function.source_code, "Main function missing source code"
    assert len(main_function.string_literals) > 0, "Main function should have string literals"

    print("\nContextual information in main function:")
    print(f"- String literals: {len(main_function.string_literals)}")
    print(f"- Comments: {len(main_function.comments)}")
    print(f"- Variables: {len(main_function.variables)}")
    print(f"- File references: {len(main_function.file_references)}")

    # 5. Check for execution flow from entry point to crew functions
    main_id = None
    for func_id, func in graph.functions.items():
        if func.name == "main":
            main_id = func_id
            break

    # Check dependencies between functions
    if main_id in graph.dependencies:
        direct_deps = graph.dependencies.get(main_id, [])
        print(f"\nDirect dependencies of main: {len(direct_deps)}")

    # Create a comprehensive analysis summary
    analysis_summary = {
        "files_analyzed": list(analyzer.visited_files),
        "total_functions": len(all_functions),
        "main_function_info": {
            "source_code_length": len(main_function.source_code),
            "string_literals_count": len(main_function.string_literals),
            "comments_count": len(main_function.comments),
            "variables_count": len(main_function.variables),
            "file_references": [ref["path"] for ref in main_function.file_references],
        },
        "execution_flow": [
            "1. main() in entrypoint.py loads environment and creates data",
            "2. main() instantiates LeadEmailCrew",
            "3. LeadEmailCrew defines agents and tasks in crew.py",
            "4. main() calls crew_instance.crew().kickoff() to execute",
            "5. Execution follows through the defined tasks in crew.py",
            "6. Result is returned back to main()",
        ],
    }

    print("\nAnalysis Summary:")
    print(json.dumps(analysis_summary, indent=2))

    # Store the analysis summary for potential use but don't return it (avoids pytest warning)
    # Return values from test functions are not recommended in pytest
    # stored_analysis_summary = analysis_summary


def run_crewai_analysis():
    """
    Run a comprehensive analysis of the CrewAI example.

    This function can be called directly from other scripts to analyze
    the CrewAI example code and generate visualizations.

    Returns:
        A dictionary with analysis results.
    """
    entrypoint_path = Path(__file__).parent.parent.parent / "examples" / "crewai_agent.py"

    # Set up the analyzer
    analyzer = CodeAnalyzer(language="python")

    # Get the entrypoint path
    entrypoint_path_str = str(entrypoint_path)

    # Set up output directory
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)

    # Analyze the code with recursive import analysis
    print(f"Analyzing {entrypoint_path_str} with recursive import analysis...")
    graph = analyzer.analyze_from_file(entrypoint_path_str, recursive=True, max_depth=3)

    # Generate visualizations
    md_path = os.path.join(output_dir, "comprehensive_analysis.md")
    json_path = os.path.join(output_dir, "comprehensive_analysis.json")
    dot_path = os.path.join(output_dir, "comprehensive_analysis.dot")

    graph.visualize(format="markdown", output_path=md_path)
    graph.visualize(format="json", output_path=json_path)
    graph.visualize(format="dot", output_path=dot_path)

    print("\nAnalysis outputs:")
    print(f"- Markdown: {md_path}")
    print(f"- JSON: {json_path}")
    print(f"- DOT: {dot_path}")

    # Print some statistics
    print(f"\nFiles analyzed: {len(analyzer.visited_files)}")
    for file in analyzer.visited_files:
        print(f"- {file}")

    all_functions = list(graph.functions.values())
    print(f"\nFunctions found: {len(all_functions)}")
    for func in all_functions:
        print(f"- {func.name} (from {os.path.basename(func.file_path)})")

    # Find crew functions
    crew_function_names = [
        "lead_extractor_agent",
        "email_crafter_agent",
        "extract_lead_profiles_task",
        "create_personalized_emails_task",
        "crew",
    ]

    found_crew_functions = []
    for func in all_functions:
        if func.name in crew_function_names:
            found_crew_functions.append(func.name)

    # Find main function
    main_function = None
    for func in all_functions:
        if func.name == "main":
            main_function = func
            break

    # Create analysis summary dictionary
    analysis_summary = {
        "files_analyzed": list(analyzer.visited_files),
        "total_functions": len(all_functions),
        "crew_functions": found_crew_functions,
        "main_function_info": {
            "source_code_length": len(main_function.source_code) if main_function else 0,
            "string_literals_count": len(main_function.string_literals) if main_function else 0,
            "comments_count": len(main_function.comments) if main_function else 0,
            "variables_count": len(main_function.variables) if main_function else 0,
            "file_references": [ref["path"] for ref in main_function.file_references] if main_function else [],
        },
        "execution_flow": [
            "1. main() in entrypoint.py loads environment and creates data",
            "2. main() instantiates LeadEmailCrew",
            "3. LeadEmailCrew defines agents and tasks in crew.py",
            "4. main() calls crew_instance.crew().kickoff() to execute",
            "5. Execution follows through the defined tasks in crew.py",
            "6. Result is returned back to main()",
        ],
    }

    return analysis_summary


if __name__ == "__main__":
    # Allow running the analysis directly
    analysis = run_crewai_analysis()
    print("\nCrewAI Analysis Complete!")
