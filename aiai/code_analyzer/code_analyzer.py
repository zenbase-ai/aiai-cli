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
        recursive: bool = True,
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
                    logger.warning(f"Error extracting context from function {func.name}: {str(e)}")

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
                    if os.path.exists(imported_file) and imported_file not in self.visited_files:
                        logger.info(f"Recursively analyzing imported file: {imported_file}")
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
                        logger.debug(f"Found import: {imported_file} (not analyzing recursively)")

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
                logger.info(f"Added function to database: {func.name} in {func.file_path}")
            else:
                logger.info(f"Updated function in database: {func.name} in {func.file_path}")

        except Exception as e:
            logger.error(f"Error saving function {func.name} to database: {str(e)}")

    def find_data_files(self, base_directory: str) -> list[str]:
        """
        Find all JSON and YAML files in the repository that might contain relevant data.

        Args:
            base_directory: The root directory to start searching from

        Returns:
            A list of file paths to JSON and YAML files
        """
        import os

        logger.info(f"Finding data files in {base_directory}")

        data_files = []
        exclude_dirs = {
            ".git",
            ".github",
            ".vscode",
            "__pycache__",
            "venv",
            "env",
            "node_modules",
            "migrations",
            ".venv",
            ".env",
        }

        for root, dirs, files in os.walk(base_directory):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if file.endswith((".json", ".yaml", ".yml")):
                    # Skip files that are likely configuration files
                    if file.startswith(".") or file in {
                        "package.json",
                        "package-lock.json",
                        "poetry.lock",
                        "requirements.lock",
                        "pyproject.toml",
                    }:
                        continue

                    file_path = os.path.join(root, file)
                    data_files.append(file_path)
                    logger.debug(f"Found data file: {file_path}")

        logger.info(f"Found {len(data_files)} data files")
        return data_files

    def save_data_file_to_db(self, file_path: str) -> None:
        """
        Save data file information to the database.

        Args:
            file_path: Path to the data file
        """
        try:
            import os

            from aiai.app.models import DataFileInfo

            # Determine file type from extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == ".json":
                file_type = "json"
            elif file_ext in (".yaml", ".yml"):
                file_type = "yaml"
            else:
                logger.warning(f"Unsupported file type for {file_path}")
                return

            # Read file content
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                logger.warning(f"Could not read file {file_path}: {str(e)}")
                content = None

            # Create or update the data file record
            data_file, created = DataFileInfo.objects.update_or_create(
                file_path=file_path,
                defaults={
                    "file_type": file_type,
                    "content": content,
                    "last_analyzed": None,  # Will be updated when analyzed
                },
            )

            if created:
                logger.info(f"Added data file to database: {file_path}")
            else:
                logger.info(f"Updated data file in database: {file_path}")

            return data_file

        except Exception as e:
            logger.error(f"Error saving data file {file_path} to database: {str(e)}")
            return None

    def find_file_references_in_code(self, file_path: str) -> list[dict]:
        """
        Find references to a data file in all analyzed functions.

        Args:
            file_path: Path to the data file to find references for

        Returns:
            A list of dictionaries with function information and context
        """
        import os

        from aiai.app.models import FunctionInfo

        # Get the filename without extension to search for
        file_name = os.path.basename(file_path)
        file_name_no_ext = os.path.splitext(file_name)[0]

        # Get all functions from the database
        all_functions = FunctionInfo.objects.all()
        references = []

        for func in all_functions:
            # Check all potential places where the file might be referenced
            reference_found = False
            context = None

            # Check source code
            if func.source_code and (file_name in func.source_code or file_name_no_ext in func.source_code):
                reference_found = True

                # Find the line(s) where the reference occurs
                for i, line in enumerate(func.source_code.splitlines()):
                    if file_name in line or file_name_no_ext in line:
                        line_num = func.line_start + i
                        context = {
                            "type": "source_code",
                            "line": line_num,
                            "content": line.strip(),
                        }
                        break

            # Check string literals if available
            if not reference_found and func.string_literals:
                for literal in func.string_literals:
                    if isinstance(literal, dict) and "value" in literal:
                        if file_name in literal["value"] or file_name_no_ext in literal["value"]:
                            reference_found = True
                            context = {
                                "type": "string_literal",
                                "line": literal.get("line", 0),
                                "content": literal["value"],
                            }
                            break

            if reference_found:
                references.append({"function": func, "context": context})

        return references

    def analyze_data_file_references(self, data_files: list[str], save_to_db: bool = True) -> dict:
        """
        Analyze references to data files in the code.

        Args:
            data_files: List of data file paths to analyze
            save_to_db: Whether to save references to the database

        Returns:
            A dictionary mapping file paths to lists of referencing functions
        """

        file_references = {}

        for file_path in data_files:
            logger.info(f"Analyzing references to {file_path}")

            # Find references to this file in the code
            references = self.find_file_references_in_code(file_path)
            file_references[file_path] = references

            if save_to_db:
                try:
                    # Get or create the data file record
                    data_file = self.save_data_file_to_db(file_path)

                    if data_file:
                        # Clear existing references
                        data_file.referenced_by.clear()

                        # Store reference contexts
                        reference_contexts = []
                        for ref in references:
                            function = ref["function"]
                            context = ref["context"]

                            # Add function to the reference list
                            data_file.referenced_by.add(function)

                            # Add context to the list
                            if context:
                                reference_contexts.append(
                                    {
                                        "function_name": function.name,
                                        "function_path": function.file_path,
                                        "line": context.get("line", 0),
                                        "content": context.get("content", ""),
                                        "type": context.get("type", ""),
                                    }
                                )

                        # Update reference contexts
                        data_file.reference_contexts = reference_contexts
                        data_file.save()

                        logger.info(f"Saved {len(references)} references to {file_path}")
                except Exception as e:
                    logger.error(f"Error saving references for {file_path}: {str(e)}")

        return file_references

    def find_and_save_data_files(self, base_directory: str = None) -> dict:
        """
        Find all data files in the repository and save them to the database.

        Args:
            base_directory: The root directory to start searching from (defaults to current directory)

        Returns:
            A dictionary mapping file paths to lists of referencing functions
        """
        import os

        if base_directory is None:
            base_directory = os.getcwd()

        # Find all data files
        data_files = self.find_data_files(base_directory)

        # Analyze references to each file
        file_references = self.analyze_data_file_references(data_files, save_to_db=True)

        return file_references

    def analyze_project(self, entrypoint_file: str, save_to_db: bool = True) -> dict:
        """
        Comprehensive analysis of code and data files starting from an entrypoint file.

        This function:
        1. Analyzes the code starting from the entrypoint file
        2. Identifies all JSON and YAML files in the project directory
        3. Finds references to these data files in the analyzed code
        4. Saves all information to the database

        Args:
            entrypoint_file: Path to the entrypoint file to analyze
            save_to_db: Whether to save all information to the database

        Returns:
            A dictionary with analysis results containing:
            - 'code_graph': The dependency graph of functions
            - 'data_files': Mapping of data file paths to their references
        """
        import os

        if not os.path.exists(entrypoint_file):
            raise FileNotFoundError(f"Entrypoint file not found: {entrypoint_file}")

        logger.info(f"Starting comprehensive analysis from {entrypoint_file}")

        # Step 1: Analyze code
        code_graph = self.analyze_from_file(
            entrypoint_file=entrypoint_file,
            recursive=True,
            max_depth=5,
            save_to_db=save_to_db,
        )

        # Step 2: Find and analyze data files
        project_directory = os.path.dirname(os.path.abspath(entrypoint_file))
        data_file_references = self.find_and_save_data_files(project_directory)

        logger.info(f"Completed comprehensive analysis of {entrypoint_file}")
        logger.info(f"Found {len(code_graph.functions)} functions and {len(data_file_references)} data files")

        # Return combined results
        return {"code_graph": code_graph, "data_files": data_file_references}
