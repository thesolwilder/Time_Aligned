"""
Tests for inactive project display in completion frame

Bug: When viewing a session with an inactive project, the completion frame should
still populate the dropdowns with the inactive project, not the default project.
Historical sessions must display correctly regardless of current active/inactive status.
"""

import unittest
import tkinter as tk
from tkinter import ttk
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from src.completion_frame import CompletionFrame
from test_helpers import TestFileManager, TestDataGenerator


class TestInactiveProjectInCompletionFrame(unittest.TestCase):
    """Test that inactive projects still populate in session completion frame"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)

        # Create test settings/data files
        self.settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_settings.json", self.settings
        )
        self.test_data_file = self.file_manager.create_test_file("test_data.json", {})

    def tearDown(self):
        """Clean up after tests"""
        from test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_inactive_project_displays_in_session_completion_frame(self):
        """Test that session project displays even if project is now inactive

        Workflow:
        1. Create a session with active sphere and active project
        2. Save the session
        3. Mark that project as inactive in settings (simulating archiving)
        4. Open completion frame for that session
        5. Assert: Default project dropdown and active periods dropdown
           should show the inactive project, not the default project
        """
        # Set up initial settings with active project
        self.settings["spheres"]["Work"] = {"is_default": True, "active": True}
        self.settings["projects"]["Active Project"] = {
            "sphere": "Work",
            "is_default": True,
            "active": True,
        }
        self.settings["projects"]["Will Become Inactive"] = {
            "sphere": "Work",
            "is_default": False,
            "active": True,  # Active during session creation
        }
        self.file_manager.create_test_file(self.test_settings_file, self.settings)

        # Create a session with the project while it's active
        session_name = "2026-02-08_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-02-08",
                "start_time": "10:00:00 AM",
                "start_timestamp": 1707390000,
                "end_time": "10:05:00 AM",
                "end_timestamp": 1707390300,
                "total_duration": 300,
                "active_duration": 300,
                "break_duration": 0,
                "active": [
                    {
                        "start": "10:00:00 AM",
                        "start_timestamp": 1707390000,
                        "end": "10:02:00 AM",
                        "end_timestamp": 1707390120,
                        "duration": 120,
                        "project": "Will Become Inactive",
                        "comment": "Working on this project",
                    },
                    {
                        "start": "10:02:00 AM",
                        "start_timestamp": 1707390120,
                        "end": "10:05:00 AM",
                        "end_timestamp": 1707390300,
                        "duration": 180,
                        "project": "Will Become Inactive",
                        "comment": "Still working",
                    },
                ],
                "breaks": [],
                "idle_periods": [],
                "session_comments": {
                    "active_notes": "",
                    "break_notes": "",
                    "idle_notes": "",
                    "session_notes": "Testing inactive project display",
                },
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        # Now mark the project as inactive (simulate archiving)
        self.settings["projects"]["Will Become Inactive"]["active"] = False
        self.file_manager.create_test_file(self.test_settings_file, self.settings)

        # Load tracker with updated settings
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        # Open completion frame for the session
        frame = CompletionFrame(self.root, tracker, session_name)
        self.root.update()

        # BUG: Frame shows "Active Project" (default) instead of "Will Become Inactive"
        # After fix: Should show the session's actual project even though it's now inactive

        # Check default project dropdown
        self.assertEqual(
            frame.default_project_menu.get(),
            "Will Become Inactive",
            "Default project dropdown should show inactive project from session",
        )

        # Check that inactive project is in dropdown options
        self.assertIn(
            "Will Become Inactive",
            frame.default_project_menu["values"],
            "Inactive project should be in dropdown options",
        )

        # Check all active period dropdowns (should have 2)
        self.assertEqual(
            len(frame.project_menus), 2, "Should have 2 active period dropdowns"
        )

        # Both active periods should show the inactive project
        for idx, menu in enumerate(frame.project_menus):
            self.assertEqual(
                menu.get(),
                "Will Become Inactive",
                f"Active period {idx + 1} dropdown should show inactive project",
            )
            self.assertIn(
                "Will Become Inactive",
                menu["values"],
                f"Inactive project should be in active period {idx + 1} dropdown options",
            )


if __name__ == "__main__":
    unittest.main()
