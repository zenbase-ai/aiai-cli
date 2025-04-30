from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tree_sitter import Parser
from tree_sitter_languages import get_language

from . import register_parser
from .base import Function, LanguageParser

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------------------
# Tree-sitter language + queries
# --------------------------------------------------------------------------------------


# Function declarations (traditional, arrow, method) — capture blocks and names
FUNCTION_QUERY = r"""
(
  (function_declaration
      name: (identifier) @function.name
      parameters: (formal_parameters) @function.parameters
      body: (statement_block) @function.body
  ) @function.definition
)
(
  (export_statement
      (function_declaration
          name: (identifier) @function.name
          parameters: (formal_parameters) @function.parameters
          body: (statement_block) @function.body
      ) @function.definition
  )
)
(
  (lexical_declaration
     (variable_declarator
        name: (identifier) @function.name
        value: (arrow_function
                 parameters: (formal_parameters) @function.parameters
                 body: [(statement_block) (expression)] @function.body))
   ) @function.definition
)
(
  (lexical_declaration
     (variable_declarator
        name: (identifier) @function.name
        value: (function
                 parameters: (formal_parameters) @function.parameters
                 body: (statement_block) @function.body))
   ) @function.definition
)
(
  ((public_field_definition | private_field_definition | field_definition)
      name: (property_identifier) @function.name
      value: (arrow_function
                 parameters: (formal_parameters) @function.parameters
                 body: [(statement_block) (expression)] @function.body)
  ) @function.definition
)
(
  (method_definition
      property: (property_identifier) @function.name
      parameters: (formal_parameters) @function.parameters
      body: (statement_block) @function.body
  ) @function.definition
)
"""

# Function/Constructor calls
CALL_QUERY = r"""
(
  (call_expression
    function: [
        (identifier)            @function.call_name
        (member_expression
            object: (_)         @function.call_object
            property: (property_identifier) @function.call_method)
    ]
  ) @function.call
)
(
  (optional_chain
    (call_expression
      function: [
          (identifier) @function.call_name
          (member_expression
              object: (_) @function.call_object
              property: (property_identifier) @function.call_method)
      ]
    ) @function.call
  )
)
(
  (new_expression
      constructor: [
          (identifier) @function.call_name
          (member_expression
              object: (_) @function.call_object
              property: (property_identifier) @function.call_method)
      ]
  ) @function.call
)
"""

# ES module imports + dynamic imports and re-exports – capture source strings
IMPORT_QUERY = r"""
[
 (import_statement
    source: (string) @import.source
 )
 (export_statement
    source: (string) @import.source
 )
 (import_call
    (string) @import.source
 )
]
"""

# Additional queries for context extraction
STRING_QUERY = r"""
[(string) (template_string)] @string
"""

COMMENT_QUERY = r"""
(comment) @comment
"""

# Variable declarations inside functions
VARIABLE_QUERY = r"""
(
  (lexical_declaration
    (variable_declarator
       name: (identifier) @variable.name
       value: (_) @variable.value)
  ) @variable.decl
)
"""


# --------------------------------------------------------------------------------------
# Parser implementation
# --------------------------------------------------------------------------------------


@register_parser("typescript")
class TypeScriptParser(LanguageParser):
    """Parser implementation for TypeScript using Tree-sitter."""

    def __init__(self):
        super().__init__()

        self.language = get_language("typescript")
        self.parser = Parser(self.language)

        # Compile queries
        self.function_query = self.language.query(FUNCTION_QUERY)
        self.call_query = self.language.query(CALL_QUERY)
        self.import_query = self.language.query(IMPORT_QUERY)
        # Additional context queries
        self.string_query = self.language.query(STRING_QUERY)
        self.comment_query = self.language.query(COMMENT_QUERY)
        self.variable_query = self.language.query(VARIABLE_QUERY)

        # Track functions across all analyzed files for cross-module call resolution
        self._global_functions_map: Dict[str, List[Function]] = {}

    # --------------------------------------
    # Core parsing helpers
    # --------------------------------------

    def parse_file(self, file_path: str) -> Any:  # noqa: D401
        """Parse a TypeScript/TSX/JS file and return (tree, content, file_path)."""
        content = Path(file_path).read_bytes()
        tree = self.parser.parse(content)
        return tree, content, file_path

    # --------------------------------------
    # Function extraction
    # --------------------------------------

    def extract_functions(self, parsed_data: Any) -> List[Function]:  # noqa: D401
        tree, content, file_path = parsed_data

        captures = self.function_query.captures(tree.root_node)

        # Build dict like {capture_name: [nodes]}
        cap_map: Dict[str, List[Any]] = {}
        for node, cap_name in captures:
            cap_map.setdefault(cap_name, []).append(node)

        function_defs = cap_map.get("function.definition", [])
        function_names = cap_map.get("function.name", [])
        function_params = cap_map.get("function.parameters", [])

        functions: List[Function] = []
        for def_node in function_defs:
            # locate name / params within definition span
            name_node: Optional[Any] = next(
                (n for n in function_names if def_node.start_byte <= n.start_byte <= n.end_byte <= def_node.end_byte),
                None,
            )
            params_node: Optional[Any] = next(
                (n for n in function_params if def_node.start_byte <= n.start_byte <= n.end_byte <= def_node.end_byte),
                None,
            )

            # Handle anonymous default exports by synthesising a name
            if not name_node:
                func_name = "default"
            else:
                func_name = content[name_node.start_byte : name_node.end_byte].decode("utf-8")

            params_txt = content[params_node.start_byte : params_node.end_byte].decode("utf-8") if params_node else "()"
            signature = f"{func_name}{params_txt}"
            line_start = def_node.start_point[0] + 1
            line_end = def_node.end_point[0] + 1

            functions.append(
                Function(
                    name=func_name,
                    file_path=file_path,
                    line_start=line_start,
                    line_end=line_end,
                    signature=signature,
                )
            )

        # Update global map
        for f in functions:
            self._global_functions_map.setdefault(f.name, []).append(f)

        return functions

    # --------------------------------------
    # Function calls
    # --------------------------------------

    def identify_function_calls(
        self, parsed_data: Any, defined_functions: List[Function]
    ) -> List[Tuple[Function, Function]]:  # noqa: D401
        tree, content, _ = parsed_data

        # build quick lookup
        func_map: Dict[str, List[Function]] = {}
        for f in defined_functions:
            func_map.setdefault(f.name, []).append(f)

        # map of (start,end) -> func for containment checks
        func_ranges: Dict[Tuple[int, int], Function] = {(f.line_start, f.line_end): f for f in defined_functions}

        calls: List[Tuple[Function, Function]] = []

        for node, cap_name in self.call_query.captures(tree.root_node):
            if cap_name not in ("function.call_name", "function.call_method"):
                continue
            call_name = content[node.start_byte : node.end_byte].decode("utf-8")
            # find containing func
            caller = self._find_containing_function(node.start_point[0] + 1, func_ranges)
            # Prefer locally defined functions but fall back to global map for cross-file
            lookup_map = func_map if call_name in func_map else self._global_functions_map
            if caller and call_name in lookup_map:
                for callee in lookup_map[call_name]:
                    calls.append((caller, callee))

        return calls

    def _find_containing_function(
        self, line_number: int, function_ranges: Dict[Tuple[int, int], Function]
    ) -> Optional[Function]:
        containing = None
        smallest = float("inf")
        for (start, end), func in function_ranges.items():
            if start <= line_number <= end:
                rng = end - start
                if rng < smallest:
                    smallest = rng
                    containing = func
        return containing

    # --------------------------------------
    # Imports
    # --------------------------------------

    def extract_imports(self, parsed_data: Any) -> List[str]:  # noqa: D401
        tree, content, file_path = parsed_data
        cwd = Path(file_path).parent

        imported_files: List[str] = []
        for node, cap_name in self.import_query.captures(tree.root_node):
            if cap_name != "import.source":
                continue
            spec = content[node.start_byte : node.end_byte].decode("utf-8").strip("'\"")
            resolved = self._resolve_import_to_file_path(spec, cwd)
            if resolved:
                imported_files.append(resolved)
        return imported_files

    def _resolve_import_to_file_path(self, spec: str, cwd: Path) -> Optional[str]:
        """Resolve an ES import specifier to a concrete file on disk.

        Handles:
            • relative like './util' or '../foo/bar'
            • directory w/ index file
            • extensionless – tries .ts, .tsx, .js, .jsx, .cjs, .mjs, .cts, .mts, .d.ts, .json
        """
        if not spec:
            return None

        extensions = [
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
            ".cjs",
            ".mjs",
            ".cts",
            ".mts",
            ".d.ts",
            ".json",
        ]
        candidates: List[Path] = []

        # Support explicit extension as well as folder specs
        if spec.startswith("."):  # relative
            base = (cwd / spec).resolve()
        else:
            # For bare module names we can't resolve to disk here; skip
            return None

        if base.suffix:  # already has extension
            candidates.append(base)
        else:
            for ext in extensions:
                candidates.append(base.with_suffix(ext))
                candidates.append(base / f"index{ext}")

        for path in candidates:
            if path.exists() and path.is_file():
                return str(path)
        return None

    # --------------------------------------
    # Context extraction – minimal implementation
    # --------------------------------------

    def extract_function_context(self, parsed_data: Any, function: Function) -> None:  # noqa: D401
        """Populate basic context info for a function (source, doc comment, strings)."""
        try:
            tree, content, _file_path = parsed_data
            # Locate the function node by matching line numbers
            target_start = function.line_start - 1  # 0-indexed
            target_end = function.line_end - 1

            func_node = None
            for node, cap_name in self.function_query.captures(tree.root_node):
                if cap_name != "function.definition":
                    continue
                if node.start_point[0] == target_start:
                    func_node = node
                    break

            if not func_node:
                return

            function.source_code = content[func_node.start_byte : func_node.end_byte].decode("utf-8")

            # Look for leading /** */ comment (JSDoc) immediately preceding function
            prefix_bytes = content[: func_node.start_byte]
            last_newline = prefix_bytes.rfind(b"\n")
            if last_newline != -1:
                maybe_comment_end = prefix_bytes[last_newline + 1 :].strip()
                # If current line empty, look further up
                if (
                    maybe_comment_end.startswith(b"*/")
                    or maybe_comment_end.startswith(b"/**")
                    or maybe_comment_end.startswith(b"//")
                ):
                    # Grab up to 10 previous lines to build docstring
                    lines_back = prefix_bytes.splitlines()[-10:]
                    doc_lines = []
                    for l in reversed(lines_back):
                        text = l.decode("utf-8").strip()
                        if (
                            text.startswith("/**")
                            or text.startswith("/*")
                            or text.startswith("//")
                            or text.startswith("*")
                            or text.startswith("*/")
                        ):
                            doc_lines.append(text)
                            if text.startswith("/**"):
                                break
                        else:
                            break
                    if doc_lines:
                        doc_lines.reverse()
                        function.docstring = "\n".join([d.lstrip("/* ").rstrip("*/ ").strip() for d in doc_lines])

            # Extract string literals within function body
            for node, _ in self.string_query.captures(func_node):
                txt = content[node.start_byte : node.end_byte].decode("utf-8").strip("'\"")
                function.add_string_literal(txt, node.start_point[0] + 1)

            # Extract inline comments inside function
            for node, _ in self.comment_query.captures(func_node):
                txt = content[node.start_byte : node.end_byte].decode("utf-8")
                txt = txt.lstrip("/* ").rstrip("*/").lstrip("//").strip()
                function.add_comment(txt, node.start_point[0] + 1)

            # Extract variable and constant declarations
            for v_node, cap_name in self.variable_query.captures(func_node):
                if cap_name != "variable.decl":
                    continue
                # Determine if const or let/var by inspecting prefix text before name
                decl_text = content[v_node.start_byte : v_node.end_byte].decode("utf-8")
                # naive split
                is_const = decl_text.strip().startswith("const")

                # Find name/value child nodes captured earlier
                name_child = None
                value_child = None
                for child in v_node.children:
                    if child.type == "variable_declarator":
                        # children order name, =, value
                        for c2 in child.children:
                            if c2.type == "identifier" and name_child is None:
                                name_child = c2
                            elif name_child is not None and value_child is None and c2.type != "=":
                                value_child = c2
                if name_child:
                    var_name = content[name_child.start_byte : name_child.end_byte].decode("utf-8")
                    var_value = (
                        content[value_child.start_byte : value_child.end_byte].decode("utf-8") if value_child else None
                    )
                    if is_const or var_name.isupper():
                        function.add_constant(var_name, var_value or "", name_child.start_point[0] + 1)
                    else:
                        function.add_variable(var_name, var_value, name_child.start_point[0] + 1)

            # Consider string literals that appear to be file references
            for literal in function.string_literals:
                text = literal["text"] if "text" in literal else literal.get("value")
                if text and any(text.endswith(ext) for ext in (".json", ".yaml", ".yml", ".csv")):
                    function.add_file_reference(text, literal["line"])
        except Exception:
            # don't crash extraction on error
            logger.exception("Failed to extract context for %s", function.name)

    # -------------------------------------------------
    # Public helpers
    # -------------------------------------------------

    def clear_state(self):
        """Clear accumulated global state between analyses."""
        self._global_functions_map.clear()
