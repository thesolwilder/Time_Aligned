# Failing Tests Summary

## Error Categories

### 1. Google Sheets Integration Errors (21 errors)

**File:** `tests/test_google_sheets.py`
**Issue:** Missing 'google' module and import path issues

- All tests in TestEscapeForSheets (9 tests)
- All tests in TestGoogleSheetsIntegration (7 tests)
- All tests in TestGoogleSheetsReadOnly (2 tests)
- All tests in TestGoogleSheetsTestConnection (1 test)
- All tests in TestGoogleSheetsUploadSession (2 tests)

**Root Cause:** Import statement needs fixing - should use `from src.google_sheets_integration import ...`

### 2. Settings Frame KeyError Issues (17 errors)

**File:** `tests/test_settings_frame.py`
**Issue:** KeyError accessing test data items that don't exist

- TestSettingsFrameArchiveActivate (8 tests)
- TestSettingsFrameDefaults (2 tests)
- TestSettingsFrameOnlyOneDefault (3 tests)
- TestSettingsFrameSphereArchiveCascade (3 tests)

**Root Cause:** Test data setup is incorrect - items referenced in tests don't exist in test data

### 3. IndexError in Completion Tests (7 errors)

**Files:**

- `tests/test_completion_dropdowns.py` (2 errors)
- `tests/test_completion_priority.py` (5 errors)

**Issue:** `IndexError: list index out of range`
**Root Cause:** Likely accessing timeline widgets that don't exist - needs `root.update()` after widget creation

### 4. Analysis Frame Calculation Failures (5 failures)

**Files:**

- `tests/test_analysis_calculations.py` (2 failures)
- `tests/test_analysis_priority.py` (3 failures)

**Issue:** All calculations returning 0 instead of expected values
**Root Cause:** Analysis frame not properly initialized - needs `root.update()` or data not loading

### 5. Completion Frame Display Failures (4 failures)

**File:** `tests/test_completion_frame_comprehensive.py` (3 failures)
**File:** `tests/test_completion_dropdowns.py` (1 failure)

**Issue:** Widget values returning 0 or None
**Root Cause:** Frames not fully rendered - needs `root.update()` after frame creation

### 6. Settings Frame Display Failures (12 failures)

**File:** `tests/test_settings_frame.py`

**Issue:** Filters and defaults not working correctly
**Root Cause:** Settings frame widgets not fully initialized - needs `root.update()`

## Files Requiring Manual Review (in priority order)

1. **tests/test_google_sheets.py** - 21 errors (import issues)
2. **tests/test_settings_frame.py** - 29 errors+failures (test data + widget initialization)
3. **tests/test_completion_priority.py** - 5 errors (IndexError)
4. **tests/test_analysis_calculations.py** - 2 failures (calculation issues)
5. **tests/test_analysis_priority.py** - 3 failures (calculation issues)
6. **tests/test_completion_frame_comprehensive.py** - 3 failures (widget initialization)
7. **tests/test_completion_dropdowns.py** - 3 errors (IndexError)

## Solution Strategy

### For tkinter "RuntimeError: main thread is not in main loop" and IndexErrors:

Add `self.root.update()` after creating frames/widgets in test setUp or before assertions:

```python
frame = CompletionFrame(self.root, tracker, session_name)
self.root.update()  # Allow widgets to fully initialize
# Now run assertions
```

### For Google Sheets imports:

Fix import in test_google_sheets.py:

```python
from src.google_sheets_integration import GoogleSheetsUploader
```

### For Settings Frame test data issues:

Fix test setUp methods to create the data that tests expect to exist.

## Skipped Tests (9)

The 9 skipped tests are intentionally skipped - likely tests requiring:

- External dependencies (Google Sheets API)
- Manual interaction
- Specific system configurations
- Feature flags not enabled

To see which tests are skipped, run:

```bash
python -m unittest discover -s tests -p "test_*.py" -v 2>&1 | Select-String "skipped"
```
