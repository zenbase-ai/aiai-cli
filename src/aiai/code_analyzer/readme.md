# Code Analyzer Module

## Overview
The Code Analyzer is a service that analyzes source code files to generate a dependency graph of functions and their relationships, along with rich contextual information. Given an entrypoint file, it traverses the codebase, identifying function calls, extracting contextual data, and building a comprehensive graph representation of code structure and dependencies.

## Features
- Parse source code using Tree-sitter for accurate and language-agnostic analysis
- Generate function dependency graphs starting from an entrypoint file
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

2. **Dependency Analyzer**: Builds the function dependency graph
   - Identifies function definitions and calls
   - Resolves imports and module references
   - Tracks function call hierarchy
   - Extracts contextual information from functions

3. **Graph Builder**: Constructs a graph representation of function dependencies
   - Nodes represent functions with rich contextual information
   - Edges represent function calls
   - Includes metadata (file location, function signatures, docstrings, etc.)

4. **Output Formatter**: Converts the graph into various output formats
   - JSON for structured data
   - Markdown for LLM-friendly visualization (with Mermaid diagrams)
   - DOT for integration with graph visualization tools

## Usage

```python
from aiai.code_analyzer import CodeAnalyzer

# Initialize the analyzer with the appropriate language parser
analyzer = CodeAnalyzer(language="python")

# Analyze code starting from an entrypoint file
graph = analyzer.analyze_from_file("/path/to/entrypoint.py")

# Generate LLM-friendly Markdown visualization with rich context
graph.visualize(format="markdown", output_path="/path/to/analysis.md")

# Export structured data as JSON
graph.visualize(format="json", output_path="/path/to/analysis.json")

# Generate DOT graph for visualization tools
graph.visualize(format="dot", output_path="/path/to/analysis.dot")
```

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

## Adding New Language Support

The module is designed to be extensible, allowing new language parsers to be added easily:

1. Create a new parser class that implements the `LanguageParser` interface
2. Register the new parser with the main `CodeAnalyzer` class
3. Implement language-specific parsing logic using Tree-sitter
4. Implement the context extraction method

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
```

## Applications

The code analyzer is particularly useful for:

1. **Understanding code structure**: Quickly grasp how a codebase is organized and how functions interact
2. **Identifying prompts in code**: Extract strings, templates, and variables that might contain prompts
3. **Documentation generation**: Automatically create LLM-friendly documentation from code
4. **Code refactoring**: Identify dependencies that might be affected by changes
5. **LLM integration**: Feed the structured code information to LLMs for better code understanding

## Roadmap

- [x] Initial architecture design
- [x] Python parser implementation
- [x] Rich context extraction
- [x] Multiple visualization formats (Markdown, JSON, DOT)
- [x] Comprehensive test suite with pytest
- [ ] JavaScript parser implementation
- [ ] Support for class methods and inheritance
- [ ] Cross-language dependencies
- [ ] Performance optimizations for large codebases
- [ ] Web interface for interactive exploration