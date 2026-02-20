# Testing Guide for Time Tracker

This document explains how to run tests and what each test suite validates.

**Test coverage: 83% across core application modules.**

## Quick Start

### Run All Tests

```bash
python tests/run_all_tests.py
```

### Run Specific Test File

```bash
python tests/run_all_tests.py test_time_tracking
```

### Run With Verbose Output

```bash
python tests/run_all_tests.py -v
```

### View Test Categories

```bash
python tests/run_all_tests.py --help
```

## Test Structure

### Test Files Overview

1. **test_helpers.py** - Testing utilities and mock objects
   - MockTime: Control time progression in tests
   - TestDataGenerator: Create test sessions and settings
   - TestFileManager: Automatic test file cleanup
   - MockScreenshot: Mock screenshot capture

2. **test_time_tracking.py** - Time recording accuracy
3. **test_backup.py** - Backup save and crash recovery
4. **test_analysis.py** - Analysis filtering and aggregation
5. **test_analysis_calculations.py** - Duration calculation accuracy
6. **test_analysis_card_filters.py** - Filter card behaviour
7. **test_analysis_card_status_filter.py** - Active/archived status filter on summary cards
8. **test_analysis_csv_percentage.py** - CSV export percentage fields for multi-project/action periods
9. **test_analysis_navigation_bug.py** - Navigation regression tests
10. **test_analysis_performance.py** - Performance benchmarks
11. **test_analysis_pie_chart.py** - Pie chart data accuracy
12. **test_analysis_priority.py** - Priority sort logic
13. **test_analysis_timeline.py** - Timeline rendering
14. **test_analysis_load_more.py** - Paginated loading
15. **test_screenshots.py** - Screenshot timing and capture
16. **test_settings.py** - Settings persistence and defaults
17. **test_settings_frame.py** - Settings UI behaviour
18. **test_idle_tracking.py** - Idle detection and period recording
19. **test_active_after_idle.py** - State transitions after idle
20. **test_breaks.py** - Break period tracking
21. **test_button_navigation.py** - UI navigation
22. **test_completion_frame.py** - Session completion interface
23. **test_completion_frame_comprehensive.py** - Full completion frame coverage
24. **test_completion_frame_rename_bug.py** - Rename regression test
25. **test_completion_dropdowns.py** - Dropdown population and selection
26. **test_completion_comments_populate.py** - Comment field population
27. **test_completion_priority.py** - Priority field in completion
28. **test_completion_skip_bug.py** - Skip behaviour regression
29. **test_csv_export.py** - CSV export correctness
30. **test_csv_export_integration.py** - CSV export integration
31. **test_csv_export_imports.py** - CSV import handling
32. **test_sanitization.py** - Input sanitization and security
33. **test_ui_helpers.py** - UI utility functions and security helpers
34. **test_google_sheets.py** - Google Sheets integration and validation
35. **test_data_integrity.py** - Data structure validation
36. **test_error_handling.py** - Error and edge case handling
37. **test_navigation.py** - Frame navigation
38. **test_add_project_duplicate_bug.py** - Duplicate project name conflict regression
39. **test_secondary_project_bug.py** - Secondary project regression
40. **test_inactive_project_completion.py** - Archived project handling
41. **test_interleaved_periods_secondary_dropdown.py** - Secondary dropdown in interleaved periods
42. **test_spreadsheet_url_extraction.py** - Spreadsheet ID extraction

## Data Accuracy Priorities

### ✓ Time Recording Accuracy

All duration calculations validated to within 1 second tolerance. Tests verify:

- Start/end timestamps are accurate
- Durations match elapsed time
- Multiple periods don't overlap

### ✓ Backup Saves

Backup mechanism tested to ensure:

- Saves occur every 60 seconds (600 × 100ms iterations)
- Data persists correctly
- Sessions recoverable after crash

### ✓ Analysis Filtering

Date range calculations verified for:

- All filter types (Last 7/14/30 days, This Week, etc.)
- Correct session inclusion/exclusion
- Accurate aggregation of totals

### ✓ Screenshot Timing

Screenshot timing logic validated:

- Minimum time between captures enforced
- Window/process change detection
- Settings respected (enabled/disabled)

### ✓ Idle Detection

Idle tracking verified:

- Threshold detection works
- Periods recorded with start/end times
- Multiple idle periods handled

### ✓ Default Settings

Settings retrieval tested:

- Default sphere retrieved correctly
- Default projects for spheres
- Fallback to first active item

## Test Design Principles

### Mocking

Tests use mocking to:

- Control time progression (MockTime)
- Avoid expensive operations (screenshot capture)
- Ensure deterministic results

### Cleanup

All tests automatically clean up:

- Test files removed in tearDown()
- No pollution of user data
- Temporary directories cleaned

### Isolation

Each test is independent:

- Fresh test data for each test
- No shared state between tests
- Can run in any order

## Running Individual Tests

### By Test Class

```bash
python -m unittest tests.test_time_tracking.TestTimeTrackingAccuracy
```

### By Test Method

```bash
python -m unittest tests.test_time_tracking.TestTimeTrackingAccuracy.test_session_start_creates_accurate_timestamp
```

### By Test File

```bash
python -m unittest tests.test_backup
```

## Test Output

### Success

```
======================================================================
TIME TRACKER TEST SUITE
======================================================================

Ran 45 tests in 2.354s

OK

======================================================================
TEST SUMMARY
======================================================================
Tests run: 45
Successes: 45
Failures: 0
Errors: 0
Skipped: 0
======================================================================
```

### Failure

When tests fail, you'll see:

- Which test failed
- Expected vs actual values
- Stack trace for debugging

## Adding New Tests

1. Create test file in `tests/` directory (must start with `test_`)
2. Import `unittest`, `tkinter`, and `test_helpers`
3. Add `sys.path.insert` to ensure imports resolve from the project root
4. Create TestCase class
5. Add `setUp()` — create `tk.Tk()` root + `TestFileManager`, register `addCleanup`
6. Add `tearDown()` — call `safe_teardown_tk_root` **then** `file_manager.cleanup()`
7. Write test methods (must start with `test_`)
8. Use assertions to verify behavior

> ⚠️ **Tkinter note**: Always use `safe_teardown_tk_root()` to destroy the tk root. Never use `self.addCleanup(self.root.destroy)` — it causes crashes in the test suite.

Example:

```python
import unittest
import tkinter as tk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from test_helpers import TestFileManager, TestDataGenerator, safe_teardown_tk_root


class TestNewFeature(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        # ❌ DO NOT USE: self.addCleanup(self.root.destroy)

        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file("test_data.json")

    def tearDown(self):
        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_feature_works(self):
        # Arrange
        # Act
        # Assert
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
```

## Continuous Testing

Tests are designed to run quickly so you can:

- Run after every code change
- Run before committing code
- Run in CI/CD pipeline

## Troubleshooting

### Tests fail to import modules

Ensure you're running from the project root:

```bash
cd c:\Users\theso\Documents\Coding_Projects\time_aligned
python tests/run_all_tests.py
```

### Test files not cleaned up

Check tearDown() methods are being called. Use try/finally if needed.

### Timing-sensitive tests fail

Some tests use real time.time() - increase tolerance in assert_duration_accurate() if needed.

## Best Practices

1. **Always clean up test data** - Use TestFileManager
2. **Use mocks for expensive operations** - Screenshots, network calls
3. **Test edge cases** - Empty data, very long sessions, etc.
4. **Keep tests fast** - Use mocks, avoid sleeps
5. **Test one thing per test** - Easier to debug failures
6. **Use descriptive test names** - Explain what is being tested
