# GitHub Copilot Instructions

**🤖 AI Agents: These are standing orders for all work on this repository.**

## Primary Directive

**ALWAYS read [DEVELOPMENT.md](../DEVELOPMENT.md) before implementing features or fixing bugs.**

## Test-Driven Development (Required)

1. **Import Test** → 2. **Unit Tests** → 3. **Integration Tests** → 4. **E2E Tests**

Never skip steps. Write tests BEFORE implementation code.

## Before Any Code Changes

- [ ] Read DEVELOPMENT.md testing hierarchy
- [ ] Check TEST_STATUS.md for known issues
- [ ] Verify test file exists: `tests/test_<module>.py`
- [ ] Plan test coverage for the change

## After Code Changes

- [ ] All new functions have unit tests
- [ ] Integration tests added if component interactions changed
- [ ] All tests pass: `python tests/run_all_tests.py`
- [ ] No regressions in existing tests

## Code Standards

- **Style**: Follow existing patterns in the codebase
- **Imports**: Use absolute imports from `src.*`
- **Testing**: Mock external dependencies (files, APIs, time)
- **Documentation**: Docstrings for all public functions
- **Data**: Never use production data in tests

## File Organization

- Source: `src/` or `time_tracker.py`
- Tests: `tests/test_*.py`
- Test data: `tests/test_data/`
- Docs: Root level or `docs/`

## Testing Patterns

**Import smoke test example:**

```python
def test_import():
    from src import new_module
    assert new_module is not None
```

**Unit test pattern:**

```python
def test_function_expected_behavior():
    # Arrange
    input_val = "test"
    expected = "result"

    # Act
    result = function(input_val)

    # Assert
    assert result == expected
```

## Common Mocks

```python
# Time
@patch('time.time', return_value=1234567890)

# Files
from unittest.mock import mock_open, patch
m = mock_open(read_data="test data")

# Tkinter
from unittest.mock import Mock
root = Mock()
```

## Questions to Ask Before Implementing

1. What tests need to be written?
2. What existing tests might break?
3. Does this change the public API?
4. Are there edge cases to test?
5. Can this be tested in isolation?

## Failure Mode

If you cannot determine the correct approach:

1. Reference DEVELOPMENT.md
2. Look at similar existing tests
3. Ask for clarification rather than guessing

---

**Default assumption**: User wants TDD approach with full test coverage. If unsure, write tests first.
