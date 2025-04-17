# Code Analyzer Module

## Overview
The Code Analyzer is a powerful tool that analyzes source code files to generate a dependency graph of functions and their relationships, along with rich contextual information. Given an entrypoint file, it intelligently traverses the codebase by following imports, identifying function calls, extracting contextual data, and building a comprehensive graph representation of code structure and dependencies across multiple files.

## Features
- Parse source code using Tree-sitter for accurate and language-agnostic analysis
- Generate function dependency graphs starting from an entrypoint file
- **Smart import resolution** that automatically follows imports to analyze related files
- Recursive analysis with customizable depth to avoid infinite loops
- Extract rich contextual information from functions, including:
  - Full source code
  - Docstrings and comments
  - String literals (potential prompts)
  - Variables and constants
  - File references
- Support for multiple programming languages (currently Python, with JavaScript and others planned)
- Multiple visualization formats:
  - Markdown (LLM-friendly, with Mermaid diagrams)
  - JSON (structured data for further processing)
  - DOT (for graph visualization tools)
- Extensible architecture for adding new language parsers
- Comprehensive test coverage with pytest

## Architecture

### Core Components

1. **Parser Interface**: Abstract interface for language-specific parsers
   - Tree-sitter integration for syntax parsing
   - Language-specific implementations
   - Context extraction capabilities
   - Import resolution to find related files

2. **Dependency Analyzer**: Builds the function dependency graph
   - Identifies function definitions and calls
   - Resolves imports and module references
   - Tracks function call hierarchy
   - Extracts contextual information from functions
   - Recursively analyzes imported files

3. **Graph Builder**: Constructs a graph representation of function dependencies
   - Nodes represent functions with rich contextual information
   - Edges represent function calls
   - Includes metadata (file location, function signatures, docstrings, etc.)
   - Links functions across different files

4. **Output Formatter**: Converts the graph into various output formats
   - JSON for structured data
   - Markdown for LLM-friendly visualization (with Mermaid diagrams)
   - DOT for integration with graph visualization tools

## Usage

### Basic Usage

```python
from aiai.code_analyzer import CodeAnalyzer

# Initialize the analyzer with the appropriate language parser
analyzer = CodeAnalyzer(language="python")

# Analyze code starting from an entrypoint file without following imports
graph = analyzer.analyze_from_file("/path/to/entrypoint.py")

# Generate LLM-friendly Markdown visualization with rich context
graph.visualize(format="markdown", output_path="/path/to/analysis.md")
```

### Recursive Analysis with Smart Import Resolution

For complete analysis that automatically follows imports:

```python
from aiai.code_analyzer import CodeAnalyzer

# Initialize analyzer
analyzer = CodeAnalyzer(language="python")

# Analyze with automatic import resolution
graph = analyzer.analyze_from_file(
    "/path/to/entrypoint.py", 
    recursive=True,   # Enable recursive import analysis
    max_depth=3       # Set maximum recursion depth to avoid loops
)

# Generate visualizations
graph.visualize(format="markdown", output_path="/path/to/comprehensive_analysis.md")
graph.visualize(format="json", output_path="/path/to/comprehensive_analysis.json")
graph.visualize(format="dot", output_path="/path/to/comprehensive_analysis.dot")
```

This approach will:
1. Start with the entrypoint file
2. Identify all imports in the file
3. Intelligently resolve those imports to actual file paths
4. Recursively analyze each imported file
5. Continue this process until all imports are analyzed (up to max_depth)

### Benefits of Smart Import Resolution

The automatic import resolution provides several advantages:

1. **Accurate dependency mapping**: Only analyze files that are actually imported and used
2. **Complete code understanding**: Follow the actual import graph to analyze all relevant code
3. **No manual file selection**: No need to manually specify which files to analyze
4. **Cross-file context**: Understand how functions in different files relate to each other
5. **True dependency graph**: Generate a graph that represents the actual code dependencies

## Rich Context Extraction

The analyzer extracts comprehensive contextual information from functions:

```python
# Sample code with rich context
def generate_response(query, system_prompt=DEFAULT_PROMPT):
    """
    Generate a response for the given query using the specified prompt.
    
    Args:
        query: The user query to respond to
        system_prompt: The system prompt to use
        
    Returns:
        The generated response
    """
    # Combine the system prompt and user query
    full_prompt = f"{system_prompt}\n\nUser query: {query}"
    
    # Call the LLM API with the prompt
    response = call_llm_api(full_prompt)
    
    return response
```

The analyzer will extract:
- Function signature: `generate_response(query, system_prompt=DEFAULT_PROMPT)`
- Docstring: Full docstring with parameter and return information
- Comments: The comment about combining prompts
- String literals: The template string that might contain prompt elements
- Variables: `full_prompt`, `response`
- Dependencies: The call to `call_llm_api`

## Case Study: CrewAI Example Analysis

The code analyzer has been successfully used to analyze complex projects like the CrewAI example, which involves multiple files with interrelated functions and classes.

Key findings from the CrewAI analysis:
- **Import resolution**: Automatically discovered the relationship between `entrypoint.py` and `crew.py`
- **Cross-file tracing**: Successfully tracked function calls between files
- **Function discovery**: Identified all key functions across multiple files
- **Execution flow**: Mapped the complete execution flow from main function to crew execution
- **Function relationships**: Identified how the main function interacts with the CrewAI framework
- **Rich context**: Extracted docstrings, comments, and string literals that provide insights into the functionality

Analysis outputs:
- A comprehensive Markdown report with function details and dependencies
- A structured JSON representation for further processing
- A DOT graph for visualization in tools like Graphviz

## How Import Resolution Works

The import resolution system works through several steps:

1. **Parsing imports**: Extract all import statements from the code using Tree-sitter queries
2. **Resolving module paths**: Convert module names to file paths:
   - Regular imports (`import module`)
   - From imports (`from module import thing`) 
   - Relative imports (`from .module import thing`)
3. **Path resolution**: Find the actual file path by checking various possible locations
4. **Recursive analysis**: Analyze each imported file with the same process

The system handles complex cases like:
- Relative imports that refer to parent directories
- Module imports that might be files or directories with `__init__.py`
- Package-relative imports
- Special case handling for specific project structures

## Adding New Language Support

The module is designed to be extensible, allowing new language parsers to be added easily:

1. Create a new parser class that implements the `LanguageParser` interface
2. Register the new parser with the main `CodeAnalyzer` class
3. Implement language-specific parsing logic using Tree-sitter
4. Implement the context extraction method
5. Implement import resolution for the specific language

Example for adding JavaScript support:

```python
from aiai.code_analyzer.parsers import LanguageParser, register_parser

@register_parser("javascript")
class JavaScriptParser(LanguageParser):
    def __init__(self):
        super().__init__()
        # Initialize Tree-sitter for JavaScript
        
    def parse_file(self, file_path):
        # JavaScript-specific parsing logic
        
    def extract_functions(self, ast):
        # Extract functions from JavaScript AST
        
    def identify_function_calls(self, ast, functions):
        # Identify function calls in JavaScript
        
    def extract_function_context(self, parsed_data, function):
        # Extract rich contextual information from JavaScript functions
        
    def extract_imports(self, parsed_data):
        # Extract import/require statements from JavaScript code
```

## Applications

The code analyzer is particularly useful for:

1. **Understanding code structure**: Quickly grasp how a codebase is organized and how functions interact across multiple files
2. **Identifying prompts in code**: Extract strings, templates, and variables that might contain prompts
3. **Documentation generation**: Automatically create LLM-friendly documentation from code
4. **Code refactoring**: Identify dependencies that might be affected by changes
5. **LLM integration**: Feed the structured code information to LLMs for better code understanding
6. **Cross-file dependency analysis**: Trace function calls and data flow across different modules
7. **Codebase exploration**: Explore unfamiliar codebases by following imports and dependencies

## Roadmap

- [x] Initial architecture design
- [x] Python parser implementation
- [x] Rich context extraction
- [x] Multiple visualization formats (Markdown, JSON, DOT)
- [x] Comprehensive test suite with pytest
- [x] Cross-file analysis for Python projects
- [x] Improved automatic import resolution and recursive analysis
- [ ] JavaScript parser implementation
- [ ] Support for class methods and inheritance
- [ ] Cross-language dependencies
- [ ] Performance optimizations for large codebases
- [ ] Web interface for interactive exploration