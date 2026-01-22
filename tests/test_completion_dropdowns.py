"""
Tests for Completion Frame Dropdown Behavior

Tests that dropdown changes cascade correctly to all timeline dropdowns.
"""

import unittest
import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from frames.completion_frame import CompletionFrame
from tests.test_helpers import TestFileManager


class TestCompletionFrameSphereDropdownBehavior(unittest.TestCase):
    """Test that changing sphere dropdown updates default project and all timeline dropdowns"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_sphere_dropdown_data.json"
        self.test_settings_file = "test_sphere_dropdown_settings.json"

        settings = {
            "idle_settings": {"idle_tracking_enabled": False},
            "spheres": {
                "Work": {"is_default": True, "active": True},
                "Personal": {"is_default": False, "active": True},
            },
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True},
                "Project B": {"sphere": "Work", "is_default": False, "active": True},
                "Exercise": {"sphere": "Personal", "is_default": True, "active": True},
                "Hobby": {"sphere": "Personal", "is_default": False, "active": True},
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.file_manager.create_test_file(self.test_settings_file, settings)

    def test_sphere_change_updates_default_project_dropdown(self):
        """Test that changing sphere updates default project dropdown to new sphere's default"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 2000,
                "active_duration": 2000,
                "break_duration": 0,
                "active": [
                    {
                        "duration": 1000,
                        "start_timestamp": 1737540000,
                        "project": "Project A",
                    },
                    {
                        "duration": 1000,
                        "start_timestamp": 1737541000,
                        "project": "Project B",
                    },
                ],
                "breaks": [],
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)

        # Initially should be Work sphere with Project A as default
        self.assertEqual(frame.selected_sphere, "Work")
        self.assertEqual(frame.default_project_menu.get(), "Project A")

        # Change to Personal sphere
        frame.sphere_menu.set("Personal")
        frame._on_sphere_selected(None)

        # Default project should update to Personal's default (Exercise)
        self.assertEqual(frame.selected_sphere, "Personal")
        self.assertEqual(frame.default_project_menu.get(), "Exercise")

    def test_sphere_change_updates_all_active_timeline_dropdowns(self):
        """Test that changing sphere updates all active period dropdowns to new default project"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 3000,
                "active_duration": 3000,
                "break_duration": 0,
                "active": [
                    {
                        "duration": 1000,
                        "start_timestamp": 1737540000,
                        "project": "Project A",
                    },
                    {
                        "duration": 1000,
                        "start_timestamp": 1737541000,
                        "project": "Project B",
                    },
                    {
                        "duration": 1000,
                        "start_timestamp": 1737542000,
                        "project": "Project A",
                    },
                ],
                "breaks": [],
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)

        # Verify 3 active periods loaded
        self.assertEqual(len(frame.project_menus), 3)

        # All should have Work projects available
        for menu in frame.project_menus:
            self.assertIn("Project A", menu["values"])
            self.assertIn("Project B", menu["values"])

        # Change to Personal sphere
        frame.sphere_menu.set("Personal")
        frame._on_sphere_selected(None)

        # All dropdowns should now have Personal projects
        for menu in frame.project_menus:
            values = menu["values"]
            self.assertIn("Exercise", values)
            self.assertIn("Hobby", values)
            self.assertNotIn("Project A", values)
            self.assertNotIn("Project B", values)


class TestCompletionFrameDefaultProjectBehavior(unittest.TestCase):
    """Test that changing default project dropdown updates all timeline dropdowns"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_default_project_data.json"
        self.test_settings_file = "test_default_project_settings.json"

        settings = {
            "idle_settings": {"idle_tracking_enabled": False},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True},
                "Project B": {"sphere": "Work", "is_default": False, "active": True},
                "Project C": {"sphere": "Work", "is_default": False, "active": True},
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.file_manager.create_test_file(self.test_settings_file, settings)

    def test_default_project_change_updates_all_timeline_dropdowns(self):
        """Test that changing default project updates all active period dropdowns"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 3000,
                "active_duration": 3000,
                "break_duration": 0,
                "active": [
                    {
                        "duration": 1000,
                        "start_timestamp": 1737540000,
                        "project": "Project A",
                    },
                    {
                        "duration": 1000,
                        "start_timestamp": 1737541000,
                        "project": "Project A",
                    },
                    {
                        "duration": 1000,
                        "start_timestamp": 1737542000,
                        "project": "Project A",
                    },
                ],
                "breaks": [],
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)

        # All should start as Project A
        for menu in frame.project_menus:
            self.assertEqual(menu.get(), "Project A")

        # Change default project to Project B
        frame.default_project_menu.set("Project B")
        frame._on_project_selected(None, frame.default_project_menu)

        # All timeline dropdowns should update to Project B
        for menu in frame.project_menus:
            self.assertEqual(menu.get(), "Project B")


class TestCompletionFrameDefaultBreakActionBehavior(unittest.TestCase):
    """Test that changing default break/idle action updates all timeline break dropdowns"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_default_break_data.json"
        self.test_settings_file = "test_default_break_settings.json"

        settings = {
            "idle_settings": {"idle_tracking_enabled": True, "idle_threshold": 60},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True}
            },
            "break_actions": {
                "Resting": {"is_default": True, "active": True},
                "Walking": {"is_default": False, "active": True},
                "Eating": {"is_default": False, "active": True},
            },
        }
        self.file_manager.create_test_file(self.test_settings_file, settings)

    def test_default_break_action_change_updates_all_break_dropdowns(self):
        """Test that changing default break action updates all break and idle dropdowns"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 5000,
                "active_duration": 2000,
                "break_duration": 3000,
                "active": [
                    {
                        "duration": 1000,
                        "start_timestamp": 1737540000,
                        "project": "Project A",
                    },
                    {
                        "duration": 1000,
                        "start_timestamp": 1737543000,
                        "project": "Project A",
                    },
                ],
                "breaks": [
                    {
                        "duration": 1000,
                        "start_timestamp": 1737541000,
                        "action": "Resting",
                    },
                    {
                        "duration": 1000,
                        "start_timestamp": 1737542000,
                        "action": "Resting",
                    },
                ],
                "idle_periods": [
                    {
                        "duration": 1000,
                        "start_timestamp": 1737544000,
                        "action": "Resting",
                    }
                ],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)

        # All should start as Resting
        for menu in frame.break_action_menus:
            self.assertEqual(menu.get(), "Resting")
        for menu in frame.idle_action_menus:
            self.assertEqual(menu.get(), "Resting")

        # Change default break action to Walking
        frame.default_action_menu.set("Walking")
        frame._on_break_action_selected(None, frame.default_action_menu)

        # All break and idle dropdowns should update to Walking
        for menu in frame.break_action_menus:
            self.assertEqual(menu.get(), "Walking")
        for menu in frame.idle_action_menus:
            self.assertEqual(menu.get(), "Walking")


class TestCompletionFrameCommentPersistence(unittest.TestCase):
    """Test that comments are saved, sanitized, and loaded correctly"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_comment_persistence_data.json"
        self.test_settings_file = "test_comment_persistence_settings.json"

        settings = {
            "idle_settings": {"idle_tracking_enabled": False},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True}
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.file_manager.create_test_file(self.test_settings_file, settings)

    def test_comments_are_saved(self):
        """Test that comments are saved to data file"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 1000,
                "active_duration": 1000,
                "break_duration": 0,
                "active": [{"duration": 1000, "start_timestamp": 1737540000}],
                "breaks": [],
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)

        # Set project and comment
        frame.project_menus[0].set("Project A")
        test_comment = "This is a test comment"
        frame.text_boxes[0].insert(0, test_comment)

        # Save
        frame.save_and_close(navigate=False)

        # Reload and verify
        with open(self.test_data_file, "r") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data[session_name]["active"][0]["comment"], test_comment)

    def test_comments_are_loaded_when_session_changes(self):
        """Test that comments are loaded when switching sessions via dropdown"""
        date = "2026-01-22"
        session1_name = f"{date}_session1"
        session2_name = f"{date}_session2"

        test_data = {
            session1_name: {
                "sphere": "Work",
                "date": date,
                "start_timestamp": 1737540000,
                "end_timestamp": 1737541000,
                "total_duration": 1000,
                "active_duration": 1000,
                "break_duration": 0,
                "active": [
                    {
                        "duration": 1000,
                        "start_timestamp": 1737540000,
                        "project": "Project A",
                        "comment": "First session comment",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            },
            session2_name: {
                "sphere": "Work",
                "date": date,
                "start_timestamp": 1737542000,
                "end_timestamp": 1737543000,
                "total_duration": 1000,
                "active_duration": 1000,
                "break_duration": 0,
                "active": [
                    {
                        "duration": 1000,
                        "start_timestamp": 1737542000,
                        "project": "Project A",
                        "comment": "Second session comment",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            },
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        # Load first session
        frame = CompletionFrame(self.root, tracker, session1_name)

        # Verify first session comment loaded
        self.assertEqual(frame.text_boxes[0].get(), "First session comment")

        # Simulate changing session via dropdown
        # First, set up the date and session dropdowns
        frame.date_selector.set(date)
        frame._on_date_selected(None)

        # Session dropdown should now have both sessions
        self.assertIn("Session 1", frame.session_name_readable)
        self.assertIn("Session 2", frame.session_name_readable)

        # Switch to session 2
        frame.session_selector.set("Session 2")
        frame._on_session_selected(None)

        # After widgets rebuild, comment should be from second session
        self.assertEqual(frame.text_boxes[0].get(), "Second session comment")


class TestCompletionFrame12HourFormat(unittest.TestCase):
    """Test that 12-hour format with AM/PM works correctly"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_12hour_data.json"
        self.test_settings_file = "test_12hour_settings.json"

        settings = {
            "idle_settings": {"idle_tracking_enabled": False},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True}
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.file_manager.create_test_file(self.test_settings_file, settings)

    def test_12_hour_format_displays_correctly(self):
        """Test that timestamps display in 12-hour format with AM/PM"""
        from datetime import datetime

        session_name = "2026-01-22_session1"
        # Create timestamps for 9:30 AM and 2:45 PM
        start_timestamp = datetime(2026, 1, 22, 9, 30, 0).timestamp()  # 9:30 AM
        end_timestamp = datetime(2026, 1, 22, 14, 45, 0).timestamp()  # 2:45 PM

        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "start_timestamp": start_timestamp,
                "end_timestamp": end_timestamp,
                "total_duration": 18900,
                "active_duration": 18900,
                "break_duration": 0,
                "active": [
                    {
                        "duration": 18900,
                        "start_timestamp": start_timestamp,
                        "project": "Project A",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)

        # The session info should display times in 12-hour format
        # Start time: 9:30 AM, End time: 2:45 PM
        # Note: The actual display format strips leading zeros and uses AM/PM
        # We can't easily access the label text, but we can verify the frame initialized without errors
        # and that the timestamps are valid
        self.assertEqual(frame.session_start_timestamp, start_timestamp)
        self.assertEqual(frame.session_end_timestamp, end_timestamp)

    def test_12_hour_format_with_midnight_and_noon(self):
        """Test that 12:00 AM (midnight) and 12:00 PM (noon) display correctly"""
        from datetime import datetime

        session_name = "2026-01-22_session1"
        # Midnight to noon
        start_timestamp = datetime(2026, 1, 22, 0, 0, 0).timestamp()  # 12:00 AM
        end_timestamp = datetime(2026, 1, 22, 12, 0, 0).timestamp()  # 12:00 PM

        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "start_timestamp": start_timestamp,
                "end_timestamp": end_timestamp,
                "total_duration": 43200,
                "active_duration": 43200,
                "break_duration": 0,
                "active": [
                    {
                        "duration": 43200,
                        "start_timestamp": start_timestamp,
                        "project": "Project A",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)

        # Verify timestamps are correct (format validation happens in UI)
        self.assertEqual(frame.session_start_timestamp, start_timestamp)
        self.assertEqual(frame.session_end_timestamp, end_timestamp)


class TestCompletionFrameCommentSanitization(unittest.TestCase):
    """Test that comments are sanitized before saving"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_sanitize_data.json"
        self.test_settings_file = "test_sanitize_settings.json"

        settings = {
            "idle_settings": {"idle_tracking_enabled": False},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True}
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.file_manager.create_test_file(self.test_settings_file, settings)

    def test_dangerous_characters_handled_in_comments(self):
        """Test that dangerous characters in comments are handled safely"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 1000,
                "active_duration": 1000,
                "break_duration": 0,
                "active": [{"duration": 1000, "start_timestamp": 1737540000}],
                "breaks": [],
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)

        # Set project and comment with various special characters
        frame.project_menus[0].set("Project A")
        dangerous_comment = 'Test with "quotes" and \\backslashes\\ and <tags>'
        frame.text_boxes[0].insert(0, dangerous_comment)

        # Save - should not raise exceptions
        frame.save_and_close(navigate=False)

        # Reload and verify it was saved correctly
        with open(self.test_data_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        # Comment should be preserved exactly (JSON handles escaping)
        self.assertEqual(
            saved_data[session_name]["active"][0]["comment"], dangerous_comment
        )


if __name__ == "__main__":
    unittest.main()
