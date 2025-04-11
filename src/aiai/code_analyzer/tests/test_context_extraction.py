"""
Test script for the enhanced code analyzer with context extraction.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from aiai.code_analyzer.analyzer import CodeAnalyzer

def main():
    # Create a code analyzer for Python
    analyzer = CodeAnalyzer(language="python")
    
    # Get the path to the prompt_example.py file
    test_dir = Path(__file__).parent
    prompt_example_path = test_dir / "prompt_example.py"
    
    print(f"Analyzing {prompt_example_path}...")
    
    # Analyze the prompt example file
    dependency_graph = analyzer.analyze_from_file(str(prompt_example_path))
    
    # Create the output directory if it doesn't exist
    output_dir = test_dir / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Generate the Markdown visualization
    output_path = output_dir / "prompt_example_analysis.md"
    dependency_graph.visualize(format="markdown", output_path=str(output_path))
    
    print(f"Analysis complete. Output saved to {output_path}")
    
    # Generate other formats for comparison
    dependency_graph.visualize(format="json", output_path=str(output_dir / "prompt_example_analysis.json"))
    dependency_graph.visualize(format="dot", output_path=str(output_dir / "prompt_example_analysis.dot"))
    
    print("All visualizations generated successfully.")

if __name__ == "__main__":
    main()
