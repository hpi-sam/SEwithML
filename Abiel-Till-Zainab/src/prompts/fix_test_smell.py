fix_test_smell_prompt = """You are an expert at fixing test smells in Python unit tests.

Your task is to rewrite a test to follow these key principles:
1. Clear Arrange-Act-Assert structure
2. Single, focused assertion with meaningful message
3. Descriptive test name that explains the scenario
4. Clear docstring explaining purpose
5. Realistic test data
6. No interdependence with other tests
7. No complex setup code
8. No non-deterministic elements
9. No multiple assertions in one test case (in this case, remove all assertions except the first one)

Bad example:
```python
def test_calculation(self):
    calc = Calculator()
    res1 = calc.add(15, 30)  # Magic numbers
    res2 = calc.subtract(res1, 10)
    self.assertEqual(45, res1)  # Multiple assertions
    self.assertEqual(35, res2)
```

Good example:
```python
def test_add_handles_large_positive_numbers(self):
    \"\"\"Verify calculator can add large positive integers within system limits.\"\"\"
    # Arrange
    calculator = Calculator()
    max_safe_value = 1000000  # Explained constant
    
    # Act
    result = calculator.add(max_safe_value, max_safe_value)
    
    # Assert
    self.assertEqual(2000000, result, 
                    "Calculator should handle adding large positive numbers correctly")
```
Please do not have the explicit Arrange, Act, Assert comments in your test case (this would be too verbose and annoying to read for the user), but follow their structure for your test case.


A test smell indicates that a test is not properly testing the functionality it should test. Here are key test smells and how to fix them:

1. Assertion Roulette: Add clear messages to each assertion explaining what it tests
Bad:
```python
def test_user():
    user = create_user("test@test.com", "password123")
    assert user.email == "test@test.com"  # No message
    assert user.is_active  # No message
    assert user.created_at is not None  # No message
```

Good:
```python
def test_user():
    user = create_user("test@test.com", "password123")
    assert user.email == "test@test.com", "Email should match input"
    assert user.is_active, "New user should be active by default"
    assert user.created_at is not None, "Created timestamp should be set"
```

2. Conditional Test Logic: Split into separate test cases
Bad:
```python
def test_process():
    if some_condition:
        assert process() == "result1"
    else:
        assert process() == "result2"
```

Good:
```python
def test_process_condition_true():
    assert process(condition=True) == "result1", "Process should return result1 when condition is True"

def test_process_condition_false():
    assert process(condition=False) == "result2", "Process should return result2 when condition is False"
```

3. Empty Test: Implement meaningful assertions
Bad:
```python
def test_nothing():
    # TODO: implement test
    pass
```

Good:
```python
def test_specific_behavior():
    result = function_under_test()
    assert result == expected_value, "Function should return expected value"
```

4. Magic Number Test: Use named constants or explain numbers
Bad:
```python
def test_calculation():
    result = calculate_score(15, 30)  # Magic numbers
    assert result == 45
```

Good:
```python
def test_calculation():
    base_score = 15  # Initial player score
    bonus_points = 30  # Points from power-up
    expected_total = 45  # Base + bonus
    result = calculate_score(base_score, bonus_points)
    assert result == expected_total, "Score should be sum of base score and bonus points"
```

5. Redundant Assertions: Remove obvious/duplicate assertions
Bad:
```python
def test_obvious():
    assert True == True
    assert 1 == 1
```

Good:
```python
def test_meaningful():
    result = complex_operation()
    assert result.is_valid(), "Operation should produce valid result"
```

6. Unknown Test: Add clear purpose and assertions
Bad:
```python
def test_something():
    result = process_data()
    print(result)  # Just prints, no assertions
```

Good:
```python
def test_data_processing():
    # Test that process_data correctly transforms input
    input_data = {{"key": "value"}}
    result = process_data(input_data)
    assert result["processed_key"] == "processed_value", "Data should be correctly transformed"
```

Your task:
Given a test with smells, output a rewritten version that:
- Has clear purpose documented in comments and function name
- Includes meaningful assertions with descriptive messages
- Splits conditional logic into separate test cases
- Uses named constants or explains numeric values
- Removes redundant assertions
- Has proper setup and teardown if needed
- **DO NOT WRITE MORE THAN ONE TEST CASE and try not to have multiple assertions in one test case.**
- If you think multiple assertions make sense given the theme of the test case, you may use them (write clean code without any test smells), but prefer to split them into multiple test cases.
- If the test case needs any additional imports, add them within your test case function (we use isort later to sort imports).

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
Here's a good output example that satisfies our test case format:
```python
def test_add_two_positive_integers(self):
    \"\"\"Test adding two positive integers.\"\"\"
    result = add(3, 5)
    self.assertEqual(result, 8, "Expected 3 + 5 to equal 8")
```

Your task:
Output only the rewritten test code, maintaining the original test's intent while fixing all identified smells.
The above are examples that you can be inspired by. Now fix the following test. Do not change the purpose of the test, only fix the smells:

The code that is tested is:
```python
{code_to_test}
```

The identified smells/why we want to fix this test are:
{identified_smells}

The unit test to fix is:
```python
{unit_test}
```

Reminder: **Do not write more than one test** and try not to change the purpose of the test dramatically. 
This means that if there are for example multiple assertions in the test, you should not split them into multiple tests. Instead, you should write a single test and combine the assertions into a single test or delete additional assertions.
Output ONLY one fixed single test case function (of the unit test to fix) in ```python``` tags.
"""
