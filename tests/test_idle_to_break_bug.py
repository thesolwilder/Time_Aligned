"""
Tests for idle-to-break conversion bug.

Bug: When idle auto-converts to break and user ends session:
  1. Two duplicate active periods shown instead of one
  2. Idle period has the same time range as break
  3. Active Time header shows a negative number

Root cause: session_idle flag is never reset when idle converts to break,
so on_activity callback re-processes idle recovery on the next keypress (e.g. pressing E).

Expected behavior after fix: 1 active period, 1 break period, 0 idle periods.

Bug recreation steps:
  - Start session and let go idle
  - Idle threshold exceeded -> idle period saved
  - Break threshold exceeded -> auto-break starts (toggle_break called)
  - Press E to end session
  - Bug: two duplicate active periods, idle == break duration, negative active time
"""

import unittest
import tkinter as tk
import time
from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from tests.test_helpers import TestFileManager, TestDataGenerator


class TestIdleToBreakBug(unittest.TestCase):
    """Test that idle-to-break conversion is handled correctly."""

    def setUp(self):
        """Set up test fixtures."""
        self.file_manager = TestFileManager()

        settings = TestDataGenerator.create_settings_data()
        settings["idle_settings"]["idle_threshold"] = 1       # 1 second
        settings["idle_settings"]["idle_break_threshold"] = 3  # 3 seconds

        self.test_data_file = self.file_manager.create_test_file(
            "test_idle_break_data.json", {}
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_idle_break_settings.json", settings
        )

        self.root = tk.Tk()

    def tearDown(self):
        """Clean up after tests."""
        from tests.test_helpers import safe_teardown_tk_root
        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def _make_tracker(self):
        """Create a configured tracker for testing."""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        # Reload settings so short idle thresholds take effect in check_idle()
        tracker.settings = tracker.get_settings()
        return tracker

    def _trigger_idle_then_auto_break(self, tracker):
        """Simulate idle detection followed by auto-break threshold exceeded."""
        # Make last user input 5 seconds ago (> idle_threshold=1s and > idle_break_threshold=3s)
        tracker.last_user_input = time.time() - 5

        # First check_idle: should detect idle and save idle period start
        tracker.check_idle()

        # Second check_idle: session_idle=True and idle_time > break_threshold -> auto-start break
        tracker.check_idle()

    @patch("time_tracker.TimeTracker.show_completion_frame")
    def test_session_idle_flag_is_false_after_auto_break_starts(self, _mock):
        """session_idle should be False once idle auto-converts to break."""
        tracker = self._make_tracker()
        tracker.start_session()
        self.root.update()

        self._trigger_idle_then_auto_break(tracker)

        # Break should be active
        self.assertTrue(tracker.break_active, "Break should be active after auto-break")

        # BUG: session_idle remains True after break starts
        # FIX: session_idle should be False (break subsumes idle state)
        self.assertFalse(
            tracker.session_idle,
            "session_idle should be False after idle converts to break",
        )

        tracker.session_active = False
        tracker.stop_input_monitoring()

    @patch("time_tracker.TimeTracker.show_completion_frame")
    def test_idle_period_removed_when_break_starts_from_idle(self, _mock):
        """The open idle period should be removed when idle auto-converts to break."""
        tracker = self._make_tracker()
        tracker.start_session()
        self.root.update()

        # Trigger only idle detection (not yet break threshold)
        tracker.last_user_input = time.time() - 5
        tracker.check_idle()

        data = tracker.load_data()
        self.assertEqual(
            len(data[tracker.session_name]["idle_periods"]),
            1,
            "Idle period should be opened after idle detection",
        )
        self.assertNotIn(
            "end",
            data[tracker.session_name]["idle_periods"][0],
            "Idle period should be open (no end) after detection",
        )

        # Trigger break threshold -> auto-break starts
        tracker.check_idle()

        data = tracker.load_data()
        # BUG: idle period remains open in data
        # FIX: idle period should be removed (break starts at idle detection time)
        self.assertEqual(
            len(data[tracker.session_name]["idle_periods"]),
            0,
            "Idle period should be removed when idle converts to break",
        )

        tracker.session_active = False
        tracker.stop_input_monitoring()

    @patch("time_tracker.TimeTracker.show_completion_frame")
    def test_end_session_after_idle_to_break_produces_one_active_one_break(self, _mock):
        """After idle->break->end_session: exactly 1 active period and 1 break period."""
        tracker = self._make_tracker()
        tracker.start_session()
        self.root.update()

        self._trigger_idle_then_auto_break(tracker)
        self.assertTrue(tracker.break_active, "Break should be active")

        # End session while on break (simulates user pressing E)
        tracker.end_session()
        self.root.update()

        data = tracker.load_data()
        session = data[tracker.session_name]

        active_count = len(session.get("active", []))
        break_count = len(session.get("breaks", []))
        idle_count = len(session.get("idle_periods", []))

        self.assertEqual(
            active_count,
            1,
            f"Expected 1 active period, got {active_count}. "
            "Bug: on_activity saves a duplicate active period on keypress.",
        )
        self.assertEqual(
            break_count,
            1,
            f"Expected 1 break period, got {break_count}",
        )
        self.assertEqual(
            idle_count,
            0,
            f"Expected 0 idle periods (break subsumes idle), got {idle_count}. "
            "Bug: idle period remains with same duration as break.",
        )

    @patch("time_tracker.TimeTracker.show_completion_frame")
    def test_active_duration_non_negative_after_idle_to_break(self, _mock):
        """active_duration stored in data should be >= 0 after idle->break->end_session."""
        tracker = self._make_tracker()
        tracker.start_session()
        self.root.update()

        self._trigger_idle_then_auto_break(tracker)

        tracker.end_session()
        self.root.update()

        data = tracker.load_data()
        session = data[tracker.session_name]
        active_duration = session.get("active_duration", 0)

        self.assertGreaterEqual(
            active_duration,
            0,
            f"active_duration should be >= 0, got {active_duration}. "
            "Bug: idle duration incorrectly subtracted from active time in CompletionFrame.",
        )


if __name__ == "__main__":
    unittest.main()
