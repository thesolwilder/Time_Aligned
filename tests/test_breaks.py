"""
Tests for Break Recording

Verifies break recording, duration tracking, and break action logging.
"""

import unittest
import tkinter as tk
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from test_helpers import TestFileManager, TestDataGenerator


class TestBreakRecording(unittest.TestCase):
    """Test break recording functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_breaks_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_breaks_data.json"
        )

    def test_start_break_creates_break_period(self):
        """Test that starting a break creates a break period in session data"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        # Start a session
        tracker.start_session()
        self.root.update()
        time.sleep(0.1)

        # Start a break
        tracker.toggle_break()
        self.root.update()

        # Verify break started
        self.assertTrue(tracker.break_active)
        self.assertIsNotNone(tracker.break_start_time)

    def test_end_break_records_duration(self):
        """Test that ending a break records the break duration"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        # Start session and break
        tracker.start_session()
        self.root.update()
        time.sleep(0.1)

        tracker.toggle_break()
        self.root.update()
        time.sleep(0.2)

        # End break
        tracker.toggle_break()
        self.root.update()

        # Break should no longer be active
        self.assertFalse(tracker.break_active)

        # Break duration should be recorded in total_break_time (break_elapsed resets to 0)
        self.assertGreater(tracker.total_break_time, 0)

    def test_multiple_breaks_in_session(self):
        """Test that multiple breaks can be taken during a session"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        # Start session
        tracker.start_session()
        self.root.update()
        time.sleep(0.1)

        # First break
        tracker.toggle_break()
        self.root.update()
        time.sleep(0.1)
        tracker.toggle_break()
        self.root.update()

        first_break_time = tracker.total_break_time

        # Second break
        time.sleep(0.1)
        tracker.toggle_break()
        self.root.update()
        time.sleep(0.1)
        tracker.toggle_break()
        self.root.update()

        # Total break time should include both breaks
        self.assertGreater(tracker.total_break_time, first_break_time)


class TestBreakTimerDisplay(unittest.TestCase):
    """Test break timer display updates"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_break_timer_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_break_timer_data.json"
        )

    def test_break_timer_shows_during_break(self):
        """Test that break timer is visible during a break"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        tracker.start_session()
        self.root.update()

        tracker.toggle_break()
        self.root.update()

        # Total break label should be visible
        self.assertTrue(tracker.total_break_label.winfo_ismapped())

    def test_break_timer_updates(self):
        """Test that break timer increments during break"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        tracker.start_session()
        self.root.update()

        tracker.toggle_break()
        self.root.update()
        time.sleep(0.2)
        self.root.update()

        # Break time should be greater than 0
        self.assertGreater(tracker.break_elapsed, 0)


class TestBreakDataPersistence(unittest.TestCase):
    """Test that break data is saved correctly"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_break_persist_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_break_persist_data.json"
        )

    def test_break_data_saved_on_session_end(self):
        """Test that break data is included when session ends"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        # Start session and take a break
        tracker.start_session()
        self.root.update()
        time.sleep(0.1)

        tracker.toggle_break()
        self.root.update()
        time.sleep(0.2)
        tracker.toggle_break()
        self.root.update()

        # End session
        tracker.end_session()
        self.root.update()

        # Load data and verify break info is saved
        data = tracker.load_data()

        # Get the session by name
        self.assertIn(tracker.session_name, data, "Session not found in saved data")
        session = data[tracker.session_name]

        # Session should have break_duration
        self.assertIn("break_duration", session)
        self.assertGreater(session["break_duration"], 0)


class TestBreakDurationAccuracy(unittest.TestCase):
    """Test accuracy of break duration calculations"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_break_accuracy_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_break_accuracy_data.json"
        )

    def test_break_duration_approximately_correct(self):
        """Test that recorded break duration matches actual time"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        tracker.start_session()
        self.root.update()

        tracker.toggle_break()
        self.root.update()

        # Sleep for known duration
        time.sleep(0.3)

        tracker.toggle_break()
        self.root.update()

        # Break duration should be approximately 0.3 seconds
        # Check total_break_time (break_elapsed resets to 0 after break ends)
        # Allow 1 second tolerance for UI overhead
        self.assertGreater(tracker.total_break_time, 0.2)
        self.assertLess(tracker.total_break_time, 1.5)


if __name__ == "__main__":
    unittest.main()
