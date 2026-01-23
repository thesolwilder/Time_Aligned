"""
Tests for Data Integrity

Verifies that session durations add up correctly and data remains consistent.
"""

import unittest
import tkinter as tk
import time
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from test_helpers import TestFileManager, TestDataGenerator


class TestDurationCalculations(unittest.TestCase):
    """Test that durations are calculated correctly"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_duration_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_duration_data.json"
        )

    @patch("time_tracker.TimeTracker.show_completion_frame")
    def test_total_equals_active_plus_break(self, mock_completion):
        """Test that total_duration = active_duration + break_duration"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        # Start session
        tracker.start_session()
        self.root.update()
        time.sleep(0.2)

        # Take a break
        tracker.toggle_break()
        self.root.update()
        time.sleep(0.2)
        tracker.toggle_break()
        self.root.update()

        # Continue working
        time.sleep(0.2)

        # End session
        tracker.end_session()
        self.root.update()

        # Load session data
        data = tracker.load_data()
        self.assertGreater(len(data), 0, "No session data was saved")
        # Get the session by name, not by position
        session = data[tracker.session_name]

        # Check that required fields exist
        self.assertIn("total_duration", session, f"Session data: {session.keys()}")
        self.assertIn("active_duration", session)
        self.assertIn("break_duration", session)

        total = session["total_duration"]
        active = session["active_duration"]
        break_dur = session["break_duration"]

        # Total should equal active + break (with small tolerance for rounding)
        calculated_total = active + break_dur
        self.assertAlmostEqual(total, calculated_total, delta=0.5)

    def test_active_duration_excludes_break_time(self):
        """Test that active duration doesn't include break time"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        tracker.start_session()
        self.root.update()
        time.sleep(0.2)

        active_before_break = tracker.session_elapsed

        # Take break
        tracker.toggle_break()
        self.root.update()
        time.sleep(0.3)
        tracker.toggle_break()
        self.root.update()

        # Active time should not have increased during break
        # (allowing small tolerance for timer updates)
        self.assertLess(tracker.session_elapsed - active_before_break, 0.5)

    @patch("time_tracker.TimeTracker.show_completion_frame")
    def test_session_duration_matches_timestamps(self, mock_completion):
        """Test that total_duration matches end_timestamp - start_timestamp"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        tracker.start_session()
        self.root.update()
        time.sleep(0.3)
        tracker.end_session()
        self.root.update()

        data = tracker.load_data()
        self.assertGreater(len(data), 0, "No session data was saved")
        session = data[tracker.session_name]

        # Check required fields exist
        self.assertIn("end_timestamp", session, f"Session data keys: {session.keys()}")
        self.assertIn("start_timestamp", session)
        self.assertIn("total_duration", session)

        timestamp_duration = session["end_timestamp"] - session["start_timestamp"]
        recorded_duration = session["total_duration"]

        # Should be approximately equal (within 1 second)
        self.assertAlmostEqual(timestamp_duration, recorded_duration, delta=1.0)


class TestMultipleBreaksDuration(unittest.TestCase):
    """Test duration calculations with multiple breaks"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_multi_break_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_multi_break_data.json"
        )

    def test_multiple_breaks_sum_correctly(self):
        """Test that break_duration is sum of all breaks"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        tracker.start_session()
        self.root.update()
        time.sleep(0.1)

        # First break
        tracker.toggle_break()
        self.root.update()
        time.sleep(0.15)
        tracker.toggle_break()
        self.root.update()

        first_break = tracker.total_break_time

        # Work
        time.sleep(0.1)

        # Second break
        tracker.toggle_break()
        self.root.update()
        time.sleep(0.15)
        tracker.toggle_break()
        self.root.update()

        total_breaks = tracker.total_break_time

        # Total should be greater than first break
        self.assertGreater(total_breaks, first_break)


class TestDataConsistency(unittest.TestCase):
    """Test that saved data remains consistent"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_consistency_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_consistency_data.json"
        )

    def test_saved_data_can_be_reloaded(self):
        """Test that saved data can be loaded back correctly"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        # Create and save session
        tracker.start_session()
        self.root.update()
        time.sleep(0.2)
        tracker.end_session()
        self.root.update()

        # Load the data
        data1 = tracker.load_data()
        session_name = tracker.session_name

        # Save again (should preserve data)
        tracker.save_data(data1, merge=False)

        # Reload
        data2 = tracker.load_data()

        # Should be identical
        self.assertEqual(data1[session_name], data2[session_name])

    def test_action_count_matches_actions_list(self):
        """Test that action count equals length of actions list"""
        # Create data with known actions
        data = {
            "session_1": {
                "date": "2024-01-20",
                "start_time": "10:00:00",
                "end_time": "11:00:00",
                "start_timestamp": 1000000,
                "end_timestamp": 1003600,
                "total_duration": 3600,
                "active_duration": 3000,
                "break_duration": 600,
                "sphere": "Work",
                "active": [],
                "breaks": [],
                "actions": [
                    {"time": "10:00:00"},
                    {"time": "10:15:00"},
                    {"time": "10:30:00"},
                ],
                "break_actions": [],
            }
        }

        self.file_manager.create_test_file(self.test_data_file, data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file

        loaded_data = tracker.load_data()
        session = loaded_data["session_1"]

        # Count should match
        self.assertEqual(len(session["actions"]), 3)

    def test_break_actions_structure_preserved(self):
        """Test that break_actions structure is preserved correctly"""
        data = {
            "session_1": {
                "date": "2024-01-20",
                "start_time": "10:00:00",
                "end_time": "11:00:00",
                "start_timestamp": 1000000,
                "end_timestamp": 1003600,
                "total_duration": 3600,
                "active_duration": 3000,
                "break_duration": 600,
                "sphere": "Work",
                "active": [],
                "breaks": [],
                "actions": [],
                "break_actions": [
                    {
                        "start": 1000300,
                        "end": 1000900,
                        "actions": [
                            {"time": "10:05:00"},
                            {"time": "10:10:00"},
                        ],
                    }
                ],
            }
        }

        self.file_manager.create_test_file(self.test_data_file, data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file

        loaded_data = tracker.load_data()
        session = loaded_data["session_1"]

        # Should have break_actions
        self.assertEqual(len(session["break_actions"]), 1)
        self.assertEqual(len(session["break_actions"][0]["actions"]), 2)


class TestNonNegativeDurations(unittest.TestCase):
    """Test that durations are never negative"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_nonneg_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_nonneg_data.json"
        )

    def test_all_durations_nonnegative(self):
        """Test that all duration values are >= 0"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        # Very short session
        tracker.start_session()
        self.root.update()
        time.sleep(0.05)
        tracker.end_session()
        self.root.update()

        data = tracker.load_data()
        session = data[tracker.session_name]

        # All durations should be non-negative
        self.assertGreaterEqual(session["total_duration"], 0)
        self.assertGreaterEqual(session["active_duration"], 0)
        self.assertGreaterEqual(session["break_duration"], 0)


if __name__ == "__main__":
    unittest.main()
