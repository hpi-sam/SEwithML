write_test_case_prompt = """You are an expert Python programmer who writes clear and helpful test cases following best practices.

Your task is to write a SINGLE test case function that maximizes bug discovery while following these principles:

TEST STRUCTURE:
- Follow "Arrange, Act, Assert" pattern
- One clear assertion per test (unless multiple are essential)
- Include descriptive test name and clear docstring
- Ensure tests are repeatable and self-contained
- Include meaningful assertion messages
- Keep tests concise and readable
- Follow PEP8 style guide

TEST QUALITY:
- Use realistic test data
- Avoid complex setup code
- Test both positive and negative scenarios
- Be creative in finding potential bugs
- Choose specific, descriptive test names (avoid generic terms like "edge_cases")

COVERAGE PRIORITIES:
1. Focus on uncovered lines first
   - Make sure to test the first uncovered line
2. Only test edge cases and error scenarios after achieving full line coverage

RATIONALE:
- We want to maximize the bug discovery rate, so we prioritize covering uncovered lines first
- We want to have a minimal number of tests, so we prioritize covering multiple lines if possible
- We want to have a sensible order of tests, so we prioritize the first uncovered line

EXAMPLE:
- In a match statement with 7 cases where the first 4 cases don't have a return statement and the last 3 cases returns something, 
  you should write a test that covers at least the first case, but also other cases if possible (to maximize line coverage).
- In the same setup, if the first test case covers the first 2 cases, you should write a second test that covers the next uncovered line
  and if possible other cases.
- In the same setup, if the first two test cases cover the first 4 cases, you should write a third test that covers the next uncovered line
  (here it is not possible to cover the last 3 cases, because they all have a return statement - so only test the first uncovered case).
- etc. (this way, if we have a match statement with 100 cases, we will need a maximum of 100 tests to cover all lines)

FORMAT SPECIFICATION:
```python
def test_specific_scenario_being_tested(self):
    \"\"\"Clear description of the test's purpose and expectations.\"\"\"
    # Arrange
    calculator = Calculator()
    
    # Act
    result = calculator.add(5, -3)
    
    # Assert
    self.assertEqual(2, result, "Adding positive and negative numbers should work correctly")
```

TEST TEMPLATE:
```python
import unittest
from typing import *
from code_to_test import *

class GeneratedTestCases(unittest.TestCase):

    # .. existing tests ..

    # Your generated test case is inserted here
    def test_specific_scenario_being_tested(self) -> None:
        \"\"\"Clear description of the test's purpose and expectations.\"\"\"
        # Arrange
        # Act
        # Assert

if __name__ == "__main__":
    unittest.main()
```

EXAMPLE:
This is a bad generation because it uses multiple assertions (which is not allowed):
```python
def test_grade_assignment_a_and_b_grades(self):
    \"\"\"Test grade assignment for scores in A and B ranges.\"\"\"
    # Get grades for both A and B range scores
    a_grade = assign_letter_grade(95)
    b_grade = assign_letter_grade(85)

    # Assert both grade assignments
    self.assertEqual(a_grade, "A", "Score of 95 should receive an A grade")
    self.assertEqual(b_grade, "B", "Score of 85 should receive a B grade")
```

This is a good generation because it uses a single assertion to cover a single case (which is allowed):
```python
def test_grade_assignment_boundary_scores(self):
    \"\"\"Test grade assignment logic by checking score at B/C boundary.\"\"\"
    # Get grade at the B/C boundary (80)
    # This validates both the B grade range (>= 80) and C grade range (< 80)
    result = assign_letter_grade(80)
    
    self.assertEqual(result, "B", "Score of 80 should receive a B grade (validates B/C boundary)")
```  

This is a very good generation because it uses a single assertion to cover multiple cases (which is allowed and desirable):
(Example code)
```python
# Code to test
def process_order_status(step: int, is_premium: bool = False) -> str:
    \"\"\"Process an order status and return the appropriate customer message.\"\"\"
    msg = "Your order is being processed"
    
    match step:
        case 1:
            msg = msg + " by our team"
        case 2:
            msg = msg + " and has been confirmed"
        case 3:
            msg = msg + " through our warehouse"
        case 4:
            return msg + " and is now in transit"
        case 5:
            return "Your order has been delivered"
        case _:
            return "Invalid order step"
    return msg
```

Now here is the very good generation:
```python
def test_order_status_message_construction(self):
    \"\"\"Test message construction through multiple processing stages.
    
    This test validates the message building logic across multiple stages
    by checking step 4, which allows the message to accumulate through
    cases 1, 2, and 3 before returning in case 4.\"\"\"
    result = process_order_status(4)
    
    self.assertEqual(
        result,
        "Your order is being processed by our team and has been confirmed through our warehouse and is now in transit",
        "Message should accumulate updates through step 4 of processing"
    )
```

Context provided:
- Code to test: 
{code_to_test}

- Uncovered lines: 
{uncovered_lines}

- Existing tests:
{existing_tests}

- Coverage matrix:
{coverage_matrix}

Note: Do not add explicit comments for Arrange/Act/Assert sections - focus on meaningful comments about test purpose, input choice rationale, and expected behavior.

Return ONLY one test case function wrapped in a ```python code block.
"""