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
# Run all tests
python tests/run_all_tests.py

# Verify no regressions
# All tests should pass or have documented reasons for skipping
```

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

### Do's ✅

- Write tests BEFORE implementation (TDD)
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
