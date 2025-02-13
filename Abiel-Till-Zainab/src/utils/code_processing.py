import ast
import re
from textwrap import dedent
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

import black
import isort


class RouteTest(BaseModel):
    destination: Literal["fix_test_smell", "keep_good_test"]
    identified_smells: str


def extract_unit_tests(code: str) -> List[str]:
    """Extract individual test methods from a test class"""
    if not code.strip():
        return []

    try:
        # Parse the code into an AST
        tree = ast.parse(code)

        normalized_tests = []

        # Walk through all function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                # Get the source lines for this function
                start_line = node.lineno
                end_line = node.end_lineno

                # Extract the function source
                func_lines = code.split("\n")[start_line - 1 : end_line]
                func_source = "\n".join(func_lines)

                # Find the base indentation level of the function definition
                base_indent = len(func_lines[0]) - len(func_lines[0].lstrip())

                # Process each line to maintain relative indentation
                processed_lines = []
                for line in func_lines:
                    if not line.strip():  # Empty line
                        processed_lines.append("")
                        continue

                    # Calculate this line's indentation relative to the function definition
                    current_indent = len(line) - len(line.lstrip())
                    relative_indent = current_indent - base_indent

                    # Add the relative indentation
                    if relative_indent >= 0:
                        processed_lines.append(" " * relative_indent + line.lstrip())
                    else:
                        # Function definition line
                        processed_lines.append(line.lstrip())

                normalized_tests.append("\n".join(processed_lines))

        return normalized_tests

    except SyntaxError:
        # Fallback to empty list if code cannot be parsed
        return []


def sanitize_code_output(code: str) -> str:
    """Remove code block markers and leading/trailing whitespace"""
    # Remove ```python and ``` markers
    code = re.sub(r"^```python\s*\n", "", code)
    code = re.sub(r"\n```\s*$", "", code)
    return code.strip()


def validate_python_syntax(code: str) -> Optional[str]:
    """Validate Python code syntax"""
    try:
        compile(code, "<string>", "exec")
        return None
    except SyntaxError as e:
        return str(e)


def assemble_test_script(code_to_test_path: str, existing_tests: List[str], new_test: str) -> str:
    """
    Assemble test cases into a complete test script.

    Args:
        code_to_test_path: Path to the file containing code to test
        existing_tests: List of existing test case functions
        new_test: New test case function to add

    Returns:
        Complete test script as a string
    """
    # Extract the module name from the path
    module_name = code_to_test_path.split("/")[-1].replace(".py", "")

    # Create the test script template
    script = [
        "import unittest",
        "from typing import *",
        f"from {module_name} import *",
        "",
        "class GeneratedTestCases(unittest.TestCase):",
    ]

    # Add existing test cases with proper indentation
    for test in existing_tests:
        # Split into lines and properly indent each line
        test_lines = test.split("\n")
        indented_lines = []
        for line in test_lines:
            # Skip empty lines
            if not line.strip():
                indented_lines.append("")
                continue
            # Determine the original indentation level
            original_indent = len(line) - len(line.lstrip())
            # Add base class indentation (4 spaces) plus original indentation
            indented_lines.append("    " + " " * original_indent + line.lstrip())
        script.append("\n".join(indented_lines))
        script.append("")

    # Add the new test case
    if new_test:
        new_test_lines = new_test.split("\n")
        indented_lines = []
        for line in new_test_lines:
            if not line.strip():
                indented_lines.append("")
                continue
            original_indent = len(line) - len(line.lstrip())
            indented_lines.append("    " + " " * original_indent + line.lstrip())
        script.append("\n".join(indented_lines))

    # Add main block with proper indentation
    script.extend(
        [
            "",  # Add blank line before main block
            "if __name__ == '__main__':",
            "    unittest.main()",
        ]
    )

    assembled_script = "\n".join(script)

    try:
        # Apply isort formatting
        isort_config = isort.Config(profile="black")
        assembled_script = isort.code(assembled_script, config=isort_config)

        # Apply black formatting
        assembled_script = black.format_str(assembled_script, mode=black.FileMode())

        return assembled_script
    except Exception as e:
        # If formatting fails, return the unformatted script
        return assembled_script


if __name__ == "__main__":
    code = """
import unittest
from typing import *
from code_to_test import *

class GeneratedTestCases(unittest.TestCase):
    def test_add_two_positive_integers(self):
        \"\"\"Test adding two positive integers.\"\"\"
        result = add(3, 5)
        self.assertEqual(result, 8, "Expected 3 + 5 to equal 8")

    def test_add_edge_case_zero_and_negative_integer(self):
        \"\"\"Test adding zero to a negative integer.\"\"\"
        result = add(0, -5)
        self.assertEqual(result, -5, "Expected 0 + -5 to equal -5")

if __name__ == "__main__":
    unittest.main()
    """
    for test_case in extract_unit_tests(code):
        print(test_case)
