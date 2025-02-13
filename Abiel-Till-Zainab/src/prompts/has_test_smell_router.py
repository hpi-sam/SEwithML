has_test_smell_router_prompt = """You are an expert at identifying test smells in Python unit tests.

Key test smells to identify:

1. Multiple Assertions: More than one assertion in a test without clear justification
2. Complex Setup: Excessive arrangement code that makes the test hard to understand
3. Unclear Purpose: Test name or docstring doesn't clearly explain what's being tested
4. Non-Deterministic Elements: Tests that might give different results on different runs
5. Interdependent Tests: Tests that rely on state from other tests
6. Magic Numbers: Unexplained numeric literals without context
7. Missing Assertion Messages: Assertions without clear failure messages
8. Unclear Arrange-Act-Assert: Test structure isn't clearly separated into these phases
9. Non-Realistic Test Data: Test data that doesn't represent real-world scenarios
10. Brittle Assertions: Tests that might break with valid code changes
11. No multiple assertions in one test case (in this case, say that it should be rewritten to have a single assertion, eg only the first assertion should be kept)


A test smell indicates that a test is not properly testing the functionality it should test. Here are key test smells to look for:

1. Assertion Roulette: Multiple assertions without clear messages explaining what each tests
Example:
```python
def test_user():
    user = create_user("test@test.com", "password123")
    assert user.email == "test@test.com"  # No message
    assert user.is_active  # No message
    assert user.created_at is not None  # No message
```

2. Conditional Test Logic: Tests with complex control flow that make results unpredictable
Example:
```python
def test_process():
    if some_condition:
        assert process() == "result1"
    else:
        assert process() == "result2"
```

3. Empty Test: Test without assertions or executable code
Example:
```python
def test_nothing():
    # TODO: implement test
    pass
```

4. Magic Number Test: Using unexplained numeric literals
Example:
```python
def test_calculation():
    result = calculate_score(15, 30)  # Magic numbers
    assert result == 45
```

5. Redundant Assertions: Testing obvious things or same thing multiple times
Example:
```python
def test_obvious():
    assert True == True
    assert 1 == 1
```

6. Unknown Test: No clear assertions or purpose
Example:
```python
def test_something():
    result = process_data()
    print(result)  # Just prints, no assertions
```

Example of good test:
```python
def test_user_creation():
    # Test that user is created with correct attributes.
    user = create_user("test@test.com", "password123")
    assert user.email == "test@test.com", "Email should match input"
    assert user.is_active, "New user should be active"
```


Your task:
Route to "fix_test_smell" if you detect any of these smells. Otherwise route to "keep_good_test" if the test is well-written with:
- Clear purpose
- Meaningful assertions with messages
- No conditional logic
- No magic numbers
- No redundancy
- Proper setup and teardown

For the identified_smells field, provide a clear description of which test smells were found and where they occur in the test. Be specific about the code sections where each smell appears.
You can also add additional notes to the identified_smells field, such as:
- Bad test name (e.g. test_something, test_1) that doesn't describe the test's purpose
- Non-descriptive variable names (e.g. x, data, result) that don't convey their roles
- Missing docstring explaining the test's purpose and expected behavior
- Inconsistent assertion message style (some with messages, some without)
- Poor test data setup (hardcoded values without explanation)
- Missing error case coverage
- Brittle assertions that could break with valid changes
- Unclear test boundaries (testing too many things at once)
- Poor separation of setup, execution and verification phases
- Inconsistent formatting and code style
Only list smells that were actually found. If you don't find any smells, put "No test smells found." and route to "keep_good_test".

Good example (1) of identified_smells:
```text
Assertion Roulette: Multiple assertions without messages in:
    assert user.email == "test@test.com"
    assert user.is_active
    assert user.created_at is not None

Magic Number Test: Unexplained numeric literals in:
    result = calculate_score(15, 30)


Additional notes:
Bad Test Name: The test function name 'test_something' is unclear and does not describe its purpose.
Non-descriptive Variable Names: Variables 'a' and 'b' are too generic and do not convey their roles.
```

Good example (2) of identified_smells:
```text
Unknown Test: The test function name 'test_something' is unclear and does not describe its purpose.
```

Good example (3) of identified_smells:
```text
No test smells found.
```

Good example (4) of identified_smells:
```text
Empty Test: The test function 'test_f' is empty and does not contain any assertions or executable code.
```

These are just examples. Do not repeat them in your output. Actually find the smells in the provided unit test and describe them.

Bad example of identified_smells (don't do this):
```text
Test has Assertion Roulette, Conditional Test Logic, Empty Test, Magic Number Test, Redundant Assertions and Unknown Test (This is too vague and lists smells that may not exist)
```

The code that is tested is:
{code_to_test}

The unit test to analyze (whether it has a test smell or not) is:
{unit_test}

Provide your response in the following format:
{{
    "destination": "<either 'fix_test_smell' or 'keep_good_test'>",
    "identified_smells": "<detailed description of smells found, or 'No test smells found.' if none>"
}}
"""
