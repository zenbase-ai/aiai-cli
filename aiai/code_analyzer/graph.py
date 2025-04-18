"""
Dependency graph implementation.

This module provides a graph structure to represent function dependencies.
"""

import json
import os
from typing import Any, Dict, List, Optional, Set

import networkx as nx

from .parsers.base import Function


class DependencyGraph:
    """
    A graph representation of function dependencies.

    Nodes represent functions and edges represent function calls.
    """

    def __init__(self):
        """Initialize an empty dependency graph."""
        self.functions: Dict[str, Function] = {}  # Maps function ID to Function object
        self.dependencies: Dict[str, Set[str]] = {}  # Maps caller ID to set of callee IDs

    def get_function_id(self, func: Function) -> str:
        """
        Generate a unique ID for a function.

        Args:
            func: The Function object

        Returns:
            A string identifier unique to this function
        """
        return f"{func.file_path}:{func.name}:{func.line_start}"

    def add_function(self, func: Function) -> None:
        """
        Add a function to the graph.

        Args:
            func: The Function object to add
        """
        func_id = self.get_function_id(func)
        self.functions[func_id] = func
        if func_id not in self.dependencies:
            self.dependencies[func_id] = set()

    def add_dependency(self, caller: Function, callee: Function) -> None:
        """
        Add a dependency edge from caller to callee.

        Args:
            caller: The calling function
            callee: The function being called
        """
        caller_id = self.get_function_id(caller)
        callee_id = self.get_function_id(callee)

        # Ensure both functions are in the graph
        if caller_id not in self.functions:
            self.add_function(caller)
        if callee_id not in self.functions:
            self.add_function(callee)

        # Add the dependency
        if caller_id not in self.dependencies:
            self.dependencies[caller_id] = set()
        self.dependencies[caller_id].add(callee_id)

    def get_callers(self, func: Function) -> List[Function]:
        """
        Get all functions that call the given function.

        Args:
            func: The Function object

        Returns:
            A list of Function objects that call the given function
        """
        func_id = self.get_function_id(func)
        callers = []
        for caller_id, callees in self.dependencies.items():
            if func_id in callees:
                callers.append(self.functions[caller_id])
        return callers

    def get_callees(self, func: Function) -> List[Function]:
        """
        Get all functions called by the given function.

        Args:
            func: The Function object

        Returns:
            A list of Function objects called by the given function
        """
        func_id = self.get_function_id(func)
        if func_id not in self.dependencies:
            return []

        return [self.functions[callee_id] for callee_id in self.dependencies[func_id]]

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the graph to a dictionary representation.

        Returns:
            A dictionary representing the graph
        """
        nodes = []
        for func_id, func in self.functions.items():
            nodes.append(
                {
                    "id": func_id,
                    "name": func.name,
                    "file": func.file_path,
                    "line_start": func.line_start,
                    "line_end": func.line_end,
                    "signature": func.signature,
                    "metadata": func.metadata,
                }
            )

        edges = []
        for caller_id, callees in self.dependencies.items():
            for callee_id in callees:
                edges.append({"source": caller_id, "target": callee_id})

        return {"nodes": nodes, "edges": edges}

    def export_json(self, output_path: str) -> None:
        """
        Export the dependency graph to a JSON file.

        Args:
            output_path: Path to the output JSON file
        """
        graph_dict = self.to_dict()

        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(graph_dict, f, indent=2)

    def to_networkx(self) -> nx.DiGraph:
        """
        Convert the dependency graph to a NetworkX DiGraph.

        Returns:
            A NetworkX DiGraph representing the function dependencies
        """
        G = nx.DiGraph()

        # Add nodes
        for func_id, func in self.functions.items():
            G.add_node(
                func_id,
                function_name=func.name,
                file=func.file_path,
                line_start=func.line_start,
                line_end=func.line_end,
                signature=func.signature,
                metadata=func.metadata,
            )

        # Add edges
        for caller_id, callees in self.dependencies.items():
            for callee_id in callees:
                G.add_edge(caller_id, callee_id)

        return G

    def visualize(self, format: str = "markdown", output_path: Optional[str] = None) -> Optional[str]:
        """
        Generate a visualization of the function dependency graph.

        Args:
            format: The output format (json, dot, markdown)
            output_path: Path to save the visualization (optional)

        Returns:
            The path to the generated file, or None if output_path is None
        """
        if format == "dot":
            return self._generate_dot_visualization(output_path)
        elif format == "markdown":
            return self._generate_markdown_visualization(output_path)
        elif format == "json":
            return self._generate_json_visualization(output_path)
        else:
            raise ValueError(f"Unsupported visualization format: {format}")

    def _generate_markdown_visualization(self, output_path: Optional[str] = None) -> Optional[str]:
        """
        Generate an LLM-friendly Markdown representation of the function dependency graph.

        Args:
            output_path: Path to save the Markdown file (optional)

        Returns:
            The path to the generated file, or the Markdown content if output_path is None
        """
        # Create a map from function ID to function object for easy lookup
        {self.get_function_id(func): func for func_id, func in self.functions.items()}

        # Start building the Markdown content
        markdown_content = "# Function Dependency Graph\n\n"

        # Add a summary section
        markdown_content += "## Summary\n\n"
        markdown_content += f"- Total functions: {len(self.functions)}\n"

        # Count root functions (those that aren't called by others)
        called_functions = set()
        for caller_id, callees in self.dependencies.items():
            for callee_id in callees:
                called_functions.add(callee_id)

        root_functions = [func for func_id, func in self.functions.items() if func_id not in called_functions]

        markdown_content += f"- Entry point functions: {len(root_functions)}\n"
        if root_functions:
            markdown_content += "  - " + ", ".join(func.name for func in root_functions) + "\n"

        # Count leaf functions (those that don't call others)
        leaf_functions = [
            func
            for func_id, func in self.functions.items()
            if func_id not in self.dependencies or not self.dependencies[func_id]
        ]

        markdown_content += f"- Leaf functions: {len(leaf_functions)}\n"
        if leaf_functions:
            markdown_content += "  - " + ", ".join(func.name for func in leaf_functions) + "\n"

        markdown_content += "\n## Function Details\n\n"

        # Add details for each function
        for func_id, func in sorted(self.functions.items(), key=lambda x: x[1].name):
            markdown_content += f"### `{func.name}`\n\n"
            markdown_content += f"- **Location**: {func.file_path}:{func.line_start}-{func.line_end}\n"
            markdown_content += f"- **Signature**: `{func.signature}`\n\n"

            # Add docstring if available
            if func.docstring:
                markdown_content += "**Docstring**:\n```\n" + func.docstring + "\n```\n\n"

            # List functions that this function calls
            callees = self.get_callees(func)
            if callees:
                markdown_content += "**Calls**:\n"
                for callee in callees:
                    markdown_content += f"- `{callee.name}`\n"
                markdown_content += "\n"
            else:
                markdown_content += "**Calls**: *No functions*\n\n"

            # List functions that call this function
            callers = self.get_callers(func)
            if callers:
                markdown_content += "**Called by**:\n"
                for caller in callers:
                    markdown_content += f"- `{caller.name}`\n"
                markdown_content += "\n"
            else:
                markdown_content += "**Called by**: *No functions*\n\n"

            # Add comments
            if func.comments:
                markdown_content += "**Comments**:\n"
                for comment in func.comments:
                    markdown_content += f"- Line {comment['line']}: `{comment['text']}`\n"
                markdown_content += "\n"

            # Add string literals (potential prompts)
            if func.string_literals:
                markdown_content += "**String Literals**:\n"
                for string in func.string_literals:
                    # Only show string literals that might be prompts (minimum length and not just simple words)
                    if len(string["text"]) > 20 or "\n" in string["text"]:
                        markdown_content += f"- Line {string['line']}: ```\n{string['text']}\n```\n"
                markdown_content += "\n"

            # Add variable assignments
            if func.variables:
                markdown_content += "**Variables**:\n"
                for var in func.variables:
                    if var["value"]:
                        markdown_content += f"- Line {var['line']}: `{var['name']}` = `{var['value']}`\n"
                    else:
                        markdown_content += f"- Line {var['line']}: `{var['name']}`\n"
                markdown_content += "\n"

            # Add constants
            if func.constants:
                markdown_content += "**Constants**:\n"
                for const in func.constants:
                    markdown_content += f"- Line {const['line']}: `{const['name']}` = `{const['value']}`\n"
                markdown_content += "\n"

            # Add file references
            if func.file_references:
                markdown_content += "**File References**:\n"
                for file_ref in func.file_references:
                    markdown_content += f"- Line {file_ref['line']}: `{file_ref['path']}`\n"
                markdown_content += "\n"

            # Add full source code
            if func.source_code:
                markdown_content += "**Source Code**:\n```python\n" + func.source_code + "\n```\n\n"

        # Add a Mermaid graph for visual representation
        markdown_content += "\n## Visualization\n\n"
        markdown_content += "```mermaid\nflowchart TD\n"

        # Add nodes with labels
        for func_id, func in self.functions.items():
            safe_id = func_id.replace(":", "_").replace("/", "_").replace(".", "_")
            markdown_content += f'    {safe_id}["{func.name}"]\n'

        # Add edges
        for caller_id, callees in self.dependencies.items():
            safe_caller_id = caller_id.replace(":", "_").replace("/", "_").replace(".", "_")
            for callee_id in callees:
                safe_callee_id = callee_id.replace(":", "_").replace("/", "_").replace(".", "_")
                markdown_content += f"    {safe_caller_id} --> {safe_callee_id}\n"

        markdown_content += "```\n"

        # Write to file or return the content
        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "w") as f:
                f.write(markdown_content)
            return output_path
        else:
            return markdown_content

    def _generate_dot_visualization(self, output_path: Optional[str] = None) -> Optional[str]:
        """
        Generate a DOT visualization of the function dependency graph.

        Args:
            output_path: Path to save the DOT file (optional)

        Returns:
            The path to the generated file, or the DOT string if output_path is None
        """
        G = self.to_networkx()

        # Use NetworkX to write the DOT file
        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            nx.drawing.nx_pydot.write_dot(G, output_path)
            return output_path
        else:
            import io

            buffer = io.StringIO()
            nx.drawing.nx_pydot.write_dot(G, buffer)
            return buffer.getvalue()

    def _generate_json_visualization(self, output_path: Optional[str] = None) -> Optional[str]:
        """
        Generate a JSON representation of the function dependency graph.

        Args:
            output_path: Path to save the JSON file (optional)

        Returns:
            The path to the generated file, or the JSON string if output_path is None
        """
        import json

        # Create a dictionary to store the graph data
        graph_data = {"functions": [], "dependencies": []}

        # Add function data
        for func_id, func in self.functions.items():
            function_data = {
                "id": func_id,
                "name": func.name,
                "file_path": func.file_path,
                "line_start": func.line_start,
                "line_end": func.line_end,
                "signature": func.signature,
                "source_code": func.source_code,
                "docstring": func.docstring,
                "comments": func.comments,
                "string_literals": func.string_literals,
                "variables": func.variables,
                "constants": func.constants,
                "file_references": func.file_references,
            }

            graph_data["functions"].append(function_data)

        # Add dependency data
        for caller_id, callees in self.dependencies.items():
            for callee_id in callees:
                dependency_data = {"caller": caller_id, "callee": callee_id}

                graph_data["dependencies"].append(dependency_data)

        # Convert the graph data to JSON
        json_data = json.dumps(graph_data, indent=2)

        # Write to file or return the JSON string
        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "w") as f:
                f.write(json_data)
            return output_path
        else:
            return json_data
