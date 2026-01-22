# TDD Quick Reference Guide

## What is TDD?

Test-Driven Development (TDD) is a software development approach where you write tests **before** writing the actual code.

## TDD Cycle (Red-Green-Refactor)

```
┌─────────────────────────────────────────────┐
│  1. RED: Write a failing test              │
│     - Test should fail (feature not yet    │
│       implemented)                          │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│  2. GREEN: Write minimal code to pass test │
│     - Make the test pass                   │
│     - Don't worry about perfect code yet   │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│  3. REFACTOR: Improve the code             │
│     - Clean up                             │
│     - Optimize                             │
│     - Tests should still pass              │
└───────────────┬─────────────────────────────┘
                │
                ▼
              Repeat
```

## Standard TDD Workflow

### Step 1: Write Tests First (RED Phase)

```bash
# Create test file
touch tests/test_new_feature.py

# Write comprehensive tests
# Tests should cover:
# - UI elements (buttons, forms, etc.)
# - Function existence
# - Function behavior
# - Data integrity
# - Edge cases
# - Integration

# Run tests - they SHOULD FAIL
python -m unittest tests.test_new_feature -v
```

**Expected Output:** FAILED (tests should fail because feature isn't implemented yet)

### Step 2: Implement Feature (GREEN Phase)

```bash
# Write minimal code to make tests pass
# Focus on functionality, not perfection

# Run tests again - they SHOULD PASS
python -m unittest tests.test_new_feature -v
```

**Expected Output:** OK (all tests passing)

### Step 3: Refactor (REFACTOR Phase)

```bash
# Clean up code
# Improve structure
# Optimize performance
# Add comments/documentation

# Run tests AGAIN - they SHOULD STILL PASS
python -m unittest tests.test_new_feature -v
```

**Expected Output:** OK (all tests still passing)

## Common Test Patterns

### Pattern 1: Testing UI Button Exists

```python
def test_button_exists(self):
    """Test that the feature button exists"""
    button_found = False

    def find_button(widget):
        nonlocal button_found
        if isinstance(widget, (tk.Button, ttk.Button)):
            text = str(widget.cget("text"))
            if "EXPECTED TEXT" in text.upper():
                button_found = True
                return
        for child in widget.winfo_children():
            find_button(child)

    find_button(self.frame)
    self.assertTrue(button_found, "Button should exist")
```

### Pattern 2: Testing Function Exists

```python
def test_function_exists(self):
    """Test that the function exists"""
    self.assertTrue(
        hasattr(self.object, "function_name"),
        "Object should have function_name method"
    )
```

### Pattern 3: Testing Data File Operations

```python
def test_data_saved_correctly(self):
    """Test that data is saved to file"""
    # Create test data
    test_data = {"key": "value"}

    # Save it
    with open("test_file.json", "w") as f:
        json.dump(test_data, f)

    # Verify file exists
    self.assertTrue(os.path.exists("test_file.json"))

    # Verify content matches
    with open("test_file.json", "r") as f:
        loaded_data = json.load(f)

    self.assertEqual(loaded_data, test_data)

    # Clean up
    os.remove("test_file.json")
```

### Pattern 4: Testing with Mocks

```python
from unittest.mock import Mock, patch

@patch('module.function_to_mock')
def test_with_mock(self, mock_function):
    """Test using a mock"""
    mock_function.return_value = "mocked value"

    result = call_function_that_uses_mock()

    self.assertEqual(result, "expected result")
    mock_function.assert_called_once()
```

### Pattern 5: Integration Test

```python
def test_complete_workflow(self):
    """Test end-to-end functionality"""
    # Setup
    initial_state = setup_test_environment()

    # Execute complete workflow
    step1_result = perform_step1()
    step2_result = perform_step2(step1_result)
    final_result = perform_step3(step2_result)

    # Verify
    self.assertEqual(final_result, expected_final_state)

    # Cleanup
    cleanup_test_environment()
```

## Test Organization

### File Structure

```
project/
├── module.py                 # Implementation
└── tests/
    ├── __init__.py
    ├── test_helpers.py       # Shared test utilities
    ├── test_module.py        # Unit tests
    └── test_module_integration.py  # Integration tests
```

### Test Class Naming

```python
# Format: Test<Module><Aspect>
class TestCSVExport(unittest.TestCase):
    """Tests for CSV export"""

class TestCSVExportButton(unittest.TestCase):
    """Tests for CSV export button"""

class TestCSVDataIntegrity(unittest.TestCase):
    """Tests for CSV data integrity"""
```

### Test Method Naming

```python
# Format: test_<what_is_being_tested>
def test_button_exists(self):
    """Test that button exists"""

def test_function_handles_empty_input(self):
    """Test function handles empty input correctly"""

def test_data_persists_after_save(self):
    """Test that data persists after saving"""
```

## Running Tests

### Run All Tests

```bash
# Using unittest
python -m unittest discover tests -v

# Using pytest (if installed)
pytest tests/ -v
```

### Run Specific Test File

```bash
python -m unittest tests.test_module -v
```

### Run Specific Test Class

```bash
python -m unittest tests.test_module.TestClassName -v
```

### Run Specific Test Method

```bash
python -m unittest tests.test_module.TestClassName.test_method -v
```

### Run with Coverage (if installed)

```bash
coverage run -m unittest discover tests
coverage report
coverage html  # Creates htmlcov/index.html
```

## Common Assertions

### Equality

```python
self.assertEqual(a, b)          # a == b
self.assertNotEqual(a, b)       # a != b
self.assertAlmostEqual(a, b)    # a ≈ b (for floats)
```

### Truth

```python
self.assertTrue(condition)      # condition is True
self.assertFalse(condition)     # condition is False
self.assertIsNone(obj)          # obj is None
self.assertIsNotNone(obj)       # obj is not None
```

### Membership

```python
self.assertIn(item, container)     # item in container
self.assertNotIn(item, container)  # item not in container
```

### Type Checks

```python
self.assertIsInstance(obj, cls)     # isinstance(obj, cls)
self.assertNotIsInstance(obj, cls)  # not isinstance(obj, cls)
```

### Exceptions

```python
with self.assertRaises(ValueError):
    function_that_should_raise()

with self.assertRaises(ValueError) as cm:
    function_that_should_raise()
self.assertEqual(str(cm.exception), "Expected error message")
```

### Collections

```python
self.assertListEqual(list1, list2)
self.assertDictEqual(dict1, dict2)
self.assertSetEqual(set1, set2)
```

## Setup and Teardown

### Per-Test Setup/Teardown

```python
class TestFeature(unittest.TestCase):
    def setUp(self):
        """Run before each test method"""
        self.temp_file = "test.txt"
        self.test_data = {"key": "value"}

    def tearDown(self):
        """Run after each test method"""
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
```

### Per-Class Setup/Teardown

```python
class TestFeature(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run once before all tests in class"""
        cls.shared_resource = create_expensive_resource()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests in class"""
        cls.shared_resource.cleanup()
```

## Best Practices

### ✅ DO

- Write tests first (before implementation)
- Test one thing per test method
- Use descriptive test names
- Keep tests independent
- Use setUp/tearDown for common code
- Mock external dependencies
- Test edge cases and error conditions
- Run tests frequently

### ❌ DON'T

- Write implementation before tests
- Test multiple things in one test
- Make tests depend on each other
- Leave test data/files after tests
- Test implementation details
- Skip testing error cases
- Let tests become slow

## Example: Complete TDD Workflow

### Requirement

"Add a button to export data to CSV"

### Step 1: Write Tests (RED)

```python
# tests/test_csv_export.py
import unittest

class TestCSVExport(unittest.TestCase):
    def test_export_button_exists(self):
        """Test that export button exists"""
        # ... test implementation
        self.assertTrue(button_found)

    def test_export_function_exists(self):
        """Test that export function exists"""
        self.assertTrue(hasattr(frame, 'export_to_csv'))

    def test_csv_file_created(self):
        """Test that CSV file is created"""
        # ... test implementation
        self.assertTrue(os.path.exists('export.csv'))
```

Run: `python -m unittest tests.test_csv_export -v`  
Result: **FAILED** (expected - feature not implemented yet)

### Step 2: Implement (GREEN)

```python
# module.py
def export_to_csv(self):
    """Export data to CSV file"""
    # Minimal implementation to pass tests
    with open('export.csv', 'w') as f:
        f.write('data')

# Add button that calls export_to_csv
```

Run: `python -m unittest tests.test_csv_export -v`  
Result: **OK** (all tests pass)

### Step 3: Refactor

```python
# module.py
def export_to_csv(self):
    """
    Export data to CSV file with proper formatting

    Creates a CSV file with headers and properly escaped data.
    Opens file location after successful export.
    """
    import csv

    # Clean, well-structured implementation
    with open('export.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Header1', 'Header2'])
        writer.writerows(self.data)

    # Open file location
    os.startfile(os.path.dirname('export.csv'))
```

Run: `python -m unittest tests.test_csv_export -v`  
Result: **OK** (tests still pass after refactoring)

## Troubleshooting

### Tests Don't Fail Initially

**Problem:** Tests pass even though feature isn't implemented  
**Solution:** Make tests more specific and verify they test the actual behavior

### Tests Are Slow

**Problem:** Test suite takes too long to run  
**Solution:** Mock external dependencies, use setUp/tearDown efficiently, run subset of tests during development

### Tests Break Often

**Problem:** Tests fail after unrelated changes  
**Solution:** Tests may be too tightly coupled to implementation details. Test behavior, not implementation.

### Can't Test UI Components

**Problem:** Hard to test tkinter widgets  
**Solution:** Use widget tree traversal (see Pattern 1), separate business logic from UI

## Resources

### In This Project

- `tests/test_helpers.py` - Shared test utilities
- `CSV_EXPORT_IMPLEMENTATION.md` - Example TDD implementation
- `TESTING_GUIDE.md` - Comprehensive testing documentation

### External Resources

- [Python unittest documentation](https://docs.python.org/3/library/unittest.html)
- [Test-Driven Development by Example](https://www.oreilly.com/library/view/test-driven-development/0321146530/) (Book)

## Quick Commands Cheat Sheet

```bash
# Create new test file
touch tests/test_feature.py

# Run all tests
python -m unittest discover tests -v

# Run specific test file
python -m unittest tests.test_feature -v

# Run specific test
python -m unittest tests.test_feature.TestClass.test_method -v

# Run with coverage
coverage run -m unittest discover tests
coverage report

# The TDD cycle
python -m unittest tests.test_feature -v  # Should FAIL (red)
# ... write code ...
python -m unittest tests.test_feature -v  # Should PASS (green)
# ... refactor ...
python -m unittest tests.test_feature -v  # Should STILL PASS
```

---

**Remember:** Tests are documentation. They show how your code should be used and what it should do.
