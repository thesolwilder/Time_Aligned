# Development Guide - Time Aligned

**⚠️ AGENTS: Read this file BEFORE implementing any features or bug fixes.**

## Overview

This project follows Test-Driven Development (TDD) practices with a structured approach to testing and feature development. All code must be properly tested before being considered complete.

## Testing Hierarchy

All new features and bug fixes must follow this testing progression:

### 1. Import Test (Smoke Test)

**Purpose**: Verify the module can be imported without errors  
**When**: First test for any new module or major refactor  
**How**:

```python
def test_import():
    """Verify module imports without errors."""
    from src import module_name  # or from tests import test_module
    assert module_name is not None
```

### 2. Unit Tests

**Purpose**: Test individual functions/methods in isolation  
**When**: After import test passes, test each function separately  
**Coverage Requirements**:

- All public functions/methods
- Edge cases and boundary conditions
- Error handling and exceptions
- Return values and side effects

**Pattern**:

```python
def test_function_name_expected_behavior():
    """Test that function_name does X when given Y."""
    # Arrange
    input_data = ...
    expected = ...

    # Act
    result = function_name(input_data)

    # Assert
    assert result == expected
```

### 3. Integration Tests

**Purpose**: Test components working together  
**When**: After unit tests pass, test module interactions  
**Examples**:

- Data flow between classes
- File I/O operations with real files
- UI components interacting with data models
- API calls and external dependencies

### 4. End-to-End Tests

**Purpose**: Test complete user workflows  
**When**: After integration tests pass  
**Examples**:

- Complete session tracking cycle
- Full data export workflow
- Settings changes affecting behavior

## Test Organization

### File Structure

```
tests/
├── __init__.py              # Makes tests importable
├── run_all_tests.py         # Test runner
├── test_data/               # Test fixtures and sample data
├── test_*.py                # Individual test modules
└── TEST_STATUS.md           # Current test suite status
```

### Naming Conventions

**Test Files**: `test_<module_name>.py`

- Example: `test_backup.py` tests backup functionality

**Test Functions**: `test_<function>_<scenario>`

- Example: `test_backup_creates_file_with_timestamp()`
- Be descriptive: `test_idle_detection_marks_session_inactive_after_threshold()`

**Test Classes**: `Test<ComponentName>` (optional, for grouping)

- Example: `class TestBackupSystem:`

### Test Data

- Use `tests/test_data/` for sample files
- Create fixtures in `conftest.py` if using pytest
- Clean up test artifacts in teardown
- Never modify production data files in tests

## Development Workflow

### Adding a New Feature

1. **Create test file** (if doesn't exist): `tests/test_<feature>.py`
2. **Write import test**: Verify module loads
3. **Write unit tests**: Test each function (TDD - write tests first!)
4. **Implement feature**: Write minimal code to pass tests
5. **Write integration tests**: Test feature with related components
6. **Refactor**: Improve code while keeping tests green
7. **Update documentation**: README, docstrings, etc.

### Fixing a Bug

1. **Create failing test**: Reproduce the bug in a test
2. **Verify test fails**: Confirms bug exists
3. **Fix the bug**: Minimal change to make test pass
4. **Run full test suite**: Ensure no regressions
5. **Add edge case tests**: Prevent similar bugs

### Before Committing

```bash
# Run all tests with coverage (suppress warnings)
python -W ignore -m coverage run tests/run_all_tests.py

# View coverage report
python -m coverage report
```

### Running Full Test Suite with Coverage

**RECOMMENDED METHOD**: Use `run_all_tests.py` with coverage

```powershell
python -W ignore -m coverage run tests/run_all_tests.py; python -m coverage report
```

**What this does**:

- `-W ignore`: Suppresses runtime warnings (DeprecationWarning, ResourceWarning, etc.)
- `coverage run tests/run_all_tests.py`: Runs the test runner with coverage tracking
- Discovers and runs **all** tests in the `tests/` directory (any file matching `test_*.py`)
- `coverage report`: Displays coverage statistics after tests complete

**Alternative: Suppress specific warning types only**

```powershell
# Suppress only deprecation warnings
python -W ignore::DeprecationWarning -m coverage run tests/run_all_tests.py; python -m coverage report

# Suppress multiple specific types
python -W ignore::DeprecationWarning -W ignore::ResourceWarning -m coverage run tests/run_all_tests.py; python -m coverage report
```

**Why use run_all_tests.py instead of unittest directly?**

- ✅ Properly discovers all test files in the tests directory
- ✅ Handles test dependencies and imports correctly
- ✅ Provides formatted test summary output
- ❌ Running `unittest` directly can cause import and path errors

**Output**: You'll see test progress followed by a summary and coverage report.

**Interpreting Results**:

- `.` = Test passed
- `E` = Error (test crashed)
- `F` = Failure (assertion failed)
- `s` = Test skipped
- Coverage report shows percentage of code tested

**Does run_all_tests.py run all tests?** Yes, it discovers and runs **all** test files matching `test_*.py` in the tests directory using unittest's discovery mechanism.

## Current Architecture

### Main Components

- **TimeTracker** (`time_tracker.py`): Main application class
- **UI Frames** (`src/`): Tkinter UI components
  - SessionTrackerFrame
  - AnalysisFrame
  - SettingsFrame
  - CompletionFrame
- **Business Logic**:
  - Data persistence (JSON)
  - Screenshot capture
  - Google Sheets integration
  - Backup system
  - CSV export

### Key Patterns

**Tightly Coupled UI**: UI frames currently require TimeTracker instance

- When testing, create full TimeTracker mock or use integration tests
- Future refactor: Extract business logic into services (see TEST_STATUS.md)

**Data Files**:

- `data.json`: Main session storage
- `settings.json`: Application settings
- `backups/`: Automatic backups with timestamps

**Mock Requirements**:

- Mock `tkinter` components for UI tests
- Mock file I/O for data tests
- Mock `time.time()` for timestamp tests
- Mock Google Sheets API for integration tests

## Testing Best Practices

### TDD Red-Green-Refactor Cycle

**CRITICAL: Red Phase Must Be a FAILURE, Not an ERROR**

When following TDD, the "red" phase should produce a **test failure**, not a test **error**:

- ✅ **FAILURE (F)**: Test runs but assertion fails - THIS IS CORRECT
  - Example: `AssertionError: Expected 5 but got None`
  - Means: Test logic is valid, implementation is missing/incomplete
- ❌ **ERROR (E)**: Test crashes with exception - THIS IS WRONG
  - Example: `ImportError`, `AttributeError`, `NameError`
  - Means: Test has bugs or references non-existent code
  - **Fix the test first** before implementing the feature

**Proper TDD Workflow:**

1. **Write test** - Should fail with assertion error (F), not exception (E)
2. **Run test** - Verify it shows FAIL (F), not ERROR (E)
   - If ERROR: Fix test imports, syntax, or scaffolding first
   - If FAIL: Proceed to implementation
3. **Implement** - Write minimal code to make test pass
4. **Run test** - Should now show PASS (.)
5. **Refactor** - Improve while keeping tests green

**Common Causes of Errors (E) Instead of Failures (F):**

- Missing imports in test file
- Typos in function/class names
- Missing stub/placeholder implementation
- Incorrect test setup or mocking

**Solution**: Create minimal scaffolding (empty functions, basic classes) so tests can run and fail properly.

### Do's ✅

- Write tests BEFORE implementation (TDD)
- Ensure red phase shows FAIL (F), not ERROR (E)
- Test one thing per test function
- Use descriptive test names
- Keep tests fast (mock I/O, external APIs)
- Clean up test artifacts
- Use `setUp`/`tearDown` or fixtures
- Test edge cases and error conditions
- Keep tests independent (no shared state)

### Don'ts ❌

- Don't test implementation details
- Don't write tests after the fact (TDD violation)
- Don't proceed with ERROR (E) in red phase - fix the test first
- Don't skip tests without documenting why
- Don't use production data
- Don't create interdependent tests
- Don't ignore failing tests
- Don't commit without running tests
- Don't mock what you're testing

## Common Testing Patterns

### Mocking Time

```python
from unittest.mock import patch
import time

@patch('time.time')
def test_with_frozen_time(mock_time):
    mock_time.return_value = 1234567890
    # Your test here
```

### Temporary Files

```python
import tempfile
import os

def test_with_temp_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        temp_path = f.name
        # Use temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)
```

### Mocking Tkinter

```python
from unittest.mock import Mock, MagicMock

# For basic Tk objects
root = Mock()
root.winfo_exists.return_value = True

# For widgets that need more behavior
widget = MagicMock()
widget.get.return_value = "test value"
```

## Code Quality Standards

### Before Submitting Code

- [ ] All tests pass
- [ ] New features have tests at all levels
- [ ] Bug fixes have regression tests
- [ ] Code follows existing patterns
- [ ] No commented-out code
- [ ] Docstrings for public functions
- [ ] No hardcoded paths or credentials
- [ ] Error handling is tested

### Documentation Requirements

- **Docstrings**: All public functions, classes, methods
- **Comments**: Complex logic, non-obvious decisions
- **README**: User-facing feature additions
- **DEVELOPMENT.md**: Developer-facing changes to workflow

## Directory Organization

### Keeping It Clean

- **Source code**: `src/` for modules, `time_tracker.py` for main app
- **Tests**: `tests/` mirroring source structure
- **Documentation**: Root level (README.md, DEVELOPMENT.md)
- **Data files**: Root level, excluded from git
- **Backups**: `backups/` directory
- **Screenshots**: `screenshots/` directory (user data)
- **Credentials**: `.gitignore` - never commit!

### Adding New Files

- **New feature module**: `src/<feature_name>.py`
- **New test file**: `tests/test_<feature_name>.py`
- **Configuration**: Root level if user-facing, `src/` if internal
- **Documentation**: `docs/` for extensive docs, root for key files

## Git Workflow

### Branch Strategy

- `main`: Stable, all tests passing
- `feature/<name>`: New features
- `bugfix/<name>`: Bug fixes
- `refactor/<name>`: Code improvements

### Commit Messages

```
<type>: <short description>

<optional detailed description>

Tests: <test status>
```

**Types**: feat, fix, test, refactor, docs, chore

**Example**:

```
feat: Add priority filtering to analysis view

Allows users to filter sessions by priority level in the analysis tab.
Includes dropdown selector and dynamic filtering logic.

Tests: All passing (15 new unit tests, 3 integration tests)
```

## Troubleshooting Tests

### Common Issues

**Import Errors**: Check `__init__.py` files exist in test directories

**Class Not Found**: Verify actual class name in source matches test imports

**Constructor Mismatch**: Check actual `__init__` signature before mocking

**Test Isolation**: Use `setUp`/`tearDown` to reset state between tests

**Flaky Tests**: Usually timing or state issues - use mocks, avoid `sleep()`

## Questions?

When in doubt:

1. Look at existing tests for patterns
2. Check `TEST_STATUS.md` for known issues
3. Follow TDD: Write test first, make it pass, refactor
4. Keep tests simple and focused

---

**Remember**: The goal is maintainable, reliable code. Tests are not a burden - they're your safety net that enables confident refactoring and rapid development.
