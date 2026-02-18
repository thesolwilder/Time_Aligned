"""
Test Helpers and Utilities for Time Tracker Testing

Provides mock objects, test data generators, and helper functions
for testing time tracking, screenshots, and data persistence.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import json
import os
import time
from datetime import datetime, timedelta


class MockTime:
    """Mock time object for controlling time progression in tests"""

    def __init__(self, initial_time=None):
        """
        Initialize mock time

        Args:
            initial_time: Unix timestamp to start at (default: 2026-01-20 12:00:00)
        """
        if initial_time is None:
            # Fixed timestamp: 2026-01-20 12:00:00
            initial_time = 1737374400.0
        self.current_time = initial_time

    def time(self):
        """Return current mock time"""
        return self.current_time

    def advance(self, seconds):
        """Advance time by given seconds"""
        self.current_time += seconds
        return self.current_time

    def strftime(self, format_str):
        """Format current time"""
        return time.strftime(format_str, time.localtime(self.current_time))

    def reset(self, new_time=None):
        """Reset time to initial or specified value"""
        if new_time is None:
            new_time = 1737374400.0
        self.current_time = new_time


class TestDataGenerator:
    """Generate test data for sessions, periods, and settings"""

    @staticmethod
    def create_session_data(
        sphere="TestSphere",
        date="2026-01-20",
        start_timestamp=1737374400.0,
        num_active=2,
        num_breaks=1,
    ):
        """
        Create a complete session data structure

        Args:
            sphere: Sphere name
            date: Date string YYYY-MM-DD
            start_timestamp: Session start timestamp
            num_active: Number of active periods to create
            num_breaks: Number of break periods to create

        Returns:
            Dict with session data structure matching data.json format
        """
        session_name = f"{date}_{int(start_timestamp)}"
        current_time = start_timestamp

        active_periods = []
        break_periods = []

        # Create active periods
        for i in range(num_active):
            period_start = current_time
            period_duration = 300.0  # 5 minutes
            period_end = period_start + period_duration

            active_periods.append(
                {
                    "start": time.strftime("%H:%M:%S", time.localtime(period_start)),
                    "start_timestamp": period_start,
                    "end": time.strftime("%H:%M:%S", time.localtime(period_end)),
                    "end_timestamp": period_end,
                    "duration": period_duration,
                    "project": f"TestProject{i}",
                    "comment": f"Test comment {i}",
                }
            )
            current_time = period_end

            # Add break after each active period (except last if no more breaks)
            if i < num_breaks:
                break_start = current_time
                break_duration = 60.0  # 1 minute
                break_end = break_start + break_duration

                break_periods.append(
                    {
                        "start": time.strftime("%H:%M:%S", time.localtime(break_start)),
                        "start_timestamp": break_start,
                        "end": time.strftime("%H:%M:%S", time.localtime(break_end)),
                        "end_timestamp": break_end,
                        "duration": break_duration,
                        "action": "Resting",
                        "comment": "",
                    }
                )
                current_time = break_end

        # Calculate totals
        total_active = sum(p["duration"] for p in active_periods)
        total_break = sum(p["duration"] for p in break_periods)
        total_duration = total_active + total_break

        return {
            session_name: {
                "sphere": sphere,
                "date": date,
                "start_time": time.strftime(
                    "%H:%M:%S", time.localtime(start_timestamp)
                ),
                "start_timestamp": start_timestamp,
                "active": active_periods,
                "breaks": break_periods,
                "idle_periods": [],
                "end_time": time.strftime("%H:%M:%S", time.localtime(current_time)),
                "end_timestamp": current_time,
                "total_duration": total_duration,
                "active_duration": total_active,
                "break_duration": total_break,
            }
        }

    @staticmethod
    def create_settings_data(default_sphere="Coding", default_project="TestProject"):
        """
        Create settings data structure

        Returns:
            Dict matching settings.json format
        """
        return {
            "idle_settings": {
                "idle_threshold": 60,
                "idle_break_threshold": 300,
                "idle_tracking_enabled": True,
            },
            "screenshot_settings": {
                "enabled": True,
                "capture_on_focus_change": True,
                "min_seconds_between_captures": 5,
                "screenshot_path": "tests/screenshots",
            },
            "spheres": {
                default_sphere: {"is_default": True, "active": True},
                "General": {"is_default": False, "active": True},
            },
            "projects": {
                default_project: {
                    "sphere": default_sphere,
                    "is_default": True,
                    "active": True,
                    "note": "",
                    "goal": "",
                },
                "OtherProject": {
                    "sphere": default_sphere,
                    "is_default": False,
                    "active": True,
                    "note": "",
                    "goal": "",
                },
            },
            "break_actions": {
                "bathroom": {"is_default": True, "active": True, "notes": ""}
            },
            "analysis_settings": {
                "card_ranges": ["Last 7 Days", "Last 14 Days", "All Time"]
            },
        }

    @staticmethod
    def create_test_data_with_n_periods(n_periods):
        """
        Create test data with exactly N periods for testing pagination/load more.

        Distributes periods across multiple sessions/days to create realistic data.

        Args:
            n_periods: Total number of periods to create

        Returns:
            Dict with data.json structure containing N total periods
        """
        import random
        from datetime import datetime, timedelta

        all_data = {}
        base_date = datetime(2026, 1, 1)
        periods_created = 0
        session_counter = 0

        # Create sessions with varying numbers of periods until we reach n_periods
        while periods_created < n_periods:
            # Each session has 3-10 periods
            periods_this_session = min(
                random.randint(3, 10), n_periods - periods_created
            )

            # Distribute across different days
            days_offset = session_counter // 3  # ~3 sessions per day
            current_date = base_date + timedelta(days=days_offset)
            date_str = current_date.strftime("%Y-%m-%d")

            # Create session timestamp
            hour = 8 + ((session_counter % 3) * 4)  # 8am, 12pm, 4pm
            start_dt = current_date.replace(hour=hour, minute=0, second=0)
            start_timestamp = start_dt.timestamp()

            session_name = f"{date_str}_{int(start_timestamp)}"

            # Create periods for this session
            active_periods = []
            break_periods = []
            current_time = start_timestamp

            # Split periods between active and breaks (roughly 2:1 ratio)
            num_active = int(periods_this_session * 0.66)
            num_breaks = periods_this_session - num_active

            # Create active periods
            for i in range(num_active):
                period_start = current_time
                duration = random.randint(300, 1800)  # 5-30 minutes
                period_end = period_start + duration

                active_periods.append(
                    {
                        "start": datetime.fromtimestamp(period_start).strftime(
                            "%H:%M:%S"
                        ),
                        "start_timestamp": period_start,
                        "end": datetime.fromtimestamp(period_end).strftime("%H:%M:%S"),
                        "end_timestamp": period_end,
                        "duration": duration,
                        "project": f"Project{(periods_created + i) % 5}",
                        "comment": f"Period {periods_created + i + 1}",
                    }
                )
                current_time = period_end

            # Create break periods
            for i in range(num_breaks):
                period_start = current_time
                duration = random.randint(120, 600)  # 2-10 minutes
                period_end = period_start + duration

                break_periods.append(
                    {
                        "start": datetime.fromtimestamp(period_start).strftime(
                            "%H:%M:%S"
                        ),
                        "start_timestamp": period_start,
                        "end": datetime.fromtimestamp(period_end).strftime("%H:%M:%S"),
                        "end_timestamp": period_end,
                        "duration": duration,
                        "action": "Resting",
                        "comment": "",
                    }
                )
                current_time = period_end

            # Calculate totals
            total_active = sum(p["duration"] for p in active_periods)
            total_break = sum(p["duration"] for p in break_periods)

            all_data[session_name] = {
                "sphere": f"Sphere{session_counter % 3}",  # Rotate through 3 spheres
                "date": date_str,
                "start_time": datetime.fromtimestamp(start_timestamp).strftime(
                    "%H:%M:%S"
                ),
                "start_timestamp": start_timestamp,
                "active": active_periods,
                "breaks": break_periods,
                "idle_periods": [],
                "end_time": datetime.fromtimestamp(current_time).strftime("%H:%M:%S"),
                "end_timestamp": current_time,
                "total_duration": current_time - start_timestamp,
                "active_duration": total_active,
                "break_duration": total_break,
            }

            periods_created += periods_this_session
            session_counter += 1

        return all_data  # Return sessions dict directly (tracker.data format)


class TestFileManager:
    """Manage test files with automatic cleanup"""

    def __init__(self):
        self.test_files = []
        self.test_dirs = []
        # Get the tests directory path
        self.tests_dir = os.path.dirname(os.path.abspath(__file__))
        # Use test_data subdirectory for all test files
        self.test_data_dir = os.path.join(self.tests_dir, "test_data")
        os.makedirs(self.test_data_dir, exist_ok=True)

    def create_test_file(self, filepath, content=None):
        """
        Create a test file and track it for cleanup

        Args:
            filepath: Path to test file (relative paths will be created in tests/test_data/ directory)
            content: Content to write (dict will be JSON encoded)
        """
        # If filepath is relative, create it in the test_data directory
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.test_data_dir, filepath)

        # Ensure directory exists (only if filepath has a directory component)
        dirpath = os.path.dirname(filepath)
        if dirpath:  # Only create directory if path has a directory component
            os.makedirs(dirpath, exist_ok=True)

        if content is not None:
            with open(filepath, "w") as f:
                if isinstance(content, dict):
                    json.dump(content, f, indent=2)
                else:
                    f.write(content)
        else:
            # Create empty file
            open(filepath, "w").close()

        self.test_files.append(filepath)
        return filepath

    def create_test_dir(self, dirpath):
        """Create a test directory and track it for cleanup"""
        os.makedirs(dirpath, exist_ok=True)
        self.test_dirs.append(dirpath)
        return dirpath

    def cleanup(self):
        """Remove all tracked test files and directories"""
        # Remove files
        for filepath in self.test_files:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                print(f"Warning: Could not remove test file {filepath}: {e}")

        # Remove directories (in reverse order for nested dirs)
        for dirpath in reversed(self.test_dirs):
            try:
                if os.path.exists(dirpath):
                    # Remove directory if empty
                    if not os.listdir(dirpath):
                        os.rmdir(dirpath)
            except Exception as e:
                print(f"Warning: Could not remove test dir {dirpath}: {e}")

        self.test_files.clear()
        self.test_dirs.clear()


class MockScreenshot:
    """Mock screenshot capture for testing"""

    def __init__(self, width=1920, height=1080):
        self.width = width
        self.height = height
        self.screenshots_taken = []

    def grab(self, bbox=None):
        """Mock screenshot grab"""
        mock_image = Mock()
        mock_image.size = (self.width, self.height)
        mock_image.save = Mock()
        self.screenshots_taken.append(
            {"timestamp": time.time(), "bbox": bbox, "image": mock_image}
        )
        return mock_image

    def reset(self):
        """Clear screenshot history"""
        self.screenshots_taken.clear()


def assert_duration_accurate(test_case, expected, actual, tolerance=0.1):
    """
    Assert that duration is accurate within tolerance

    Args:
        test_case: unittest.TestCase instance
        expected: Expected duration in seconds
        actual: Actual duration in seconds
        tolerance: Acceptable difference in seconds (default 0.1)
    """
    test_case.assertAlmostEqual(
        expected,
        actual,
        delta=tolerance,
        msg=f"Duration {actual} not within {tolerance}s of {expected}",
    )


def assert_timestamp_order(test_case, start_ts, end_ts):
    """
    Assert that end timestamp is after start timestamp

    Args:
        test_case: unittest.TestCase instance
        start_ts: Start timestamp
        end_ts: End timestamp
    """
    test_case.assertGreater(
        end_ts, start_ts, msg=f"End timestamp {end_ts} should be after start {start_ts}"
    )


def assert_session_structure_valid(test_case, session_data):
    """
    Assert that session data has valid structure

    Args:
        test_case: unittest.TestCase instance
        session_data: Session data dict to validate
    """
    required_fields = [
        "sphere",
        "date",
        "start_time",
        "start_timestamp",
        "active",
        "breaks",
        "end_time",
        "end_timestamp",
        "total_duration",
        "active_duration",
        "break_duration",
    ]

    for field in required_fields:
        test_case.assertIn(
            field, session_data, msg=f"Session missing required field: {field}"
        )

    # Validate lists
    test_case.assertIsInstance(session_data["active"], list)
    test_case.assertIsInstance(session_data["breaks"], list)

    # Validate timestamps
    assert_timestamp_order(
        test_case, session_data["start_timestamp"], session_data["end_timestamp"]
    )


def cancel_tkinter_callbacks(root):
    """Cancel all pending Tkinter after() callbacks before destroying root

    This prevents crashes with "Tcl_AsyncDelete: async handler deleted by wrong thread"
    that occur when root is destroyed while callbacks are still scheduled.

    Args:
        root: The Tkinter root window
    """
    try:
        if not root or not root.winfo_exists():
            return
        root.update_idletasks()
        after_ids = root.tk.call("after", "info")
        if after_ids:
            for after_id in after_ids:
                try:
                    root.after_cancel(after_id)
                except:
                    pass
        root.update_idletasks()
    except Exception:
        pass


def safe_teardown_tk_root(root):
    """Safely tear down Tkinter root by canceling callbacks and destroying

    This is the REQUIRED tearDown pattern for all Tkinter tests to prevent
    "Tcl_AsyncDelete: async handler deleted by wrong thread" crashes.

    Use this in tearDown() instead of calling root.destroy() directly:

        def tearDown(self):
            from tests.test_helpers import safe_teardown_tk_root
            safe_teardown_tk_root(self.root)

    Args:
        root: The Tkinter root window to tear down
    """
    import gc

    try:
        # Cancel all pending callbacks first
        cancel_tkinter_callbacks(root)

        # Quit the mainloop if running
        try:
            root.quit()
        except:
            pass

        # Destroy the root window
        try:
            root.destroy()
        except:
            pass

        # Force garbage collection to clean up tkinter variables immediately
        # This helps prevent "Variable.__del__" errors in large test suites
        collected = gc.collect()
        if collected > 0:
            print(f"[GC] Collected {collected} objects after tearDown")

    except Exception:
        # Suppress all tearDown errors
        pass
