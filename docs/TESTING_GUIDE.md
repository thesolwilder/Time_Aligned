# Testing Guide for Time Tracker

This document explains how to run tests and what each test suite validates.

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
   - ✓ Session start creates accurate timestamp
   - ✓ Active period duration calculations
   - ✓ Break period duration calculations
   - ✓ Multiple active periods recorded separately
   - ✓ Timestamp chronological ordering
   - ✓ Session data structure validation
   - ✓ Edge cases (very short/long sessions)

3. **test_backup.py** - Backup save functionality
   - ✓ Backup saves occur every 600 iterations (60 seconds)
   - ✓ Backup preserves all session data
   - ✓ Backup updates duration fields
   - ✓ Crash recovery from backup
   - ✓ Backup handles sessions with breaks
   - ✓ Multiple backups don't corrupt data

4. **test_analysis.py** - Analysis filtering accuracy
   - ✓ Date range filters (Last 7/14/30 days, This Week, etc.)
   - ✓ Sphere filtering
   - ✓ Project filtering within sphere
   - ✓ Aggregate totals calculation
   - ✓ Sessions outside date range excluded
   - ✓ "All Time" includes all sessions

5. **test_screenshots.py** - Screenshot timing
   - ✓ min_seconds_between_captures enforced
   - ✓ Screenshot on window change
   - ✓ No screenshot on same window
   - ✓ Process change triggers screenshot
   - ✓ Screenshot folder structure correct
   - ✓ Metadata includes timestamp
   - ✓ Settings can disable screenshots

6. **test_settings.py** - Default sphere and projects
   - ✓ Get default sphere
   - ✓ Fallback to first active sphere
   - ✓ Set default sphere
   - ✓ Get default project for sphere
   - ✓ Projects filtered by sphere
   - ✓ Settings persistence
   - ✓ Only active spheres shown

7. **test_idle_tracking.py** - Idle detection
   - ✓ Idle period recorded on activity before auto-break
   - ✓ Multiple idle periods tracked
   - ✓ Idle data structure validation

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
2. Import unittest and test_helpers
3. Create TestCase class
4. Add setUp() for test fixtures
5. Add tearDown() for cleanup
6. Write test methods (must start with `test_`)
7. Use assertions to verify behavior

Example:

```python
import unittest
from test_helpers import TestFileManager

class TestNewFeature(unittest.TestCase):
    def setUp(self):
        self.file_manager = TestFileManager()
        # Setup code

    def tearDown(self):
        self.file_manager.cleanup()

    def test_feature_works(self):
        # Arrange
        # Act
        # Assert
        self.assertEqual(expected, actual)
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
