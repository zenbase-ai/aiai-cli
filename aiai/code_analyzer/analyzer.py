"""
CodeAnalyzer class implementation.

This is the main entry point for analyzing code and generating function dependency graphs.
"""

import logging
import os

from aiai.code_analyzer.graph import DependencyGraph
from aiai.code_analyzer.parsers import get_parser_for_language
from aiai.utils import setup_django

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
        setup_django()
        self.language = language
        self.parser = get_parser_for_language(language)
        if not self.parser:
            raise ValueError(f"Unsupported language: {language}")

        self.visited_files = set[str]()
        self.dependency_graph = DependencyGraph()

    def analyze_from_file(
        self,
        entrypoint_file: str,
        recursive: bool = False,
        max_depth: int = 3,
        save_to_db: bool = False,
    ) -> DependencyGraph:
        """
        Analyze code starting from an entrypoint file.

        Args:
            entrypoint_file: Path to the entrypoint file to analyze
            recursive: Whether to recursively analyze imported files
            max_depth: Maximum depth of recursion for imports (to prevent infinite loops)
            save_to_db: Whether to save function information to the database

        Returns:
            A dependency graph representing function calls
        """
        if not os.path.exists(entrypoint_file):
            raise FileNotFoundError(f"Entrypoint file not found: {entrypoint_file}")

        # Reset state for new analysis
        self.visited_files = set()
        self.dependency_graph = DependencyGraph()

        # Begin analysis from the entrypoint
        self._analyze_file(
            entrypoint_file,
            recursive=recursive,
            current_depth=0,
            max_depth=max_depth,
            save_to_db=save_to_db,
        )

        return self.dependency_graph

    def _analyze_file(
        self,
        file_path: str,
        recursive: bool = False,
        current_depth: int = 0,
        max_depth: int = 3,
        save_to_db: bool = False,
    ) -> None:
        """
        Analyze a single file and add its functions and dependencies to the graph.

        Args:
            file_path: Path to the file to analyze
            recursive: Whether to recursively analyze imported files
            current_depth: Current depth of recursion
            max_depth: Maximum depth of recursion
            save_to_db: Whether to save function information to the database
        """
        if file_path in self.visited_files:
            return

        if current_depth > max_depth:
            logger.warning(f"Maximum recursion depth reached for file: {file_path}")
            return

        self.visited_files.add(file_path)
        logger.info(f"Analyzing file: {file_path} (depth {current_depth})")

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

                    # Save function information to the database if requested
                    if save_to_db:
                        self.save_function_to_db(func)

                except Exception as e:
                    logger.warning(
                        f"Error extracting context from function {func.name}: {str(e)}"
                    )

            # Extract function calls and add edges to the graph
            function_calls = self.parser.identify_function_calls(parsed_data, functions)
            for caller, callee in function_calls:
                self.dependency_graph.add_dependency(caller, callee)

            # Process imports to find additional files to analyze
            imports = self.parser.extract_imports(parsed_data)

            # If recursive is enabled, analyze imported files
            if recursive and imports:
                logger.info(f"Found {len(imports)} imports in {file_path}")
                for imported_file in imports:
                    # Check if the imported file exists and has not been visited yet
                    if (
                        os.path.exists(imported_file)
                        and imported_file not in self.visited_files
                    ):
                        logger.info(
                            f"Recursively analyzing imported file: {imported_file}"
                        )
                        self._analyze_file(
                            imported_file,
                            recursive=recursive,
                            current_depth=current_depth + 1,
                            max_depth=max_depth,
                            save_to_db=save_to_db,
                        )
            # If not recursive, just add imported files to the graph for reference
            else:
                for imported_file in imports:
                    if os.path.exists(imported_file):
                        logger.debug(
                            f"Found import: {imported_file} (not analyzing recursively)"
                        )

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}")

    def save_function_to_db(self, func) -> None:
        """
        Save function information to the database.

        Args:
            func: The Function object to save
        """
        try:
            from aiai.app.models import FunctionInfo

            # Create or update the function information in the database
            _function_info, created = FunctionInfo.objects.update_or_create(
                file_path=func.file_path,
                name=func.name,
                line_start=func.line_start,
                defaults={
                    "line_end": func.line_end,
                    "signature": func.signature,
                    "source_code": func.source_code,
                    "docstring": func.docstring,
                    "comments": func.comments,
                    "string_literals": func.string_literals,
                    "variables": func.variables,
                    "constants": func.constants,
                },
            )

            if created:
                logger.info(
                    f"Added function to database: {func.name} in {func.file_path}"
                )
            else:
                logger.info(
                    f"Updated function in database: {func.name} in {func.file_path}"
                )

        except Exception as e:
            logger.error(f"Error saving function {func.name} to database: {str(e)}")
