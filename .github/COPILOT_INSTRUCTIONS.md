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

## Development Workflows

**Shortcuts**: When user types these phrases, apply the corresponding workflow:

- "bug fix" or "fix bug" or "b" → Bug Fix Workflow
- "new feature" or "add feature" or "f" → Feature Implementation Workflow
- "add tests" or "t" → Add Tests Workflow
- "review" or "check code" or "r" → Code Review Checklist

### Bug Fix Workflow

Following DEVELOPMENT.md bug fix workflow:

**Process:**

1. Create a failing test that reproduces the bug
2. Verify test fails
3. Fix the bug with minimal changes
4. Verify test passes
5. Run full test suite (no regressions)
6. Add edge case tests if needed

**⛔ TKINTER TEST TEARDOWN — FORBIDDEN PATTERN (checked every time):**

```python
# ❌ FORBIDDEN — causes TclError in subsequent tests:
self.addCleanup(self.root.destroy)

# ✅ REQUIRED — always use this instead:
def tearDown(self):
    from tests.test_helpers import safe_teardown_tk_root
    safe_teardown_tk_root(self.root)
    self.file_manager.cleanup()
```

### Feature Implementation Workflow

Following DEVELOPMENT.md standards:

**Requirements:**

1. Read DEVELOPMENT.md testing hierarchy
2. Create `tests/test_[feature].py`
3. Write tests FIRST (TDD approach):
   - Import test (smoke test)
   - Unit tests (isolated functions)
   - Integration tests (component interactions)
   - E2E tests (complete workflow)
4. Implement minimal code to pass tests
5. Run full test suite to verify no regressions

### Add Tests Workflow

Add comprehensive tests following DEVELOPMENT.md:

**Test progression:**

1. Import test (if new module)
2. Unit tests for each function
3. Integration tests for interactions
4. E2E tests for workflows

**⛔ TKINTER TEST TEARDOWN — FORBIDDEN PATTERN (checked every time):**

```python
# ❌ FORBIDDEN — causes TclError in subsequent tests:
self.addCleanup(self.root.destroy)

# ✅ REQUIRED — always use this instead:
def tearDown(self):
    from tests.test_helpers import safe_teardown_tk_root
    safe_teardown_tk_root(self.root)
    self.file_manager.cleanup()
```

### Code Review Checklist

Review implementation against standards:

**Testing & Quality Assurance:**

- [ ] Test coverage (import → unit → integration → E2E)
- [ ] All tests passing with no warnings
- [ ] Edge cases and error paths tested
- [ ] No test data in production code

**Architecture & Design:**

- [ ] Follows existing patterns and project structure
- [ ] Single Responsibility Principle (each function does ONE thing)
- [ ] DRY principle (no duplicate code)
- [ ] Proper separation of concerns

**Documentation:**

- [ ] Docstrings present for all public functions/classes
- [ ] Complex logic has explanatory comments
- [ ] README accurately reflects current functionality
- [ ] Type hints on function signatures

**Configuration & Dependencies:**

- [ ] No hardcoded values (use config files/constants)
- [ ] All dependencies in requirements.txt with versions
- [ ] Environment variables documented
- [ ] Sensitive data excluded from version control

**Error Handling & Logging:**

- [ ] Comprehensive error handling (try/except where appropriate)
- [ ] User-friendly error messages
- [ ] Logging used instead of print statements for debugging
- [ ] No silent failures

**Code Quality (CRITICAL FOR PORTFOLIO):**

- [ ] **Strictly follows PEP 8 formatting standards**
- [ ] **Absolutely NO dead code, commented-out code, or unused imports**
- [ ] **Clear, descriptive variable/function names (no abbreviations)**
- [ ] **Consistent naming conventions throughout**
- [ ] **Maximum function length ~50 lines (break up large functions)**
- [ ] **Human readability prioritized over "clever" code**
- [ ] **No magic numbers - use named constants**
- [ ] **Proper use of whitespace for visual clarity**

---

**Default assumption**: User wants TDD approach with full test coverage. If unsure, write tests first.
