# Development Guide - Time Aligned

**⚠️ CRITICAL: AI AGENTS MUST FOLLOW THESE DIRECTIVES**

## 🧠 DECISION LOG

### ⚠️ DIRECTIVE 1: READ BEFORE ANY ACTION

**BEFORE making ANY code changes**, you MUST read [DECISION_LOG.md](DECISION_LOG.md) to:

- Review what approaches have been tried before
- Understand what worked and what didn't work
- Avoid repeating failed approaches
- Learn from past successful patterns

**🔍 CRITICAL: Search for Related Entries**

When working on a specific task (bug fix, feature, or test), you MUST:

1. **Search DECISION_LOG.md for keywords related to your task**
   - Module names (e.g., "analysis_frame", "timeline", "backup")
   - Technology/library names (e.g., "tkinter", "pandas", "CSV")
   - Error patterns (e.g., "geometry manager", "headless", "width")
   - Feature areas (e.g., "columns", "filtering", "export")

2. **Review ALL related entries before starting**
   - Check "What Didn't Work" sections for past failures
   - Note specific error messages and their causes
   - Review "Key Learnings" for best practices
   - Apply successful patterns from "What Worked" sections

3. **Common pitfalls to search for:**
   - **Tkinter tests**: Search "tkinter", "headless", "geometry", "winfo"
     - Example: Mixing `pack()` and `grid()` causes TclError
     - Example: `winfo_width()` returns 1px in headless tests, use `winfo_reqwidth()`
   - **File operations**: Search "file", "backup", "JSON", "CSV"
   - **UI components**: Search specific widgets, "frame", "canvas", "label"
   - **Data processing**: Search "filtering", "sorting", "aggregation"

**Why this matters**: DECISION_LOG.md contains solutions to problems you WILL encounter. Not searching it wastes time repeating failed approaches.

### ⚠️ DIRECTIVE 2: UPDATE AFTER EVERY CHANGE

**AFTER completing ANY code changes**, you MUST update [DECISION_LOG.md](DECISION_LOG.md) with:

- Everything you tried (all approaches, not just the final one)
- Whether each approach worked or failed
- WHY it worked or didn't work
- Emphasis on what worked (so it can be reused)
- Key learnings for future reference

**This is not optional** - it builds institutional knowledge and prevents wasted effort.

---

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

## � FORBIDDEN PATTERNS — NEVER USE THESE IN TKINTER TESTS

**Search keywords: forbidden pattern, addCleanup root destroy, Tcl_AsyncDelete, TclError init.tcl, wrong thread**

| ❌ FORBIDDEN                                 | ✅ REQUIRED REPLACEMENT                              |
| -------------------------------------------- | ---------------------------------------------------- |
| `self.addCleanup(self.root.destroy)`         | `tearDown()` with `safe_teardown_tk_root(self.root)` |
| `self.root.destroy()` called directly        | `safe_teardown_tk_root(self.root)` in `tearDown()`   |
| Inline import `from test_helpers import ...` | Top-level `from tests.test_helpers import ...`       |
| Running full pytest suite in agent env       | Run as `python test_file.py` OR one class at a time  |

> **WHY**: `self.addCleanup(self.root.destroy)` does NOT cancel pending `after()` callbacks
> before destroying the root. This leaves the Tcl interpreter in a corrupted state.
> The **next** test's `tk.Tk()` then fails with `TclError: Can't find a usable init.tcl`.
> `safe_teardown_tk_root` cancels all callbacks first, then quits and destroys cleanly.
>
> **This has caused repeated failures across this codebase.** The user has had to
> correct this pattern multiple times. DO NOT USE `self.addCleanup(self.root.destroy)`.

---

> ⚠️ **AGENT ENVIRONMENT TCLERROR — DO NOT TRY TO FIX THIS**
>
> **Search keywords: TclError agent env, tcl_findLibrary, pytest suite TclError, agent tcl error, TclError invalid command, pytest TclError fail**
>
> When running Tkinter tests via **pytest** in the agent/CI environment with many test
> classes, you may see 1–2 tests FAIL with:
>
> ```
> TclError: invalid command name "tcl_findLibrary"
> TclError: Can't find a usable init.tcl
> ```
>
> **THIS IS NOT A REAL TEST FAILURE.** It is a pytest session isolation artifact caused
> by multiple `tk.Tk()` instances across many test classes in one session.
>
> **DO NOT:**
>
> - ❌ Modify the teardown pattern — it is already correct with `safe_teardown_tk_root`
> - ❌ Switch to `setUpClass`/`tearDownClass` — tried and abandoned, makes things worse
> - ❌ Add `addCleanup` patterns — FORBIDDEN (see above)
> - ❌ Treat it as a real test failure requiring code fixes
> - ❌ Waste time "debugging" it
>
> **CORRECT VERIFICATION — always use one of these two methods:**
>
> ```bash
> # Option 1: Run file as a script (most reliable):
> python tests/test_your_file.py
>
> # Option 2: Run one class at a time via pytest:
> pytest tests/test_your_file.py::TestClassName -v
> ```
>
> User confirmed: running as a script gives `OK` for all tests even when pytest shows failures.
> The user does not want to be reminded of this again — **check the script output first**.

---

## �📋 TDD Test Template (USE THIS FOR ALL NEW TESTS)

**⚠️ CRITICAL: Use this exact template when creating new Tkinter UI tests**

Search keywords: **TDD template, test template, tkinter test, setUp tearDown**

```python
"""
Tests for [Feature Name]

Description of what this test file covers.
"""

import unittest
import tkinter as tk
from tkinter import ttk
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from src.your_module import YourClass
from test_helpers import TestFileManager, TestDataGenerator


class TestYourFeature(unittest.TestCase):
    """Test [specific aspect of feature]"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        # ❌ DO NOT USE: self.addCleanup(self.root.destroy)

        # Create test settings/data files
        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_data.json"
        )

    def tearDown(self):
        """Clean up after tests"""
        from tests.test_helpers import safe_teardown_tk_root
        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_feature_expected_behavior(self):
        """Test that feature does X when given Y"""
        # Arrange
        tracker = TimeTracker(
            self.test_settings_file, self.test_data_file, root=self.root
        )

        # Act
        result = tracker.some_method()

        # Assert
        self.assertEqual(result, expected_value)


if __name__ == "__main__":
    unittest.main()
```

**Key Points**:

- ✅ Import `safe_teardown_tk_root` in `tearDown()` method
- ✅ Use `TestFileManager` for test file cleanup (via `addCleanup`)
- ✅ Use `TestDataGenerator` for creating test data
- ✅ **NEVER** use `self.addCleanup(self.root.destroy)` - causes crashes
- ✅ Always call `safe_teardown_tk_root(self.root)` in tearDown
- ✅ Always call `self.file_manager.cleanup()` after safe_teardown_tk_root
- ✅ **NEVER** use hardcoded dates without setting `selected_card = 2` (see Date Handling section below)

## 📅 Date Handling in Tests

**⚠️ CRITICAL: Hardcoded dates cause test failures over time**

### The Problem

Tests with hardcoded dates like `"2026-01-22"` will fail when that date falls outside the default filter window ("Last 7 Days" = `selected_card = 0`). This causes tests to pass today but fail in the future.

### Solution: Choose Based on Test Purpose

**Option 1: Use `datetime.now()` for tests requiring recent data**

```python
from datetime import datetime, timedelta

def test_recent_data_filtering(self):
    # Use dynamic dates for tests that need "current" data
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    date = today.strftime("%Y-%m-%d")

    test_data = {f"{date}_session1": {"date": date, ...}}
```

**Use when**: Test logic requires recent/current dates (e.g., testing "Last 7 Days" filter behavior)

**Option 2: Use hardcoded dates + `selected_card = 2` (All Time)**

```python
def test_specific_date_logic(self):
    date = "2026-01-22"  # Specific date for test consistency
    test_data = {f"{date}_session1": {"date": date, ...}}

    # CRITICAL: Set to "All Time" to ensure date is included
    frame.selected_card = 2  # All Time - ensures test date is always visible
    frame.update_timeline()
```

**Use when**: Test needs specific dates for consistency (e.g., testing date parsing, specific scenarios)

**Option 3: Combination approach** (RECOMMENDED)

- Use `datetime.now()` for timeline/filter tests that need recent data
- Use hardcoded + `selected_card = 2` for tests that need specific dates

### Required Filter Settings for Timeline Tests

**ALWAYS set these filter variables before calling `update_timeline()` or `get_timeline_data()`:**

```python
frame.status_filter.set("all")  # "all", "active", or "archived"
frame.sphere_var.set("All Spheres")  # or specific sphere name
frame.project_var.set("All Projects")  # or specific project name
frame.selected_card = 2  # 0=Last 7 Days, 1=Last 30 Days, 2=All Time
frame.update_timeline()
```

### Common Pitfalls

❌ **DON'T**: Use hardcoded dates without setting `selected_card`

```python
date = "2026-01-22"  # Will fail after 2026-01-29 (8 days later)
# ... no selected_card set (defaults to 0 = Last 7 Days)
frame.update_timeline()  # FAILS: No data visible!
```

✅ **DO**: Set `selected_card = 2` for hardcoded dates

```python
date = "2026-01-22"  # Specific date for test consistency
frame.selected_card = 2  # All Time - ensures always visible
frame.update_timeline()  # WORKS: Data visible regardless of test run date
```

✅ **DO**: Use `datetime.now()` for dynamic tests

```python
today = datetime.now().strftime("%Y-%m-%d")  # Always current
# Works with default selected_card = 0 (Last 7 Days)
frame.update_timeline()  # WORKS: Data is recent
```

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
- Clean up test artifacts in teardown (use `TestFileManager` helper)
- Never modify production data files in tests

## Development Workflow

### Running Tests

**⚠️ CRITICAL: Run tests ONCE with all needed output to avoid multiple executions**

When running tests, capture comprehensive output in a single execution:

```bash
# Run with full output (stdout + stderr)
python tests/test_<module>.py 2>&1
```

**During Development**: Run only the relevant test files

```bash
# Run specific test file
python tests/test_<module>.py

# Run multiple related test files
python tests/test_backup.py
python tests/test_session_tracker.py
```

**Before Major Commits**: Run full test suite with coverage

```bash
python -W ignore -m coverage run tests/run_all_tests.py; python -m coverage report
```

**Why Run Only Relevant Tests?**

- ✅ Faster feedback during development
- ✅ Focus on what you're changing
- ✅ Reduces context switching
- ✅ Full suite reserved for pre-commit validation

### Adding a New Feature

1. **Create test file** (if doesn't exist): `tests/test_<feature>.py`
2. **Write import test**: Verify module loads
3. **Write unit tests**: Test each function (TDD - write tests first!)
4. **Implement feature**: Write minimal code to pass tests
5. **Write integration tests**: Test feature with related components
6. **Run relevant test file(s)**: `python tests/test_<feature>.py`
7. **Refactor**: Improve code while keeping tests green
8. **Update documentation**: README, docstrings, etc.

### Fixing a Bug

1. **Create failing test**: Reproduce the bug in a test
2. **Verify test fails**: Confirms bug exists
3. **Fix the bug**: Minimal change to make test pass
4. **Run relevant test file(s)**: `python tests/test_<affected_module>.py`
5. **Add edge case tests**: Prevent similar bugs

### Before Committing

```bash
# Run only relevant test files for your changes
python tests/test_<module>.py
python tests/test_<related_module>.py

# Or run full test suite with coverage (only before major commits/PRs)
python -W ignore -m coverage run tests/run_all_tests.py; python -m coverage report
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
4. **Run relevant test file** - `python tests/test_<module>.py` - Should now show PASS (.)
5. **Refactor** - Improve while keeping tests green

**⚠️ CRITICAL: Test Naming Convention**

**DO NOT** use "TDD RED PHASE" or similar labels in test names/docstrings:

- ❌ **WRONG**: `"""TDD RED PHASE TEST: Verify session notes appear in UI"""`
- ✅ **CORRECT**: `"""Verify session notes appear in UI"""`

**Why**: Once the test passes, the "RED PHASE" label becomes misleading and causes confusion. The test name should describe WHAT it tests, not WHEN it was written.

**Use descriptive names that remain accurate throughout the test lifecycle**:

```python
def test_session_notes_displays_in_correct_column():
    """Verify session notes text appears in Session Notes column (column 13)."""
    # Test implementation...
```

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

### Testing Tkinter UI Components

**⚠️ CRITICAL: Known Tkinter Testing Limitations**

When writing tests for Tkinter UI components, be aware of these platform and environment limitations:

#### 🔴 MOST CRITICAL: Tkinter Test Teardown Pattern (ALWAYS USE THIS)

**Search keywords**: teardown, safe_teardown_tk_root, tkinter crashes, Tcl_AsyncDelete

**This is THE MOST IMPORTANT pattern - get this wrong and tests will crash intermittently!**

```python
class TestMyFeature(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        # ❌ DO NOT USE: self.addCleanup(self.root.destroy)

    def tearDown(self):
        """Clean up after tests"""
        from test_helpers import safe_teardown_tk_root
        safe_teardown_tk_root(self.root)  # ✅ REQUIRED!
        self.file_manager.cleanup()
```

**Why**: Tkinter widgets schedule `after()` callbacks that MUST be cancelled before destroying root, or you get "Tcl_AsyncDelete: async handler deleted by wrong thread" crashes.

**What safe_teardown_tk_root does**:

1. Cancels all pending `after()` callbacks
2. Quits the mainloop cleanly
3. Destroys the root window
4. Forces garbage collection to clean up tkinter variables
5. Suppresses all tearDown errors

**❌ WRONG PATTERNS (DO NOT USE)**:

```python
# ❌ WRONG #1: Using addCleanup
self.addCleanup(self.root.destroy)  # Causes crashes!

# ❌ WRONG #2: Manual try/except
def tearDown(self):
    try:
        self.root.destroy()  # Doesn't cancel callbacks!
    except:
        pass

# ❌ WRONG #3: Direct destroy
def tearDown(self):
    self.root.destroy()  # Will crash!
```

#### 1. StringVar/IntVar/BooleanVar Must Have Master Parameter

**Always specify the master parameter** when creating Tkinter variables:

```python
# ✅ CORRECT
self.status_filter = tk.StringVar(master=self.root, value="active")
range_var = tk.StringVar(master=self.root, value="default")

# In dialogs where dialog is a Toplevel
name_var = tk.StringVar(master=dialog, value="")

# ❌ WRONG - Attaches to global Tk singleton!
self.status_filter = tk.StringVar(value="active")  # Will cause crashes
```

**Why**: Without master, variables attach to global default Tk root, causing state pollution between tests and "Tcl_AsyncDelete" crashes.

#### 2. Geometry Manager Mixing

**Never mix `pack()` and `grid()` in the same container**:

```python
# ❌ WRONG - Causes TclError
label = tk.Label(frame, text="Test")
label.pack()
button = tk.Button(frame, text="Click")
button.grid(row=0, column=0)  # TclError: cannot use geometry manager grid

# ✅ CORRECT - Use one geometry manager per container
label.pack()
button.pack()
```

#### 3. Widget Width in Headless Tests

**Use `winfo_reqwidth()` instead of `winfo_width()` in tests**:

```python
# ❌ WRONG - Returns 1 in headless tests
actual_width = widget.winfo_width()  # Returns 1px before window is drawn

# ✅ CORRECT - Returns requested width based on content
actual_width = widget.winfo_reqwidth()  # Works in headless tests
```

**Why**: `winfo_width()` returns actual rendered width (requires window to be drawn), `winfo_reqwidth()` returns requested/calculated width (works without drawing).

#### 4. Text vs Label Widgets

**Comment columns use `tk.Text` widgets, not `tk.Label`**:

```python
# When accessing timeline row children:

# ❌ WRONG - Filters out Text widgets
row_labels = [w for w in row.winfo_children() if isinstance(w, tk.Label)]
comment_widget = row_labels[8]  # IndexError! Comment columns are Text widgets

# ✅ CORRECT - Get all widgets and handle both types
row_widgets = list(row.winfo_children())
widget = row_widgets[8]
if isinstance(widget, tk.Text):
    text = widget.get("1.0", "end-1c")  # Text uses get() method
else:
    text = widget.cget("text")  # Label uses cget()
```

**Why**: Text widgets support word-wrapping for long comments; Label widgets don't wrap.

#### 5. Configuration vs Rendered Width

**Understand the difference between configured and rendered dimensions**:

```python
# Configuration (what you set)
label.config(width=20)  # 20 character units
width_chars = label.cget("width")  # Returns 20

# Rendered dimensions (actual pixels)
width_pixels = label.winfo_reqwidth()  # Returns pixel width based on font

# ✅ Test both when alignment matters
self.assertEqual(header.cget("width"), data.cget("width"))  # Config match
self.assertEqual(header.winfo_reqwidth(), data.winfo_reqwidth())  # Pixel match
```

#### 6. Optional Dependencies Pattern

**For tests requiring optional libraries (Google Sheets, etc.)**:

```python
# Check if optional module can be imported
OPTIONAL_AVAILABLE = False
try:
    from src import optional_module
    OPTIONAL_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    pass

# Skip test class if dependency not available
@unittest.skipIf(not OPTIONAL_AVAILABLE, "Optional dependency not installed")
class TestOptionalFeature(unittest.TestCase):
    # Tests using @patch('src.optional_module.method')
    ...
```

**Why**: `@patch` decorators are evaluated at import time. If the module imports fail, you get AttributeError before skipIf can run.

### Common Tkinter Testing Patterns

```python
# Pattern: Test widget existence
def test_widget_exists(self):
    # Create UI component
    frame = MyFrame(self.root, tracker_mock)
    # Access widget
    self.assertIsNotNone(frame.my_button)
    self.assertIsInstance(frame.my_button, tk.Button)

# Pattern: Test widget configuration
def test_widget_text(self):
    frame = MyFrame(self.root, tracker_mock)
    actual_text = frame.label.cget("text")
    self.assertEqual(actual_text, "Expected Text")

# Pattern: Test callback binding
def test_button_callback(self):
    frame = MyFrame(self.root, tracker_mock)
    frame.button.invoke()  # Trigger button click
    tracker_mock.some_method.assert_called_once()

# Pattern: Test StringVar value
def test_variable_value(self):
    frame = MyFrame(self.root, tracker_mock)
    self.assertEqual(frame.status_var.get(), "active")

# Pattern: Test widget dimensions (headless-safe)
def test_widget_width(self):
    frame = MyFrame(self.root, tracker_mock)
    # Use winfo_reqwidth for headless tests
    actual_width = frame.widget.winfo_reqwidth()
    expected_width = 200
    self.assertGreater(actual_width, expected_width)
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
- **Test credentials**: `tests/credentials.json` and `tests/token.pickle` exist for Google Sheets integration tests but are gitignored

**⚠️ IMPORTANT: Test Google Sheets Files**

The `tests/` directory contains duplicate Google Sheets authentication files:

- `tests/credentials.json` - OAuth credentials for test Google Sheets
- `tests/token.pickle` - Saved authentication token for tests

These files are:

- Required for Google Sheets integration tests to pass
- Located in `tests/` directory (NOT root)
- Excluded from git via `.gitignore`
- Must exist for `test_google_sheets.py` to authenticate

**Running Google Sheets Tests**:

```bash
# Must run from tests directory or with proper path
cd tests
python test_google_sheets.py

# Or from root with proper venv
.venv\Scripts\python.exe -m unittest tests.test_google_sheets
```

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
