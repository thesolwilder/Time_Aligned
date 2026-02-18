"""
Test that active periods are properly created when resuming from idle.

Bug Reported: Active-Idle-Active sequence only shows 2 periods instead of 3.
When user resumes activity after idle, no new active period is created.
"""

import unittest
import tkinter as tk
import time
from datetime import datetime
from unittest.mock import patch

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from time_tracker import TimeTracker
from tests.test_helpers import TestFileManager, TestDataGenerator


class TestActiveAfterIdle(unittest.TestCase):
    """Test that active periods are properly tracked after idle periods"""

    def setUp(self):
        """Set up test fixtures before each test"""
        self.file_manager = TestFileManager()

        # Create test settings with very short idle threshold (1 second)
        settings = TestDataGenerator.create_settings_data()
        settings["idle_settings"]["idle_threshold"] = 1  # 1 second
        settings["idle_settings"][
            "idle_break_threshold"
        ] = 300  # 5 minutes (won't trigger)

        self.test_data_file = self.file_manager.create_test_file(
            "test_active_idle_data.json", {}
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_active_idle_settings.json", settings
        )

        # Create root window for TimeTracker
        self.root = tk.Tk()
        self.tracker = TimeTracker(self.root)
        self.tracker.settings_file = self.test_settings_file
        self.tracker.data_file = self.test_data_file

    def tearDown(self):
        """Clean up after each test"""
        if self.tracker.session_active:
            self.tracker.session_active = False
            if hasattr(self.tracker, "stop_input_monitoring"):
                self.tracker.stop_input_monitoring()
        self.root.destroy()

        # Clean up test files
        self.file_manager.cleanup()

    def test_new_active_period_created_after_idle_ends(self):
        """Test that completion frame should show 3 periods for Active-Idle-Active sequence"""
        # Bug recreation:
        # User manually creates a session with Active(5s) → Idle(5s) → Active(5s)
        # Completion frame should show 3 periods but only shows 2
        # The second active period is missing from the data

        # Create test session data that simulates what SHOULD happen
        # when user: starts session → active 5s → idle 5s → active 5s → end session
        session_name = "2026-02-02_session1"
        test_data = {
            session_name: {
                "sphere": "General",
                "date": "2026-02-02",
                "start_time": "05:58:54 PM",
                "end_time": "05:59:11 PM",
                "total_duration": 17,  # 17 seconds total
                "active_duration": 11,  # 11 seconds active (6s + 5s)
                "break_duration": 0,
                "total_elapsed": 17,
                "active_time": 11,
                "break_time": 0,
                "session_start_timestamp": 1000,
                "session_end_timestamp": 1017,
                "active": [
                    # First active period: 5:58:54 PM - 5:59:00 PM (6 seconds)
                    {
                        "start": "17:58:54",
                        "start_timestamp": 1000,
                        "end": "17:59:00",
                        "end_timestamp": 1006,
                        "duration": 6,
                    },
                    # Second active period: 5:59:06 PM - 5:59:11 PM (5 seconds)
                    # THIS IS WHAT SHOULD EXIST BUT IS MISSING DUE TO THE BUG
                    {
                        "start": "17:59:06",
                        "start_timestamp": 1011,
                        "end": "17:59:11",
                        "end_timestamp": 1016,
                        "duration": 5,
                    },
                ],
                "idle_periods": [
                    # Idle period: 5:59:00 PM - 5:59:06 PM (6 seconds, but 5 seconds without threshold)
                    {
                        "start": "17:59:00",
                        "start_timestamp": 1005,  # idle detected 1 sec after last activity
                        "end": "17:59:06",
                        "end_timestamp": 1011,
                        "duration": 6,
                    }
                ],
                "breaks": [],
            }
        }

        # Save test data
        self.tracker.save_data(test_data)

        # Load the data to verify
        all_data = self.tracker.load_data()
        session_data = all_data[session_name]

        # Verify we have the expected structure
        self.assertEqual(len(session_data["active"]), 2, "Should have 2 active periods")
        self.assertEqual(
            len(session_data["idle_periods"]), 1, "Should have 1 idle period"
        )
        self.assertEqual(len(session_data["breaks"]), 0, "Should have 0 break periods")

        # When completion frame loads this, it should show 3 periods total
        from src.completion_frame import CompletionFrame

        frame = CompletionFrame(self.root, self.tracker, session_name)

        # Check that all_periods contains all 3 periods
        self.assertEqual(
            len(frame.all_periods),
            3,
            f"Completion frame should show 3 periods (Active, Idle, Active), "
            f"but got {len(frame.all_periods)}. Periods: {frame.all_periods}",
        )

        # Verify the periods are in chronological order
        self.assertEqual(
            frame.all_periods[0]["type"], "Active", "First period should be Active"
        )
        self.assertEqual(
            frame.all_periods[1]["type"], "Idle", "Second period should be Idle"
        )
        self.assertEqual(
            frame.all_periods[2]["type"], "Active", "Third period should be Active"
        )

    def test_bug_active_idle_active_shows_only_two_periods(self):
        """
        This test demonstrates the ACTUAL bug that occurs in production.

        Bug: When a session has Active → Idle → Active sequence,
        the second active period is NOT created/saved.
        Result: Completion frame only shows 2 periods instead of 3.
        """
        # This is what ACTUALLY gets saved (the buggy behavior)
        session_name = "2026-02-02_session_buggy"
        buggy_data = {
            session_name: {
                "sphere": "General",
                "date": "2026-02-02",
                "start_time": "05:58:54 PM",
                "end_time": "05:59:11 PM",
                "total_duration": 17,
                "active_duration": 11,  # Says 11 seconds but...
                "break_duration": 0,
                "total_elapsed": 17,
                "active_time": 11,
                "break_time": 0,
                "session_start_timestamp": 1000,
                "session_end_timestamp": 1017,
                "active": [
                    # Only ONE active period saved (the first one)
                    {
                        "start": "17:58:54",
                        "start_timestamp": 1000,
                        "end": "17:59:00",
                        "end_timestamp": 1006,
                        "duration": 6,
                    },
                    # Second active period MISSING! (The bug)
                    # Should have: start: 1011, end: 1016, duration: 5
                ],
                "idle_periods": [
                    {
                        "start": "17:59:00",
                        "start_timestamp": 1005,
                        "end": "17:59:06",
                        "end_timestamp": 1011,
                        "duration": 6,
                    }
                ],
                "breaks": [],
            }
        }

        self.tracker.save_data(buggy_data)

        from src.completion_frame import CompletionFrame

        frame = CompletionFrame(self.root, self.tracker, session_name)

        # This is the bug - only 2 periods show up
        self.assertEqual(
            len(frame.all_periods),
            2,
            f"Bug demonstration: Only 2 periods show (should be 3). "
            f"This is the current buggy behavior.",
        )

        # The periods that do show are:
        self.assertEqual(frame.all_periods[0]["type"], "Active")  # First active
        self.assertEqual(frame.all_periods[1]["type"], "Idle")  # Idle period
        # Missing: Second active period after idle ends


if __name__ == "__main__":
    unittest.main()
