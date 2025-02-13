import importlib.util
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Tuple

import coverage
import pandas as pd


class CoverageMatrix:
    def __init__(self, code_path: str, test_cases: List[str]):
        self.code_path = code_path
        self.test_cases = test_cases
        # Remove the coverage instance from __init__ as we'll create fresh ones for each test
        self._matrix = []
        self._line_numbers = []
        self._total_lines = []
        self._missed_lines = []
        self._unexecuted_lines = []

    def _get_code_lines(self) -> Tuple[List[int], int, List[str]]:
        """Get line numbers and content from the code file"""
        with open(self.code_path, "r") as file:
            lines = file.readlines()
            total_lines = [line.strip() for line in lines]
            # Only include non-empty, non-comment lines
            code_lines = []
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    code_lines.append(i)
        return code_lines, len(lines), total_lines

    def analyze(self) -> Dict[str, Any]:
        """Analyze code coverage and generate coverage matrix"""
        self._line_numbers, total_line_count, self._total_lines = self._get_code_lines()

        # Initialize storage
        self._missed_lines = []
        self._unexecuted_lines = []
        self._matrix = []

        # Get the directory containing the test file
        test_dir = os.path.dirname(os.path.abspath(self.code_path))

        # Create a temporary directory for coverage files and test execution
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy the code to test into the temporary directory
            code_to_test_path = os.path.join(temp_dir, "code_to_test.py")
            with open(self.code_path, "r") as src, open(code_to_test_path, "w") as dst:
                dst.write(src.read())

            # Add temp directory to Python path
            if temp_dir not in sys.path:
                sys.path.insert(0, temp_dir)

            try:
                for test_case in self.test_cases:
                    # Create a new coverage instance for each test
                    coverage_file = os.path.join(temp_dir, f'coverage_{test_case.replace(".", "_")}.coverage')
                    test_cov = coverage.Coverage(
                        branch=True,
                        source=[temp_dir],  # Updated source path
                        data_file=coverage_file,
                        omit=["*/site-packages/*", "*/dist-packages/*"],
                    )

                    try:
                        # Start fresh coverage collection
                        test_cov.start()

                        # Create a test suite for this specific test method
                        suite = unittest.TestSuite()
                        method_name = test_case.split(".")[-1]

                        # Import the module fresh each time
                        if "combined_test_script" in sys.modules:
                            del sys.modules["combined_test_script"]
                        if "code_to_test" in sys.modules:
                            del sys.modules["code_to_test"]

                        # Copy the test script to the temp directory
                        test_script_path = os.path.join(temp_dir, "combined_test_script.py")
                        with open(os.path.join(test_dir, "combined_test_script.py"), "r") as src, open(
                            test_script_path, "w"
                        ) as dst:
                            dst.write(src.read())

                        spec = importlib.util.spec_from_file_location("combined_test_script", test_script_path)
                        module = importlib.util.module_from_spec(spec)
                        sys.modules["combined_test_script"] = module
                        spec.loader.exec_module(module)

                        # Find and add the test to the suite
                        test_class = None
                        for item in dir(module):
                            obj = getattr(module, item)
                            if isinstance(obj, type) and issubclass(obj, unittest.TestCase):
                                test_class = obj
                                break

                        if test_class:
                            test_instance = test_class(method_name)
                            suite.addTest(test_instance)

                            # Run the test
                            runner = unittest.TextTestRunner(stream=io.StringIO())
                            runner.run(suite)

                            # Stop coverage and save
                            test_cov.stop()
                            test_cov.save()

                            # Analyze coverage
                            analysis = test_cov.analysis(code_to_test_path)  # Updated path
                            _, _, missing_lines, _ = analysis
                            self._missed_lines.append(missing_lines)

                            # Get unexecuted lines for this test
                            for line_num in missing_lines:
                                if 0 <= line_num - 1 < len(self._total_lines):
                                    self._unexecuted_lines.append(
                                        {
                                            "test": test_case,
                                            "line": self._total_lines[line_num - 1].strip(),
                                            "line_number": line_num,
                                        }
                                    )

                    except Exception as e:
                        print(f"Error running test {test_case}: {str(e)}")
                        self._missed_lines.append([])  # Add empty missing lines for failed test
                    finally:
                        test_cov.stop()
                        test_cov.erase()
                        del test_cov

            finally:
                # Clean up sys.path
                if temp_dir in sys.path:
                    sys.path.remove(temp_dir)

            # Create coverage matrix (1 = executed, 0 = not executed)
            for line in self._line_numbers:
                row = [0 if line in missed_lines else 1 for missed_lines in self._missed_lines]
                self._matrix.append(row)

            # Calculate coverage metrics
            row_sums = [sum(row) for row in self._matrix]
            col_sums = [sum(col) for col in zip(*self._matrix)]

            # Reset unexecuted lines and only collect lines that aren't covered by any test
            self._unexecuted_lines = []
            for i, row_sum in enumerate(row_sums):
                if row_sum == 0:  # Line not covered by any test
                    line_num = self._line_numbers[i]
                    if 0 <= line_num - 1 < len(self._total_lines):
                        self._unexecuted_lines.append(
                            {
                                "line": self._total_lines[line_num - 1].strip(),
                                "line_number": line_num,
                            }
                        )

            # Calculate line coverage
            covered_lines = sum(1 for row_sum in row_sums if row_sum > 0)
            total_lines = len(self._matrix)
            line_coverage = covered_lines / total_lines if total_lines > 0 else 0

            return {
                "matrix": self._matrix,
                "line_numbers": self._line_numbers,
                "row_sums": row_sums,
                "col_sums": col_sums,
                "unexecuted_lines": self._unexecuted_lines,
                "total_lines": self._total_lines,
                "line_coverage": line_coverage,
            }

    def _get_line_context(self, line_num: int, context_lines: int = 2) -> List[str]:
        """Get context lines around a specific line number"""
        start = max(0, line_num - context_lines - 1)
        end = min(len(self._total_lines), line_num + context_lines)
        return self._total_lines[start:end]

    def format_matrix(self, analysis_results: Dict[str, Any]) -> pd.DataFrame:
        """Format the coverage matrix as a pandas DataFrame"""
        # Create column names for tests
        test_cols = [f"Test{i+1}" for i in range(len(self._missed_lines))]

        # Create the DataFrame with line numbers as index
        df = pd.DataFrame(
            analysis_results["matrix"],
            columns=test_cols,
            index=analysis_results["line_numbers"],
        )
        
        # Add code lines content and highlight
        df["Code"] = [line.strip() for line in analysis_results["total_lines"] if line.strip() and not line.strip().startswith('#')] 
        df["Coverage"] = analysis_results["row_sums"]

        # Reorder columns to put Code first
        cols = ["Code"] + test_cols + ["Coverage"]
        df = df[cols]

        # Add column sums as a new row - Fix the placement of empty string
        col_sums_row = [0] + analysis_results["col_sums"] + [sum(analysis_results["row_sums"])]
        df.loc["Col Sum"] = col_sums_row

        return df


def analyze_test_coverage(
    code_path: str, test_module: str, test_cases: List[str]
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Analyze test coverage and return formatted matrix and raw results

    Args:
        code_path: Path to the code file being tested
        test_module: Full module path of the test file
        test_cases: List of test case names to analyze

    Returns:
        Tuple of (formatted matrix string, raw analysis results)
    """
    coverage_matrix = CoverageMatrix(code_path, [f"{test_module}.{tc}" for tc in test_cases])
    results = coverage_matrix.analyze()
    formatted_matrix = coverage_matrix.format_matrix(results)
    return formatted_matrix, results
