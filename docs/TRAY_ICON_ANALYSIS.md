# System Tray Icon Analysis

## Issue

System tray icon appears multiple times when the app is run multiple times.

## Current Implementation

The tray icon is created in [time_tracker.py](time_tracker.py#L1110) in the `setup_tray_icon()` method:

```python
def setup_tray_icon(self):
    """Set up system tray icon with menu"""

    def run_tray():
        # ... icon menu setup ...
        self.tray_icon = pystray.Icon(
            "Time Tracker",
            icon=create_colored_icon(),
            menu=menu
        )
        self.tray_icon.run()  # Blocking call

    # Start tray in daemon thread
    tray_thread = threading.Thread(target=run_tray, daemon=True)
    tray_thread.start()
```

Called from `__init__`:

```python
def __init__(self, root):
    # ... other initialization ...
    self.setup_tray_icon()
```

## Cleanup Implementation

The [on_closing()](time_tracker.py#L1280) method properly stops the tray icon:

```python
def on_closing(self):
    if self.session_active:
        if messagebox.askyesno("Confirm", "Are you sure you want to quit?"):
            if self.tray_icon:
                self.tray_icon.stop()  # ✓ Properly stops tray icon
            self.root.destroy()
    else:
        if self.tray_icon:
            self.tray_icon.stop()  # ✓ Properly stops tray icon
        self.root.destroy()
```

## Why Multiple Icons Appear

The issue occurs when:

1. **Window is hidden (not closed)**: When hiding to system tray, `on_closing()` is NOT called, so the tray icon remains running
2. **App is run again**: A new TimeTracker instance is created with a new tray icon
3. **Result**: Multiple tray icons accumulate in the system tray

## Detection

The current code has **no check** for existing tray icons before creating a new one:

```python
# ❌ No check before creating icon
def setup_tray_icon(self):
    # Directly creates new icon
    self.tray_icon = pystray.Icon(...)
```

## Solution Options

### Option 1: Prevent Multiple Instances (Recommended)

Use a lock file or mutex to ensure only one instance of the app runs at a time:

```python
import sys
import os

class TimeTracker:
    def __init__(self, root):
        # Check for existing instance
        lock_file = "time_tracker.lock"
        if os.path.exists(lock_file):
            messagebox.showerror(
                "Already Running",
                "Time Tracker is already running. Check system tray."
            )
            sys.exit(0)

        # Create lock file
        with open(lock_file, "w") as f:
            f.write(str(os.getpid()))

        # ... rest of initialization ...

    def on_closing(self):
        # Remove lock file on exit
        if os.path.exists("time_tracker.lock"):
            os.remove("time_tracker.lock")

        # ... existing cleanup ...
```

### Option 2: Check Before Creating Icon

Add a check before setting up tray icon:

```python
def setup_tray_icon(self):
    # Don't create if already exists
    if hasattr(self, 'tray_icon') and self.tray_icon:
        return

    # ... create icon as before ...
```

### Option 3: Single-Instance Library

Use a library like `tendo.singleton` to enforce single instance:

```python
from tendo import singleton

class TimeTracker:
    def __init__(self, root):
        try:
            self.single_instance = singleton.SingleInstance()
        except singleton.SingleInstanceException:
            messagebox.showerror(
                "Already Running",
                "Time Tracker is already running."
            )
            sys.exit(0)

        # ... rest of initialization ...
```

## Recommended Fix

**Option 1** is recommended because:

- ✓ Prevents all duplicate resource issues (not just tray icon)
- ✓ Provides clear user feedback
- ✓ Simple to implement without additional dependencies
- ✓ Cleans up lock file on normal exit

## Testing

After implementing fix, verify:

1. App shows error when attempting second launch
2. Tray icon appears only once
3. Lock file is created on launch
4. Lock file is removed on proper exit
5. Stale lock file doesn't prevent restart after crash

## Current Test Coverage

The new [test_google_sheets.py](tests/test_google_sheets.py) includes 13 tests:

- ✓ 5 passing: Google Sheets settings structure tests
- ✓ 7 skipped: Tests requiring Google API libraries (expected)
- ✓ 1 passing: Upload method existence test

All tests handle missing Google API dependencies gracefully.
