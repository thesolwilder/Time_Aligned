# Files with Errors/Failures - Manual Review List

## Priority 1: Tkinter Widget Initialization (needs root.update())

### tests/test_completion_dropdowns.py

- **Errors**: 2 (IndexError: list index out of range)
- **Tests**:
  - test_comments_are_saved
  - test_dangerous_characters_handled_in_comments
- **Fix**: Add `self.root.update()` after `CompletionFrame()` creation

### tests/test_completion_priority.py

- **Errors**: 5 (IndexError: list index out of range)
- **Tests**:
  - test_toggle_shows_secondary_widgets
  - test_comment_with_quotes
  - test_multiple_periods_with_different_secondaries
  - test_percentage_split_50_50
  - test_save_single_project_writes_correctly
- **Fix**: Add `self.root.update()` after `CompletionFrame()` creation

### tests/test_completion_frame_comprehensive.py

- **Failures**: 3 (Assertions failing - values are 0/None instead of expected)
- **Tests**:
  - test_no_zero_duration_active_period_after_break
  - test_active_duration_sum_matches_display
  - test_shows_last_active_session
- **Fix**: Add `self.root.update()` after `CompletionFrame()` creation

### tests/test_analysis_calculations.py

- **Failures**: 2 (Calculations returning 0)
- **Tests**:
  - test_last_7_days_filter
  - test_total_duration_equals_sum_of_sessions
- **Fix**: Add `self.root.update()` after `AnalysisFrame()` creation

### tests/test_analysis_priority.py

- **Failures**: 3 (Calculations returning 0)
- **Tests**:
  - test_csv_export_creates_file
  - test_secondary_projects_aggregated_correctly
  - test_session_assigned_to_start_date
- **Fix**: Add `self.root.update()` after `AnalysisFrame()` creation

### tests/test_settings_frame.py

- **Errors**: 17 (KeyError accessing non-existent test data)
- **Failures**: 12 (Filters/defaults not working)
- **Total**: 29 issues
- **Fix Strategy**:
  1. Add `self.root.update()` after `SettingsFrame()` creation
  2. Fix test data to match what tests expect (e.g., 'ActiveSphere' vs 'Coding')

## Priority 2: External Dependencies (Not Reorganization Related)

### tests/test_google_sheets.py

- **Errors**: 21 (ModuleNotFoundError: No module named 'google')
- **Root Cause**: Missing google-api-python-client package
- **Fix**: Install dependencies OR tests will correctly skip
- **Not urgent**: These tests work correctly when dependencies are available

## Quick Test Command Reference

```powershell
# Test single file:
python -m unittest tests.test_completion_dropdowns -v

# Test specific class:
python -m unittest tests.test_completion_dropdowns.TestCompletionFrameSphereDropdownBehavior -v

# Test multiple files (only the failing ones):
python -m unittest tests.test_completion_dropdowns tests.test_completion_priority tests.test_completion_frame_comprehensive tests.test_analysis_calculations tests.test_analysis_priority tests.test_settings_frame -v 2>&1 | Select-Object -Last 5

# Count errors/failures only:
python -m unittest tests.test_completion_dropdowns tests.test_completion_priority tests.test_completion_frame_comprehensive tests.test_analysis_calculations tests.test_analysis_priority tests.test_settings_frame 2>&1 | Select-String "Ran|FAILED|OK"
```

## Summary Statistics

### Total Issues: 64

- **Tkinter initialization (fixable)**: 31
  - IndexError: 7
  - Assertion failures (0/None values): 8
  - KeyError (test data): 17
  - Filter/display failures: 12
- **External dependencies (expected)**: 21
  - Google Sheets API module missing: 21

- **Skipped (intentional)**: 9
  - Google Sheets feature tests: 8
  - Frame import issue: 1

### Time Estimate

- Fix tkinter issues: 30-45 minutes (systematic edits)
- Fix test data issues: 15-20 minutes
- **Total**: ~1 hour of focused work

All issues follow predictable patterns and are straightforward to fix!
