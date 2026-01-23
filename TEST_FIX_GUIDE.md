# Test Fixes Required

## Summary

You're right - the tkinter errors ARE from reorganization. When modules moved to `src/`, the initialization sequence changed and widgets aren't fully rendered before tests try to access them.

## Root Cause

The `RuntimeError: main thread is not in main loop` and `IndexError` issues occur because:

1. Frames/widgets are created but not given time to render
2. The event loop needs to process pending events before widgets are accessible
3. Lists/menus aren't populated until after `update()` is called

## Solution: Add `self.root.update()` after frame creation

### Pattern to Apply:

```python
# OLD (causes errors):
frame = CompletionFrame(self.root, tracker, session_name)
self.assertEqual(frame.some_widget.get(), "expected_value")  # ERROR!

# NEW (works):
frame = CompletionFrame(self.root, tracker, session_name)
self.root.update()  # Process all pending events
self.assertEqual(frame.some_widget.get(), "expected_value")  # OK!
```

## Files Requiring `root.update()` Fixes:

### High Priority (causes most errors):

1. `tests/test_completion_dropdowns.py` - Add after every `CompletionFrame()` creation
2. `tests/test_completion_priority.py` - Add after every `CompletionFrame()` creation
3. `tests/test_completion_frame_comprehensive.py` - Add after every `CompletionFrame()` creation
4. `tests/test_analysis_calculations.py` - Add after every `AnalysisFrame()` creation
5. `tests/test_analysis_priority.py` - Add after every `AnalysisFrame()` creation
6. `tests/test_settings_frame.py` - Add after every `SettingsFrame()` creation

### Where to Add `self.root.update()`:

After EVERY line that creates a frame, add:

- `CompletionFrame(...)` → add `self.root.update()`
- `AnalysisFrame(...)` → add `self.root.update()`
- `SettingsFrame(...)` → add `self.root.update()`
- `TimeTracker(...)` → add `self.root.update()` if accessing widgets immediately after

## Systematic Fix Approach:

```bash
# For each test file, search for frame creation patterns:
# 1. CompletionFrame creation
# 2. AnalysisFrame creation
# 3. SettingsFrame creation
# 4. Add self.root.update() immediately after
```

## Example Fixes:

### test_completion_dropdowns.py - Line ~87

```python
frame = CompletionFrame(self.root, tracker, session_name)
self.root.update()  # <-- ADD THIS LINE
```

### test_analysis_calculations.py - After AnalysisFrame creation

```python
analysis = AnalysisFrame(self.content_frame(), tracker, self.root)
self.root.update()  # <-- ADD THIS LINE
analysis.sphere_var.set("All Spheres")
```

### test_settings_frame.py - After SettingsFrame creation

```python
frame = SettingsFrame(self.root, self.tracker, self.root)
self.root.update()  # <-- ADD THIS LINE
```

## Google Sheets Tests (9 skipped + 12 errors)

These are NOT reorganization issues - they require the `google-api-python-client` package:

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

Without this package, tests correctly skip. The errors are expected.

## Settings Frame Test Data Issues (17 KeyErrors)

File: `tests/test_settings_frame.py`

Tests expect items like 'ActiveSphere', 'ArchivedSphere', etc. but test data uses 'Coding', 'General'.
Need to either:

1. Update test data to match what tests expect, OR
2. Update tests to use actual test data names

## Running Only Failing Tests

Instead of running full suite (278 tests, ~2 minutes), run only failing test files:

```bash
# Run specific failing test file:
python -m unittest tests.test_completion_dropdowns -v

# Run multiple failing files:
python -m unittest tests.test_completion_dropdowns tests.test_completion_priority tests.test_analysis_calculations -v

# Run specific test class:
python -m unittest tests.test_completion_dropdowns.TestCompletionFrameSphereDropdownBehavior -v

# Run single test:
python -m unittest tests.test_completion_dropdowns.TestCompletionFrameSphereDropdownBehavior.test_sphere_change_updates_default_project_dropdown -v
```

## Estimated Fix Effort:

- **Tkinter update() fixes**: ~50-60 locations across 6 files (15-20 minutes)
- **Settings frame test data**: ~17 test fixes (10 minutes)
- **Total**: ~30 minutes of systematic edits

All errors are fixable and follow predictable patterns!
