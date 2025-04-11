# Code Analyzer Module

## Overview
The Code Analyzer is a service that analyzes source code files to generate a dependency graph of functions and their relationships. Given an entrypoint file, it traverses the codebase, identifying function calls and building a graph representation of how functions are connected.

## Features
- Parse source code using Tree-sitter for accurate and language-agnostic analysis
- Generate function dependency graphs starting from an entrypoint file
- Support for multiple programming languages (initially Python, with JavaScript and others planned)
- Extensible architecture for adding new language parsers
- Visualization of function call hierarchies

## Architecture

### Core Components

1. **Parser Interface**: Abstract interface for language-specific parsers
   - Tree-sitter integration for syntax parsing
   - Language-specific implementations

2. **Dependency Analyzer**: Builds the function dependency graph
   - Identifies function definitions and calls
   - Resolves imports and module references
   - Tracks function call hierarchy

3. **Graph Builder**: Constructs a graph representation of function dependencies
   - Nodes represent functions
   - Edges represent function calls
   - Includes metadata (file location, function signatures, etc.)

4. **Output Formatter**: Converts the graph into various output formats
   - JSON for API responses
   - Visualization formats (DOT, GraphML, etc.)

## Usage

```python
from aiai.code_analyzer import CodeAnalyzer

# Initialize the analyzer with the appropriate language parser
analyzer = CodeAnalyzer(language="python")

# Analyze code starting from an entrypoint file
graph = analyzer.analyze_from_file("/path/to/entrypoint.py")

# Export the dependency graph
graph.export_json("/path/to/output.json")

# Visualize the graph
graph.visualize(format="dot", output_path="/path/to/visualization.dot")
```

## Adding New Language Support

The module is designed to be extensible, allowing new language parsers to be added easily:

1. Create a new parser class that implements the `LanguageParser` interface
2. Register the new parser with the main `CodeAnalyzer` class
3. Implement language-specific parsing logic using Tree-sitter

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
```

## Roadmap

- [x] Initial architecture design
- [ ] Python parser implementation
- [ ] Basic graph visualization
- [ ] JavaScript parser implementation
- [ ] Support for class methods and inheritance
- [ ] Cross-language dependencies
- [ ] Performance optimizations for large codebases