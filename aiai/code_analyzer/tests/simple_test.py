"""
Simple test to understand how the tree-sitter-python library works.
"""

import tree_sitter_python
from tree_sitter import Language, Parser

# Create a parser
parser = Parser()

# Get the Python language from tree-sitter-python
# We need to wrap the PyCapsule with the Language class
PY_LANGUAGE = Language(tree_sitter_python.language())
print("Python language type:", type(PY_LANGUAGE))

# Set the language for the parser
parser.language = PY_LANGUAGE

# Try to parse a simple Python code
code = b"def hello(): print('Hello, world!')"
tree = parser.parse(code)
print("Tree root type:", tree.root_node.type)

# Try a simple query
query = PY_LANGUAGE.query("""
(function_definition
  name: (identifier) @function.name)
""")

# Print all captures
captures = query.captures(tree.root_node)
print("Captures type:", type(captures))
print("Captures:", captures)

# Iterate through captures correctly
for capture in captures:
    print(f"Capture: {capture}")
    # Handle capture based on its structure
    if isinstance(capture, tuple) and len(capture) == 2:
        node, capture_name = capture
        print(f"  Node type: {node.type}, Capture name: {capture_name}")
        print(f"  Text: {code[node.start_byte : node.end_byte].decode('utf8')}")
