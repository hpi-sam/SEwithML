fix_similarities_prompt = """You are an expert at finding untested code behaviour given a set of unit tests and rewriting a highlighted unit test to cover the untested behaviour.

COVERAGE PRIORITIES:
1. Focus on uncovered lines first
   - If the test covers previously uncovered lines, DO NOT modify it even if behavior seems similar
   - Tests covering new lines are valuable regardless of similarity to other tests
2. Only consider rewriting if:
   - The test covers only already-covered lines AND
   - The test behavior is too similar to existing tests

SIMILARITY ANALYSIS:
1. Consider tests similar if they:
   - Test the same function with similar inputs
   - Have the same assertions checking the same conditions
   - Cover the same lines of code
   - Test the same edge cases or scenarios
2. Tests are NOT similar if they:
   - Cover different lines of code
   - Test different edge cases or error conditions
   - Verify different aspects of the same function
   - Use significantly different input values or combinations

ANALYSIS PROTOCOL:
1. Check if the new test covers any uncovered lines from the coverage matrix
2. If it covers uncovered lines: Return the test unchanged
3. If it only covers already-covered lines:
   a) Compare behavior with existing tests using similarity criteria above
   b) If too similar: Rewrite to test a new edge case or scenario while maintaining good coverage
   c) If testing unique behavior: Return unchanged
4. When rewriting:
   - Look for untested edge cases
   - Consider boundary conditions
   - Test error scenarios
   - Use different combinations of inputs
   - Maintain or improve code coverage

The code to test:
```python
{code_to_test}
```

Coverage Information:
Uncovered lines:
{uncovered_lines}

Coverage matrix:
{coverage_matrix}

The existing unit tests:
{existing_unit_tests}

The new unit test that you potentially have to rewrite:
```python
{new_unit_test}
```

Format specification:
You can assume that the produced test code is already given as a single file with a single test class `GeneratedTestCases` and that the test case function will be added to this class.
If you need any additional imports, add them within your test case function (we use isort later to sort imports).
Also, assume that the code to test is already imported and available in the test case:
```python
import unittest
from typing import *
from code_to_test import *

class GeneratedTestCases(unittest.TestCase):
    def test_add_two_positive_integers(self):
        \"\"\"Test adding two positive integers.\"\"\"
        result = add(3, 5)
        self.assertEqual(result, 8, "Expected 3 + 5 to equal 8")
    
    # ... (more test case functions here)

if __name__ == '__main__':
    unittest.main()
```

Reminder: Your task is only to write the test case function, not the entire test script.
Keep test documentation concise and focused on what is being tested. Include only essential test-related comments (e.g., assertion messages, comments on the test setup).

Here's a good output example that satisfies our test case format:
```python
def test_add_two_positive_integers(self):
    \"\"\"Test adding two positive integers with boundary conditions.\"\"\"
    first_number = 2147483647  # Max 32-bit integer
    second_number = 42
    expected_sum = 2147483689
    
    result = add(first_number, second_number)
    
    self.assertEqual(result, expected_sum, 
        f"Expected {{first_number}} + {{second_number}} to equal {{expected_sum}}")
    self.assertIsInstance(result, int, "Result should be an integer")
```

Here's a bad output example that is too verbose (it should not add comments how it rewrites the test):
```python
def test_switch_function_case_1(self):
    \"\"\"Test the behavior of switch_function_0 when input is 1.\"\"\"
    # The original test checks the case for input 1, which is already covered. (<-- do not add this comment)
    # We will rewrite this test to check an edge case for input 0, which is not covered. (<-- do not add this comment)
    input_value = 0
    result = switch_function_0(input_value)
    expected_result = 0 + 0  # result should be 0
    self.assertEqual(result, expected_result, 
        f"Expected switch_function_0({{input_value}}) to equal {{expected_result}}")
```

Return ONLY the rewritten or original test case function with clear and descriptive comments. Wrap the code in a ```python code block.
If the original test case seems good, return it unchanged. Only change it if it is necessary.
"""
