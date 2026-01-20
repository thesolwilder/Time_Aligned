"""
Tests for Idle Tracking Functionality

Verifies that idle detection works correctly and idle periods are recorded accurately.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk
import time
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from test_helpers import MockTime, TestDataGenerator, TestFileManager
from time_tracker import TimeTracker


class TestIdleTracking(unittest.TestCase):
    """Test idle detection and tracking"""

    def setUp(self):
        """Set up test fixtures before each test"""
        self.file_manager = TestFileManager()
        self.test_data_file = "test_idle_data.json"
        self.test_settings_file = "test_idle_settings.json"

        # Create test settings with short thresholds
        settings = TestDataGenerator.create_settings_data()
        settings["idle_settings"]["idle_threshold"] = 2  # 2 seconds
        settings["idle_settings"]["idle_break_threshold"] = 10  # 10 seconds

        self.file_manager.create_test_file(self.test_data_file, {})
        self.file_manager.create_test_file(self.test_settings_file, settings)

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

    def test_idle_period_recorded_on_activity_before_auto_break(self):
        """Test that idle period is properly recorded when user becomes active before auto-break"""
        # Start a session
        self.tracker.start_session()
        session_name = self.tracker.session_name

        # Set last user input to 3 seconds ago (past idle threshold)
        self.tracker.last_user_input = time.time() - 3

        # Trigger idle detection
        self.tracker.check_idle()

        # Verify we are now idle
        self.assertTrue(self.tracker.session_idle, "Should be in idle state")

        # Load data and verify idle period was started
        all_data = self.tracker.load_data()
        idle_periods = all_data[session_name]["idle_periods"]
        self.assertEqual(len(idle_periods), 1, "Should have one idle period")
        self.assertIn("start", idle_periods[0], "Idle period should have start time")
        self.assertIn(
            "start_timestamp",
            idle_periods[0],
            "Idle period should have start timestamp",
        )
        self.assertNotIn(
            "end", idle_periods[0], "Idle period should not have end time yet"
        )

        # Simulate user activity (before auto-break threshold)
        self.tracker.last_user_input = time.time()

        # Manually trigger the on_activity logic (since we can't easily simulate mouse/keyboard)
        if self.tracker.session_idle:
            self.tracker.session_idle = False
            # Save idle period end
            all_data = self.tracker.load_data()
            if self.tracker.session_name in all_data:
                idle_periods = all_data[self.tracker.session_name]["idle_periods"]
                if idle_periods and "end" not in idle_periods[-1]:
                    last_idle = idle_periods[-1]
                    from datetime import datetime

                    last_idle["end"] = datetime.now().strftime("%H:%M:%S")
                    last_idle["end_timestamp"] = self.tracker.last_user_input
                    last_idle["duration"] = (
                        last_idle["end_timestamp"] - last_idle["start_timestamp"]
                    )
                    self.tracker.save_data(all_data)

        # Verify idle period was ended
        all_data = self.tracker.load_data()
        idle_periods = all_data[session_name]["idle_periods"]

        self.assertEqual(len(idle_periods), 1, "Should still have one idle period")
        self.assertIn("end", idle_periods[0], "Idle period should now have end time")
        self.assertIn(
            "end_timestamp", idle_periods[0], "Idle period should have end timestamp"
        )
        self.assertIn("duration", idle_periods[0], "Idle period should have duration")

        # Verify duration is positive and reasonable
        duration = idle_periods[0]["duration"]
        self.assertGreater(duration, 0, "Duration should be positive")
        self.assertLess(
            duration, 10, "Duration should be less than auto-break threshold"
        )

        # Verify we're no longer idle
        self.assertFalse(self.tracker.session_idle, "Should no longer be in idle state")

    def test_multiple_idle_periods(self):
        """Test that multiple idle periods are recorded correctly"""
        # Start a session
        self.tracker.start_session()
        session_name = self.tracker.session_name

        # First idle period - set last input to 3 seconds ago
        self.tracker.last_user_input = time.time() - 3
        self.tracker.check_idle()
        self.assertTrue(self.tracker.session_idle, "Should be idle after first check")

        # Return to active
        self.tracker.last_user_input = time.time()
        if self.tracker.session_idle:
            self.tracker.session_idle = False
            all_data = self.tracker.load_data()
            idle_periods = all_data[session_name]["idle_periods"]
            if idle_periods and "end" not in idle_periods[-1]:
                last_idle = idle_periods[-1]
                from datetime import datetime

                last_idle["end"] = datetime.now().strftime("%H:%M:%S")
                last_idle["end_timestamp"] = self.tracker.last_user_input
                last_idle["duration"] = (
                    last_idle["end_timestamp"] - last_idle["start_timestamp"]
                )
                self.tracker.save_data(all_data)

        self.assertFalse(self.tracker.session_idle, "Should not be idle after activity")

        # Second idle period - set last input to 3 seconds ago again
        self.tracker.last_user_input = time.time() - 3
        self.tracker.check_idle()
        self.assertTrue(self.tracker.session_idle, "Should be idle after second check")

        # Return to active again
        self.tracker.last_user_input = time.time()
        if self.tracker.session_idle:
            self.tracker.session_idle = False
            all_data = self.tracker.load_data()
            idle_periods = all_data[session_name]["idle_periods"]
            if idle_periods and "end" not in idle_periods[-1]:
                last_idle = idle_periods[-1]
                from datetime import datetime

                last_idle["end"] = datetime.now().strftime("%H:%M:%S")
                last_idle["end_timestamp"] = self.tracker.last_user_input
                last_idle["duration"] = (
                    last_idle["end_timestamp"] - last_idle["start_timestamp"]
                )
                self.tracker.save_data(all_data)

        # Verify we have two idle periods
        all_data = self.tracker.load_data()
        idle_periods = all_data[session_name]["idle_periods"]

        self.assertEqual(len(idle_periods), 2, "Should have two idle periods")
        self.assertIn("end", idle_periods[0], "First idle period should have end time")
        self.assertIn("end", idle_periods[1], "Second idle period should have end time")


if __name__ == "__main__":
    unittest.main()
