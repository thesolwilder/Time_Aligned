"""
Priority Tests for Completion Frame

Tests for critical functionality: save and close, percentage validation,
add/remove secondary projects, comment special characters, and multiple secondary projects.
"""

import unittest
import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from src.completion_frame import CompletionFrame
from tests.test_helpers import TestFileManager


class TestCompletionFrameSaveAndClose(unittest.TestCase):
    """Test save and close functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        # Create test data and settings
        test_data = {}
        settings = {
            "idle_settings": {"idle_tracking_enabled": False},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True},
                "Project B": {"sphere": "Work", "is_default": False, "active": True},
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }

        self.test_data_file = self.file_manager.create_test_file(
            "test_save_data.json", test_data
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_save_settings.json", settings
        )

    def test_save_single_project_writes_correctly(self):
        """Test that saving a single project writes data correctly"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 1800,
                "active_duration": 1800,
                "break_duration": 0,
                "active": [{"duration": 1800, "start_timestamp": 1737540000}],
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
        frame.text_boxes[0].insert(0, "Test comment")

        # Save without navigation
        frame.save_and_close(navigate=False)

        # Verify data was saved
        with open(self.test_data_file, "r") as f:
            saved_data = json.load(f)

        active_period = saved_data[session_name]["active"][0]
        self.assertEqual(active_period["project"], "Project A")
        self.assertEqual(active_period["comment"], "Test comment")
        self.assertNotIn("projects", active_period)  # Should not have projects array

    def test_save_secondary_project_writes_array(self):
        """Test that saving with secondary project creates projects array"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 2000,
                "active_duration": 2000,
                "break_duration": 0,
                "active": [{"duration": 2000, "start_timestamp": 1737540000}],
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

        # Set primary project
        frame.project_menus[0].set("Project A")
        frame.text_boxes[0].insert(0, "Primary work")

        # Toggle secondary and set it
        frame._toggle_secondary(0)
        frame.secondary_menus[0].set("Project B")
        frame.secondary_text_boxes[0].insert(0, "Secondary work")
        frame.percentage_spinboxes[0].set(40)  # Project B gets 40%, A gets 60%

        # Save without navigation
        frame.save_and_close(navigate=False)

        # Verify data was saved as array
        with open(self.test_data_file, "r") as f:
            saved_data = json.load(f)

        active_period = saved_data[session_name]["active"][0]
        self.assertIn("projects", active_period)
        self.assertEqual(len(active_period["projects"]), 2)

        # Check primary project (60%)
        primary = [p for p in active_period["projects"] if p.get("project_primary")][0]
        self.assertEqual(primary["name"], "Project A")
        self.assertEqual(primary["percentage"], 60)
        self.assertEqual(primary["duration"], 1200)  # 60% of 2000
        self.assertEqual(primary["comment"], "Primary work")

        # Check secondary project (40%)
        secondary = [
            p for p in active_period["projects"] if not p.get("project_primary")
        ][0]
        self.assertEqual(secondary["name"], "Project B")
        self.assertEqual(secondary["percentage"], 40)
        self.assertEqual(secondary["duration"], 800)  # 40% of 2000
        self.assertEqual(secondary["comment"], "Secondary work")

    def test_save_preserves_sphere_change(self):
        """Test that changing sphere is saved correctly"""
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

        # Add Personal sphere
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)
        settings["spheres"]["Personal"] = {"is_default": False, "active": True}
        settings["projects"]["Exercise"] = {
            "sphere": "Personal",
            "is_default": True,
            "active": True,
        }
        with open(self.test_settings_file, "w") as f:
            json.dump(settings, f, indent=2)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)

        # Change sphere
        frame.selected_sphere = "Personal"
        frame.save_and_close(navigate=False)

        # Verify sphere was saved
        with open(self.test_data_file, "r") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data[session_name]["sphere"], "Personal")

    def test_save_break_with_secondary_action(self):
        """Test that breaks with secondary actions are saved correctly"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 1000,
                "active_duration": 0,
                "break_duration": 1000,
                "active": [],
                "breaks": [{"duration": 1000, "start_timestamp": 1737540000}],
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        # Add second break action
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)
        settings["break_actions"]["Walking"] = {"is_default": False, "active": True}
        with open(self.test_settings_file, "w") as f:
            json.dump(settings, f, indent=2)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)

        # Set primary break action
        frame.break_action_menus[0].set("Resting")
        frame.text_boxes[0].insert(0, "Sitting")

        # Toggle secondary and set it
        frame._toggle_secondary(0)
        frame.secondary_menus[0].set("Walking")
        frame.secondary_text_boxes[0].insert(0, "Strolling")
        frame.percentage_spinboxes[0].set(30)  # Walking gets 30%, Resting gets 70%

        # Save without navigation
        frame.save_and_close(navigate=False)

        # Verify data was saved as array
        with open(self.test_data_file, "r") as f:
            saved_data = json.load(f)

        break_period = saved_data[session_name]["breaks"][0]
        self.assertIn("actions", break_period)
        self.assertEqual(len(break_period["actions"]), 2)

        # Check primary (70%)
        primary = [a for a in break_period["actions"] if a.get("break_primary")][0]
        self.assertEqual(primary["name"], "Resting")
        self.assertEqual(primary["percentage"], 70)
        self.assertEqual(primary["duration"], 700)

        # Check secondary (30%)
        secondary = [a for a in break_period["actions"] if not a.get("break_primary")][
            0
        ]
        self.assertEqual(secondary["name"], "Walking")
        self.assertEqual(secondary["percentage"], 30)
        self.assertEqual(secondary["duration"], 300)


class TestCompletionFramePercentageValidation(unittest.TestCase):
    """Test percentage validation and calculations"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        # Create test data and settings
        test_data = {}
        settings = {
            "idle_settings": {"idle_tracking_enabled": False},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True},
                "Project B": {"sphere": "Work", "is_default": False, "active": True},
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }

        self.test_data_file = self.file_manager.create_test_file(
            "test_percentage_data.json", test_data
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_percentage_settings.json", settings
        )

    def test_percentage_split_50_50(self):
        """Test 50/50 percentage split"""
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

        frame.project_menus[0].set("Project A")
        frame._toggle_secondary(0)
        frame.secondary_menus[0].set("Project B")
        frame.percentage_spinboxes[0].set(50)

        frame.save_and_close(navigate=False)

        with open(self.test_data_file, "r") as f:
            saved_data = json.load(f)

        projects = saved_data[session_name]["active"][0]["projects"]
        self.assertEqual(projects[0]["percentage"], 50)
        self.assertEqual(projects[0]["duration"], 500)
        self.assertEqual(projects[1]["percentage"], 50)
        self.assertEqual(projects[1]["duration"], 500)

    def test_percentage_split_25_75(self):
        """Test 25/75 percentage split"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 2000,
                "active_duration": 2000,
                "break_duration": 0,
                "active": [{"duration": 2000, "start_timestamp": 1737540000}],
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

        frame.project_menus[0].set("Project A")
        frame._toggle_secondary(0)
        frame.secondary_menus[0].set("Project B")
        frame.percentage_spinboxes[0].set(25)  # Project B gets 25%

        frame.save_and_close(navigate=False)

        with open(self.test_data_file, "r") as f:
            saved_data = json.load(f)

        projects = saved_data[session_name]["active"][0]["projects"]

        # Primary gets 75%
        primary = [p for p in projects if p.get("project_primary")][0]
        self.assertEqual(primary["percentage"], 75)
        self.assertEqual(primary["duration"], 1500)

        # Secondary gets 25%
        secondary = [p for p in projects if not p.get("project_primary")][0]
        self.assertEqual(secondary["percentage"], 25)
        self.assertEqual(secondary["duration"], 500)

    def test_percentage_duration_rounding(self):
        """Test that duration rounding works correctly for odd percentages"""
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

        frame.project_menus[0].set("Project A")
        frame._toggle_secondary(0)
        frame.secondary_menus[0].set("Project B")
        frame.percentage_spinboxes[0].set(33)  # 33% for B, 67% for A

        frame.save_and_close(navigate=False)

        with open(self.test_data_file, "r") as f:
            saved_data = json.load(f)

        projects = saved_data[session_name]["active"][0]["projects"]

        # Check that durations are integers (no fractional seconds)
        self.assertIsInstance(projects[0]["duration"], int)
        self.assertIsInstance(projects[1]["duration"], int)

        # 67% of 1000 = 670, 33% of 1000 = 330
        self.assertEqual(projects[0]["duration"], 670)
        self.assertEqual(projects[1]["duration"], 330)


class TestCompletionFrameAddRemoveSecondary(unittest.TestCase):
    """Test add/remove secondary project functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        # Create test data and settings
        test_data = {}
        settings = {
            "idle_settings": {"idle_tracking_enabled": False},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True},
                "Project B": {"sphere": "Work", "is_default": False, "active": True},
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }

        self.test_data_file = self.file_manager.create_test_file(
            "test_toggle_data.json", test_data
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_toggle_settings.json", settings
        )

    def test_toggle_shows_secondary_widgets(self):
        """Test that toggling + shows secondary widgets"""
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

        # Initially button should be +
        self.assertEqual(frame.toggle_buttons[0].cget("text"), "+")

        # Toggle to show
        frame._toggle_secondary(0)

        # Button should change to -
        self.assertEqual(frame.toggle_buttons[0].cget("text"), "−")

        # Secondary widgets should now have valid values set
        self.assertEqual(frame.secondary_menus[0].get(), "Select A Project")
        self.assertEqual(frame.percentage_spinboxes[0].get(), "50")

    def test_toggle_hides_secondary_widgets(self):
        """Test that toggling - hides secondary widgets and clears data"""
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

        # Show secondary first
        frame._toggle_secondary(0)
        frame.secondary_menus[0].set("Project B")
        frame.secondary_text_boxes[0].insert(0, "Test data")
        frame.percentage_spinboxes[0].set(40)

        # Verify data is set
        self.assertEqual(frame.secondary_menus[0].get(), "Project B")
        self.assertEqual(frame.secondary_text_boxes[0].get(), "Test data")
        self.assertEqual(int(frame.percentage_spinboxes[0].get()), 40)

        # Toggle to hide
        frame._toggle_secondary(0)

        # Button should be back to +
        self.assertEqual(frame.toggle_buttons[0].cget("text"), "+")

        # Data should be cleared
        self.assertEqual(frame.secondary_menus[0].get(), "")
        self.assertEqual(frame.secondary_text_boxes[0].get(), "")
        self.assertEqual(
            int(frame.percentage_spinboxes[0].get()), 50
        )  # Reset to default

    def test_secondary_not_saved_when_hidden(self):
        """Test that secondary data is not saved when widgets are hidden"""
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

        # Set primary project
        frame.project_menus[0].set("Project A")

        # Don't toggle secondary - leave it hidden

        # Save
        frame.save_and_close(navigate=False)

        # Verify only single project saved
        with open(self.test_data_file, "r") as f:
            saved_data = json.load(f)

        active_period = saved_data[session_name]["active"][0]
        self.assertEqual(active_period["project"], "Project A")
        self.assertNotIn("projects", active_period)


class TestCompletionFrameCommentSpecialCharacters(unittest.TestCase):
    """Test comment handling with special characters"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        # Create test data and settings
        test_data = {}
        settings = {
            "idle_settings": {"idle_tracking_enabled": False},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True}
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }

        self.test_data_file = self.file_manager.create_test_file(
            "test_comment_data.json", test_data
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_comment_settings.json", settings
        )

    def test_comment_with_quotes(self):
        """Test that comments with quotes are saved correctly"""
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

        frame.project_menus[0].set("Project A")
        frame.text_boxes[0].insert(0, 'Test "quoted" text')

        frame.save_and_close(navigate=False)

        with open(self.test_data_file, "r") as f:
            saved_data = json.load(f)

        self.assertEqual(
            saved_data[session_name]["active"][0]["comment"], 'Test "quoted" text'
        )

    def test_comment_with_newlines(self):
        """Test that comments with newlines are preserved"""
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

        frame.project_menus[0].set("Project A")
        # Note: Entry widgets don't support multi-line, but test the data flow
        comment_text = "Line 1\nLine 2\nLine 3"
        frame.text_boxes[0].insert(0, comment_text)

        frame.save_and_close(navigate=False)

        with open(self.test_data_file, "r") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data[session_name]["active"][0]["comment"], comment_text)

    def test_comment_with_unicode_emoji(self):
        """Test that comments with emoji are saved correctly"""
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

        frame.project_menus[0].set("Project A")
        frame.text_boxes[0].insert(0, "Great work! 🎉✨💪")

        frame.save_and_close(navigate=False)

        with open(self.test_data_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.assertEqual(
            saved_data[session_name]["active"][0]["comment"], "Great work! 🎉✨💪"
        )

    def test_comment_with_special_json_characters(self):
        """Test that comments with JSON special characters are handled"""
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

        frame.project_menus[0].set("Project A")
        # Backslash, quotes, and control characters
        frame.text_boxes[0].insert(0, r'Test \ / " { } [ ]')

        frame.save_and_close(navigate=False)

        with open(self.test_data_file, "r") as f:
            saved_data = json.load(f)

        self.assertEqual(
            saved_data[session_name]["active"][0]["comment"], r'Test \ / " { } [ ]'
        )

    def test_very_long_comment(self):
        """Test that very long comments are saved correctly"""
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

        frame.project_menus[0].set("Project A")
        long_comment = "A" * 1000  # 1000 character comment
        frame.text_boxes[0].insert(0, long_comment)

        frame.save_and_close(navigate=False)

        with open(self.test_data_file, "r") as f:
            saved_data = json.load(f)

        self.assertEqual(len(saved_data[session_name]["active"][0]["comment"]), 1000)
        self.assertEqual(saved_data[session_name]["active"][0]["comment"], long_comment)


class TestCompletionFrameMultipleSecondaryProjects(unittest.TestCase):
    """Test scenarios with multiple periods having secondary projects"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        # Create test data and settings
        test_data = {}
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

        self.test_data_file = self.file_manager.create_test_file(
            "test_multi_secondary_data.json", test_data
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_multi_secondary_settings.json", settings
        )

    def test_multiple_periods_with_different_secondaries(self):
        """Test saving multiple periods each with different secondary projects"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 3000,
                "active_duration": 3000,
                "break_duration": 0,
                "active": [
                    {"duration": 1000, "start_timestamp": 1737540000},
                    {"duration": 2000, "start_timestamp": 1737541000},
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

        # First period: A (70%) + B (30%)
        frame.project_menus[0].set("Project A")
        frame._toggle_secondary(0)
        frame.secondary_menus[0].set("Project B")
        frame.percentage_spinboxes[0].set(30)

        # Second period: B (60%) + C (40%)
        frame.project_menus[1].set("Project B")
        frame._toggle_secondary(1)
        frame.secondary_menus[1].set("Project C")
        frame.percentage_spinboxes[1].set(40)

        frame.save_and_close(navigate=False)

        with open(self.test_data_file, "r") as f:
            saved_data = json.load(f)

        active_periods = saved_data[session_name]["active"]

        # Check first period
        period1 = active_periods[0]
        self.assertEqual(len(period1["projects"]), 2)
        self.assertEqual(period1["projects"][0]["name"], "Project A")
        self.assertEqual(period1["projects"][0]["percentage"], 70)
        self.assertEqual(period1["projects"][0]["duration"], 700)
        self.assertEqual(period1["projects"][1]["name"], "Project B")
        self.assertEqual(period1["projects"][1]["percentage"], 30)
        self.assertEqual(period1["projects"][1]["duration"], 300)

        # Check second period
        period2 = active_periods[1]
        self.assertEqual(len(period2["projects"]), 2)
        self.assertEqual(period2["projects"][0]["name"], "Project B")
        self.assertEqual(period2["projects"][0]["percentage"], 60)
        self.assertEqual(period2["projects"][0]["duration"], 1200)
        self.assertEqual(period2["projects"][1]["name"], "Project C")
        self.assertEqual(period2["projects"][1]["percentage"], 40)
        self.assertEqual(period2["projects"][1]["duration"], 800)

    def test_some_periods_with_secondary_some_without(self):
        """Test session with mix of single and split project periods"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 4000,
                "active_duration": 4000,
                "break_duration": 0,
                "active": [
                    {"duration": 1000, "start_timestamp": 1737540000},
                    {"duration": 1500, "start_timestamp": 1737541000},
                    {"duration": 1500, "start_timestamp": 1737542500},
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

        # First period: Single project
        frame.project_menus[0].set("Project A")

        # Second period: Split A (50%) + B (50%)
        frame.project_menus[1].set("Project A")
        frame._toggle_secondary(1)
        frame.secondary_menus[1].set("Project B")
        frame.percentage_spinboxes[1].set(50)

        # Third period: Single project
        frame.project_menus[2].set("Project C")

        frame.save_and_close(navigate=False)

        with open(self.test_data_file, "r") as f:
            saved_data = json.load(f)

        active_periods = saved_data[session_name]["active"]

        # First period should be single project
        self.assertEqual(active_periods[0]["project"], "Project A")
        self.assertNotIn("projects", active_periods[0])

        # Second period should be split
        self.assertIn("projects", active_periods[1])
        self.assertEqual(len(active_periods[1]["projects"]), 2)

        # Third period should be single project
        self.assertEqual(active_periods[2]["project"], "Project C")
        self.assertNotIn("projects", active_periods[2])


if __name__ == "__main__":
    unittest.main()
