"""
Regression Test for Secondary Project/Action Preservation

Ensures that when editing session comments for an existing session,
the secondary project and action data is preserved correctly.

Test Scenario:
1. Load a session with secondary projects and actions
2. Edit session comments
3. Save the session
4. Verify secondary project/action data remains intact
"""

import unittest
import tkinter as tk
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from src.completion_frame import CompletionFrame
from tests.test_helpers import TestFileManager


class TestSecondaryProjectPreservation(unittest.TestCase):
    """Regression test: secondary project/action data preserved when editing session"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        # Create settings with multiple projects and actions
        self.settings = {
            "idle_settings": {
                "idle_tracking_enabled": True,
                "idle_threshold": 60,
                "idle_break_threshold": 300,
            },
            "spheres": {
                "Coding": {"is_default": True, "active": True},
            },
            "projects": {
                "Project A": {
                    "sphere": "Coding",
                    "is_default": True,
                    "active": True,
                },
                "Project B": {
                    "sphere": "Coding",
                    "is_default": False,
                    "active": True,
                },
            },
            "break_actions": {
                "bathroom": {"active": True},
                "snack": {"active": True},
            },
        }

        # Create test data and settings files
        self.data_file = self.file_manager.create_test_file(
            "test_secondary_bug_data.json", {}
        )
        self.settings_file = self.file_manager.create_test_file(
            "test_secondary_bug_settings.json", self.settings
        )

        # Create tracker with test settings
        self.tracker = TimeTracker(self.root)
        self.tracker.data_file = self.data_file
        self.tracker.settings_file = self.settings_file
        self.tracker.settings = self.tracker.get_settings()

    def test_secondary_project_preserved_when_editing_comments(self):
        """
        Regression test: secondary project/action preserved when editing session comments

        Verifies that:
        1. Sessions with secondary projects/actions load correctly
        2. Editing session comments doesn't remove secondary data
        3. Secondary data persists after save operations
        """
        # Create a session with 1 active period and 1 break period
        session_name = "2026-01-28_1234567890"
        test_data = {
            session_name: {
                "sphere": "Coding",
                "date": "2026-01-28",
                "start_time": "10:00:00",
                "start_timestamp": 1234567890.0,
                "active": [
                    {
                        "start": "10:00:00",
                        "start_timestamp": 1234567890.0,
                        "end": "10:30:00",
                        "end_timestamp": 1234569690.0,
                        "duration": 1800,
                        "projects": [
                            {
                                "name": "Project A",
                                "percentage": 70,
                                "comment": "primary work",
                                "duration": 1260,
                                "project_primary": True,
                            },
                            {
                                "name": "Project B",
                                "percentage": 30,
                                "comment": "secondary work",
                                "duration": 540,
                                "project_primary": False,
                            },
                        ],
                    }
                ],
                "breaks": [
                    {
                        "start": "10:30:00",
                        "start_timestamp": 1234569690.0,
                        "end": "10:35:00",
                        "end_timestamp": 1234569990.0,
                        "duration": 300,
                        "actions": [
                            {
                                "name": "bathroom",
                                "percentage": 60,
                                "duration": 180,
                                "comment": "primary break",
                                "break_primary": True,
                            },
                            {
                                "name": "snack",
                                "percentage": 40,
                                "duration": 120,
                                "comment": "secondary break",
                                "break_primary": False,
                            },
                        ],
                    }
                ],
                "idle_periods": [],
                "end_time": "10:35:00",
                "end_timestamp": 1234569990.0,
                "total_duration": 2100,
                "active_duration": 1800,
                "break_duration": 300,
                "session_comments": {
                    "active_notes": "",
                    "break_notes": "",
                    "idle_notes": "",
                    "session_notes": "",
                },
            }
        }

        # Save the test data
        with open(self.data_file, "w") as f:
            json.dump(test_data, f, indent=2)

        # Create completion frame (simulating going back to session view)
        frame = CompletionFrame(self.root, self.tracker, session_name)
        self.root.update()

        # Verify the frame loaded the data correctly
        self.assertEqual(len(frame.all_periods), 2)  # 1 active + 1 break

        # Verify secondary project is loaded
        active_period = frame.all_periods[0]
        self.assertEqual(active_period["type"], "Active")
        self.assertEqual(active_period["project"], "Project A")
        self.assertEqual(active_period["secondary_project"], "Project B")
        self.assertEqual(active_period["comment"], "primary work")
        self.assertEqual(active_period["secondary_comment"], "secondary work")

        # *THIS IS THE BUG* - Check what the secondary dropdown shows
        # It should show "Project B", but let's see what it actually shows
        secondary_menu = frame.secondary_menus[0]
        print(f"Secondary menu value: {secondary_menu.get()}")

        # THE BUG: The dropdown might show "Select A Project" instead of "Project B"
        # even though secondary_project data exists
        # Let's assert what we EXPECT (this might fail and expose the bug)
        self.assertEqual(
            secondary_menu.get(),
            "Project B",
            "Secondary dropdown should show the saved secondary project",
        )

        # Verify break period has secondary action
        break_period = frame.all_periods[1]
        self.assertEqual(break_period["type"], "Break")
        self.assertEqual(break_period["action"], "bathroom")
        self.assertEqual(break_period["secondary_action"], "snack")
        self.assertEqual(break_period["comment"], "primary break")
        self.assertEqual(break_period["secondary_comment"], "secondary break")

        # Simulate user editing session comments only
        frame.active_notes.delete(0, tk.END)
        frame.active_notes.insert(0, "Updated active notes")
        frame.break_notes.delete(0, tk.END)
        frame.break_notes.insert(0, "Updated break notes")

        # Save the changes (without navigating back)
        frame.save_and_close(navigate=False)

        # Reload data and verify secondary project is STILL present
        all_data = self.tracker.load_data()
        session = all_data[session_name]

        # Verify active period still has secondary project
        active_period_data = session["active"][0]
        self.assertIn(
            "projects",
            active_period_data,
            "Active period should still have 'projects' array",
        )
        self.assertEqual(
            len(active_period_data["projects"]),
            2,
            "Active period should still have 2 projects",
        )

        # Find primary and secondary projects
        primary_project = None
        secondary_project = None
        for proj in active_period_data["projects"]:
            if proj.get("project_primary"):
                primary_project = proj
            else:
                secondary_project = proj

        self.assertIsNotNone(primary_project, "Primary project should exist")
        self.assertIsNotNone(secondary_project, "Secondary project should exist")
        self.assertEqual(primary_project["name"], "Project A")
        self.assertEqual(secondary_project["name"], "Project B")
        self.assertEqual(primary_project["comment"], "primary work")
        self.assertEqual(secondary_project["comment"], "secondary work")

        # Verify break period still has secondary action
        break_period_data = session["breaks"][0]
        self.assertIn(
            "actions",
            break_period_data,
            "Break period should still have 'actions' array",
        )
        self.assertEqual(
            len(break_period_data["actions"]),
            2,
            "Break period should still have 2 actions",
        )

        # Find primary and secondary actions
        primary_action = None
        secondary_action = None
        for action in break_period_data["actions"]:
            if action.get("break_primary"):
                primary_action = action
            else:
                secondary_action = action

        self.assertIsNotNone(primary_action, "Primary action should exist")
        self.assertIsNotNone(secondary_action, "Secondary action should exist")
        self.assertEqual(primary_action["name"], "bathroom")
        self.assertEqual(secondary_action["name"], "snack")
        self.assertEqual(primary_action["comment"], "primary break")
        self.assertEqual(secondary_action["comment"], "secondary break")

        # Verify session comments were updated
        self.assertEqual(
            session["session_comments"]["active_notes"], "Updated active notes"
        )
        self.assertEqual(
            session["session_comments"]["break_notes"], "Updated break notes"
        )


if __name__ == "__main__":
    unittest.main()
