"""
Integration test for completion frame skip bug

Bug recreation:
1. Create session with 5sec active, 5sec break
2. End session
3. Click skip (goes back to home screen)
4. Navigate to analysis frame
5. BUG: Only break period shows up on card and timeline - active period missing

Root cause: skip doesn't record sphere/project at all for active periods.
Expected: Active periods should get default sphere and project when skip is clicked.
"""

import unittest
import tkinter as tk
from unittest.mock import patch
import json
import os
import sys
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from src.completion_frame import CompletionFrame
from tests.test_helpers import TestDataGenerator, TestFileManager, MockTime


class TestCompletionFrameSkipBug(unittest.TestCase):
    """Integration test: Skip button should record default sphere/project for session"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        # Create test settings with default sphere and project
        test_settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_skip_settings.json", test_settings
        )

        # Create initial session with active and break periods (mimics end_session behavior)
        session_name = "2026-01-20_1737374400"
        start_time = 1737374400.0
        active_duration = 5.0  # 5 seconds
        break_duration = 5.0  # 5 seconds

        session_data = {
            session_name: {
                "date": "2026-01-20",
                "start_time": "12:00:00",
                "start_timestamp": start_time,
                "end_time": "12:00:10",
                "end_timestamp": start_time + active_duration + break_duration,
                "total_duration": active_duration + break_duration,
                "active_duration": active_duration,
                "break_duration": break_duration,
                # Note: NO sphere set yet - this is key to the bug
                "active": [
                    {
                        "start": "12:00:00",
                        "start_timestamp": start_time,
                        "end": "12:00:05",
                        "end_timestamp": start_time + active_duration,
                        "duration": active_duration,
                        # Note: NO project set - skip should set default
                    }
                ],
                "breaks": [
                    {
                        "start": "12:00:05",
                        "start_timestamp": start_time + active_duration,
                        "end": "12:00:10",
                        "end_timestamp": start_time + active_duration + break_duration,
                        "duration": break_duration,
                        # Note: NO action set - skip should set default
                    }
                ],
                "idle_periods": [],
            }
        }

        self.test_data_file = self.file_manager.create_test_file(
            "test_skip_data.json", session_data
        )
        self.session_name = session_name

    def test_skip_records_default_sphere_and_project(self):
        """
        When user clicks skip, session should get default sphere and all periods
        should get default project/action assigned.

        Bug recreation:
        1. Session with 5sec active, 5sec break (no sphere/project assigned yet)
        2. User clicks skip button
        3. Expected: Session gets default sphere, active gets default project
        4. Bug: Session has NO sphere, active has NO project
        5. Result: Analysis frame filters out active periods (no project = hidden)
        """
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.session_name = self.session_name

        # Get default sphere and project from settings using correct helper methods
        default_sphere = tracker._get_default_sphere()
        default_project = tracker.get_default_project(default_sphere)
        _, default_break_action = tracker.get_active_break_actions()

        # Create completion frame
        frame = CompletionFrame(self.root, tracker, self.session_name)
        self.root.update()

        # Verify initial state - session has NO sphere yet
        data_before = tracker.load_data()
        session_before = data_before[self.session_name]
        self.assertNotIn("sphere", session_before)  # Bug: no sphere
        self.assertNotIn("project", session_before["active"][0])  # Bug: no project
        self.assertNotIn("action", session_before["breaks"][0])  # Bug: no action

        # User clicks skip button (the bug scenario)
        frame.skip_and_close()

        # Load data after skip
        data_after = tracker.load_data()
        session_after = data_after[self.session_name]

        # EXPECTED BEHAVIOR (this test will FAIL until bug is fixed):
        # Skip should record default sphere
        self.assertEqual(
            session_after.get("sphere"),
            default_sphere,
            "Skip should set default sphere on session",
        )

        # Skip should record default project for active periods
        active_period = session_after["active"][0]
        self.assertEqual(
            active_period.get("project"),
            default_project,
            "Skip should set default project for active periods",
        )

        # Skip should record default action for break periods
        break_period = session_after["breaks"][0]
        self.assertEqual(
            break_period.get("action"),
            default_break_action,
            "Skip should set default break action for break periods",
        )

    def test_skip_does_not_overwrite_existing_assignments(self):
        """
        If session already has sphere/project/action assigned (via autosave),
        skip should preserve those values, not overwrite with defaults.
        """
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        # Manually assign specific sphere/project/action (simulates user editing before skip)
        data = tracker.load_data()
        session = data[self.session_name]
        session["sphere"] = "CustomSphere"
        session["active"][0]["project"] = "CustomProject"
        session["active"][0]["comment"] = "Custom comment"
        session["breaks"][0]["action"] = "CustomBreak"
        session["breaks"][0]["comment"] = "Break comment"
        tracker.save_data(data)

        # Create completion frame
        frame = CompletionFrame(self.root, tracker, self.session_name)
        self.root.update()

        # User clicks skip
        frame.skip_and_close()

        # Load data after skip
        data_after = tracker.load_data()
        session_after = data_after[self.session_name]

        # Should preserve existing assignments, not overwrite with defaults
        self.assertEqual(session_after.get("sphere"), "CustomSphere")
        self.assertEqual(session_after["active"][0].get("project"), "CustomProject")
        self.assertEqual(session_after["active"][0].get("comment"), "Custom comment")
        self.assertEqual(session_after["breaks"][0].get("action"), "CustomBreak")
        self.assertEqual(session_after["breaks"][0].get("comment"), "Break comment")


if __name__ == "__main__":
    unittest.main()
