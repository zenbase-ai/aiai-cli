"""
CodeAnalyzer class implementation.

This is the main entry point for analyzing code and generating function dependency graphs.
"""

from typing import Dict, List, Optional, Set, Union
import os
import logging

from .parsers import get_parser_for_language
from .graph import DependencyGraph

logger = logging.getLogger(__name__)

class CodeAnalyzer:
    """
    A service that analyzes source code files to generate a dependency graph
    of functions and their relationships.
    """
    
    def __init__(self, language: str = "python"):
        """
        Initialize the code analyzer with a specific language parser.
        
        Args:
            language: The programming language to analyze (default: "python")
        """
        self.language = language
        self.parser = get_parser_for_language(language)
        if not self.parser:
            raise ValueError(f"Unsupported language: {language}")
        
        self.visited_files: Set[str] = set()
        self.dependency_graph = DependencyGraph()
    
    def analyze_from_file(self, entrypoint_file: str) -> DependencyGraph:
        """
        Analyze code starting from an entrypoint file.
        
        Args:
            entrypoint_file: Path to the entrypoint file to analyze
            
        Returns:
            A dependency graph representing function calls
        """
        if not os.path.exists(entrypoint_file):
            raise FileNotFoundError(f"Entrypoint file not found: {entrypoint_file}")
        
        # Reset state for new analysis
        self.visited_files = set()
        self.dependency_graph = DependencyGraph()
        
        # Begin analysis from the entrypoint
        self._analyze_file(entrypoint_file)
        
        return self.dependency_graph
    
    def _analyze_file(self, file_path: str) -> None:
        """
        Analyze a single file and add its functions and dependencies to the graph.
        
        Args:
            file_path: Path to the file to analyze
        """
        if file_path in self.visited_files:
            return
        
        self.visited_files.add(file_path)
        
        try:
            # Parse the file
            parsed_data = self.parser.parse_file(file_path)
            
            # Extract functions and add them to the graph
            functions = self.parser.extract_functions(parsed_data)
            for func in functions:
                self.dependency_graph.add_function(func)
                
                # Extract rich contextual information from the function
                try:
                    self.parser.extract_function_context(parsed_data, func)
                except Exception as e:
                    logger.warning(f"Error extracting context from function {func.name}: {str(e)}")
            
            # Extract function calls and add edges to the graph
            function_calls = self.parser.identify_function_calls(parsed_data, functions)
            for caller, callee in function_calls:
                self.dependency_graph.add_dependency(caller, callee)
            
            # Process imports to find additional files to analyze
            imports = self.parser.extract_imports(parsed_data)
            for imported_file in imports:
                if os.path.exists(imported_file) and imported_file not in self.visited_files:
                    self._analyze_file(imported_file)
                    
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}")
