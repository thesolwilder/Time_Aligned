"""
Tests for Time Tracking Accuracy - Simplified Integration Tests

Verifies that time periods, durations, and timestamps are recorded correctly.
Uses real TimeTracker instances for integration testing.
"""

import unittest
import json
import os
import sys
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from test_helpers import (
    TestDataGenerator,
    TestFileManager,
    assert_duration_accurate,
    assert_session_structure_valid,
)


class TestTimeTrackingAccuracy(unittest.TestCase):
    """Test time tracking accuracy and duration calculations"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()
        self.test_data_file = "test_time_data.json"
        self.test_settings_file = "test_time_settings.json"

        # Create test files
        self.file_manager.create_test_file(self.test_data_file, {})
        self.file_manager.create_test_file(
            self.test_settings_file, TestDataGenerator.create_settings_data()
        )

    def tearDown(self):
        """Clean up test files"""
        self.file_manager.cleanup()

    def test_session_start_creates_timestamp(self):
        """Test that session start creates a timestamp"""
        from time_tracker import TimeTracker
        import tkinter as tk

        root = tk.Tk()
        tracker = TimeTracker(root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        start_time = time.time()
        tracker.start_session()

        self.assertIsNotNone(tracker.session_name)
        self.assertTrue(tracker.session_active)
        self.assertIsNotNone(tracker.session_start_time)

        # Timestamp should be close to now
        self.assertLess(abs(tracker.session_start_time - start_time), 1.0)

        tracker.end_session()
        from time_tracker import TimeTracker
        import tkinter as tk

        root = tk.Tk()
        tracker = TimeTracker(root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        tracker.start_session()
        time.sleep(0.2)
        tracker.end_session()

        # Load saved data
        with open(self.test_data_file, "r") as f:
            data = json.load(f)

        self.assertGreater(len(data), 0)
        session = list(data.values())[0]

        # Verify session structure
        assert_session_structure_valid(self, session)

        root.destroy()

    def test_active_duration_recorded(self):
        """Test that active duration is recorded"""
        from time_tracker import TimeTracker
        import tkinter as tk

        root = tk.Tk()
        tracker = TimeTracker(root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        tracker.start_session()
        time.sleep(0.3)  # Work for 0.3 seconds
        tracker.end_session()

        with open(self.test_data_file, "r") as f:
            data = json.load(f)

        session = list(data.values())[0]

        # Active duration should be close to sleep time (0.3s)
        # We allow a tolerance for system overhead
        assert_duration_accurate(self, 0.3, session["active_duration"], tolerance=1.0)

        root.destroy()

    def test_session_has_sphere(self):
        """Test that session records sphere"""
        from time_tracker import TimeTracker
        import tkinter as tk

        root = tk.Tk()
        tracker = TimeTracker(root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        tracker.start_session()
        tracker.end_session()

        with open(self.test_data_file, "r") as f:
            data = json.load(f)

        session = list(data.values())[0]
        self.assertIn("sphere", session)
        self.assertIsNotNone(session["sphere"])

        root.destroy()

    def test_timestamp_ordering(self):
        """Test that end timestamp is after start timestamp"""
        from time_tracker import TimeTracker
        import tkinter as tk

        root = tk.Tk()
        tracker = TimeTracker(root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        tracker.start_session()
        time.sleep(0.1)
        tracker.end_session()

        with open(self.test_data_file, "r") as f:
            data = json.load(f)

        session = list(data.values())[0]
        self.assertGreater(session["end_timestamp"], session["start_timestamp"])

        root.destroy()


if __name__ == "__main__":
    unittest.main()
