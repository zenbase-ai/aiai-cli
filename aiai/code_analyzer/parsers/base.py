"""
Base interface for language parsers.

This module defines the abstract base class that all language-specific parsers must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple


class Function:
    """Represents a function definition in the code."""

    def __init__(
        self,
        name: str,
        file_path: str,
        line_start: int,
        line_end: int,
        signature: str = "",
    ):
        self.name = name
        self.file_path = file_path
        self.line_start = line_start
        self.line_end = line_end
        self.signature = signature
        self.metadata = {}

        # Enhanced context information
        self.source_code = ""  # Full source code of the function
        self.docstring = ""  # Function docstring if available
        self.comments = []  # List of comments inside the function
        self.string_literals = []  # List of string literals in the function
        self.file_references = []  # List of potential file references
        self.variables = []  # List of variables defined in the function
        self.constants = []  # List of constants used in the function

    def __repr__(self):
        return f"Function({self.name}, {self.file_path}:{self.line_start}-{self.line_end})"

    def __eq__(self, other):
        if not isinstance(other, Function):
            return False
        return self.name == other.name and self.file_path == other.file_path and self.line_start == other.line_start

    def __hash__(self):
        return hash((self.name, self.file_path, self.line_start))

    def add_string_literal(self, text: str, line: int):
        """Add a string literal found in the function."""
        self.string_literals.append({"text": text, "line": line})

    def add_comment(self, text: str, line: int):
        """Add a comment found in the function."""
        self.comments.append({"text": text, "line": line})

    def add_file_reference(self, path: str, line: int):
        """Add a potential file reference found in the function."""
        self.file_references.append({"path": path, "line": line})

    def add_variable(self, name: str, value: Optional[str] = None, line: int = 0):
        """Add a variable defined in the function."""
        self.variables.append({"name": name, "value": value, "line": line})

    def add_constant(self, name: str, value: str, line: int):
        """Add a constant used in the function."""
        self.constants.append({"name": name, "value": value, "line": line})


class LanguageParser(ABC):
    """
    Abstract base class for language-specific parsers.

    Each language implementation must provide methods for:
    - Parsing a file into an AST
    - Extracting functions from the AST
    - Identifying function calls
    - Resolving imports
    """

    @abstractmethod
    def parse_file(self, file_path: str) -> Any:
        """
        Parse a file and return its abstract syntax tree or equivalent structure.

        Args:
            file_path: Path to the file to parse

        Returns:
            The parsed representation of the file (AST or equivalent)
        """
        pass

    @abstractmethod
    def extract_functions(self, parsed_data: Any) -> List[Function]:
        """
        Extract function definitions from the parsed data.

        Args:
            parsed_data: The parsed representation of a file

        Returns:
            A list of Function objects representing the functions defined in the file
        """
        pass

    @abstractmethod
    def identify_function_calls(
        self, parsed_data: Any, defined_functions: List[Function]
    ) -> List[Tuple[Function, Function]]:
        """
        Identify function calls within the parsed data.

        Args:
            parsed_data: The parsed representation of a file
            defined_functions: List of defined functions to match against

        Returns:
            A list of (caller, callee) tuples representing function calls
        """
        pass

    @abstractmethod
    def extract_imports(self, parsed_data: Any) -> List[str]:
        """
        Extract imported modules or files from the parsed data.

        Args:
            parsed_data: The parsed representation of a file

        Returns:
            A list of file paths that are imported by the current file
        """
        pass

    def extract_function_context(self, parsed_data: Any, function: Function) -> None:
        """
        Extract rich contextual information from a function.

        Args:
            parsed_data: The parsed representation of a file
            function: The Function object to enrich with context

        Note:
            This method should be implemented by language-specific parsers
            to extract comments, string literals, file references, variables, and constants.
            If not implemented by a subclass, it will do nothing.
        """
        # Default implementation does nothing
        pass
