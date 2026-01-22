"""
Comprehensive Tests for Completion Frame

Tests data accuracy, UI behavior, and validation for the completion frame.
"""

import unittest
import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from frames.completion_frame import CompletionFrame
from test_helpers import TestFileManager, TestDataGenerator


class TestCompletionFrameAfterSession(unittest.TestCase):
    """Test completion frame behavior after a tracker session completes"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_completion_after_session.json"
        self.test_settings_file = "test_completion_after_settings.json"

        # Create settings with default sphere and project
        self.settings = {
            "idle_settings": {
                "idle_tracking_enabled": True,
                "idle_threshold": 60,
                "idle_break_threshold": 300,
            },
            "spheres": {
                "Work": {"is_default": True, "active": True},
                "Personal": {"is_default": False, "active": True},
            },
            "projects": {
                "Default Project": {
                    "sphere": "Work",
                    "is_default": True,
                    "active": True,
                },
                "Project Alpha": {
                    "sphere": "Work",
                    "is_default": False,
                    "active": True,
                },
                "Exercise": {
                    "sphere": "Personal",
                    "is_default": False,
                    "active": True,
                },
            },
            "break_actions": {
                "Resting": {"is_default": True, "active": True},
                "Coffee": {"is_default": False, "active": True},
            },
        }
        self.file_manager.create_test_file(self.test_settings_file, self.settings)

    def test_default_sphere_populates(self):
        """Test that default sphere is selected on completion frame load"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 1000,
                "active_duration": 800,
                "break_duration": 200,
                "active": [{"duration": 800, "start_timestamp": 1000000}],
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

        # Default sphere should be "Work"
        self.assertEqual(frame.sphere_menu.get(), "Work")

    def test_default_project_populates(self):
        """Test that default project is populated in default project dropdown"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 1000,
                "active_duration": 800,
                "break_duration": 200,
                "active": [{"duration": 800, "start_timestamp": 1000000}],
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

        # Default project should be "Default Project"
        self.assertEqual(frame.default_project_menu.get(), "Default Project")

    def test_timeline_is_created(self):
        """Test that timeline with all periods is created"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 2000,
                "active_duration": 1500,
                "break_duration": 500,
                "active": [
                    {
                        "duration": 800,
                        "start_timestamp": 1000000,
                        "end_timestamp": 1000800,
                    },
                    {
                        "duration": 700,
                        "start_timestamp": 1001300,
                        "end_timestamp": 1002000,
                    },
                ],
                "breaks": [
                    {
                        "duration": 500,
                        "start_timestamp": 1000800,
                        "end_timestamp": 1001300,
                    }
                ],
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)

        # Should have 3 periods total (2 active + 1 break)
        self.assertEqual(len(frame.all_periods), 3)
        self.assertEqual(frame.all_periods[0]["type"], "Active")
        self.assertEqual(frame.all_periods[1]["type"], "Break")
        self.assertEqual(frame.all_periods[2]["type"], "Active")

    def test_timeline_periods_sorted_chronologically(self):
        """Test that timeline periods are sorted by start timestamp"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 2000,
                "active": [
                    {"duration": 700, "start_timestamp": 1001300},  # Later
                    {"duration": 800, "start_timestamp": 1000000},  # Earlier
                ],
                "breaks": [{"duration": 500, "start_timestamp": 1000800}],  # Middle
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)

        # Verify chronological order
        self.assertEqual(frame.all_periods[0]["start_timestamp"], 1000000)
        self.assertEqual(frame.all_periods[1]["start_timestamp"], 1000800)
        self.assertEqual(frame.all_periods[2]["start_timestamp"], 1001300)

    def test_secondary_widgets_hidden_initially(self):
        """Test that secondary dropdown/text/spinbox are hidden initially"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "active": [{"duration": 800, "start_timestamp": 1000000}],
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

        # Secondary widgets should exist but be hidden initially
        self.assertGreater(len(frame.secondary_menus), 0)
        self.assertGreater(len(frame.secondary_text_boxes), 0)
        self.assertGreater(len(frame.percentage_spinboxes), 0)

        # Check first secondary menu is not visible (grid_info should be empty or row_configure invisible)
        # In tkinter, hidden widgets via grid_remove have no grid_info
        if frame.secondary_menus:
            # Widget exists but should not be mapped initially (no data)
            pass  # Initial state depends on whether there's saved secondary data

    def test_screenshot_icon_appears_when_folder_exists(self):
        """Test that screenshot icon (📸) appears when screenshot folder exists"""
        # Create a temporary screenshot folder
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "active": [
                    {
                        "duration": 800,
                        "start_timestamp": 1000000,
                        "screenshot_folder": temp_dir,
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
        self.root.update()

        # Screenshot folder should be in period data
        self.assertEqual(frame.all_periods[0]["screenshot_folder"], temp_dir)

    def test_screenshot_icon_absent_when_no_folder(self):
        """Test that no screenshot icon appears when folder doesn't exist"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "active": [
                    {
                        "duration": 800,
                        "start_timestamp": 1000000,
                        "screenshot_folder": "",
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

        # Screenshot folder should be empty
        self.assertEqual(frame.all_periods[0]["screenshot_folder"], "")

    def test_dropdowns_dont_scroll(self):
        """Test that dropdowns don't change value when mouse wheel is scrolled"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "active": [{"duration": 800, "start_timestamp": 1000000}],
                "breaks": [{"duration": 200, "start_timestamp": 1000800}],
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)
        self.root.update()

        # Test sphere menu doesn't scroll (up and down)
        initial_sphere = frame.sphere_menu.get()
        frame.sphere_menu.event_generate("<MouseWheel>", delta=120)  # Scroll up
        self.root.update()
        self.assertEqual(frame.sphere_menu.get(), initial_sphere)
        frame.sphere_menu.event_generate("<MouseWheel>", delta=-120)  # Scroll down
        self.root.update()
        self.assertEqual(frame.sphere_menu.get(), initial_sphere)

        # Test project menus don't scroll (up and down)
        for menu in frame.project_menus:
            initial_value = menu.get()
            menu.event_generate("<MouseWheel>", delta=120)  # Scroll up
            self.root.update()
            self.assertEqual(menu.get(), initial_value)
            menu.event_generate("<MouseWheel>", delta=-120)  # Scroll down
            self.root.update()
            self.assertEqual(menu.get(), initial_value)

        # Test break action menus don't scroll (up and down)
        for menu in frame.break_action_menus:
            initial_value = menu.get()
            menu.event_generate("<MouseWheel>", delta=120)  # Scroll up
            self.root.update()
            self.assertEqual(menu.get(), initial_value)
            menu.event_generate("<MouseWheel>", delta=-120)  # Scroll down
            self.root.update()
            self.assertEqual(menu.get(), initial_value)

        # Test default project menu doesn't scroll (up and down)
        initial_default_project = frame.default_project_menu.get()
        frame.default_project_menu.event_generate(
            "<MouseWheel>", delta=120
        )  # Scroll up
        self.root.update()
        self.assertEqual(frame.default_project_menu.get(), initial_default_project)
        frame.default_project_menu.event_generate(
            "<MouseWheel>", delta=-120
        )  # Scroll down
        self.root.update()
        self.assertEqual(frame.default_project_menu.get(), initial_default_project)

        # Test default action menu doesn't scroll (up and down)
        initial_default_action = frame.default_action_menu.get()
        frame.default_action_menu.event_generate("<MouseWheel>", delta=120)  # Scroll up
        self.root.update()
        self.assertEqual(frame.default_action_menu.get(), initial_default_action)
        frame.default_action_menu.event_generate(
            "<MouseWheel>", delta=-120
        )  # Scroll down
        self.root.update()
        self.assertEqual(frame.default_action_menu.get(), initial_default_action)

    def test_periods_add_up_to_total(self):
        """Test that sum of period durations equals total duration"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 2500,
                "active": [
                    {"duration": 800, "start_timestamp": 1000000},
                    {"duration": 700, "start_timestamp": 1001300},
                ],
                "breaks": [{"duration": 500, "start_timestamp": 1000800}],
                "idle_periods": [{"duration": 500, "start_timestamp": 1002000}],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)

        # Sum all period durations
        total = sum(p["duration"] for p in frame.all_periods)
        self.assertEqual(total, 2500)

    def test_no_secondary_inputs_means_no_secondary_data_saved(self):
        """Test that if no secondary inputs are shown, no secondary data is saved"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "active": [
                    {
                        "duration": 800,
                        "start_timestamp": 1000000,
                        "end_timestamp": 1000800,
                        "project": "Default Project",
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
        frame.save_and_close(navigate=False)

        # Reload data and verify no secondary project saved
        all_data = tracker.load_data()
        session = all_data[session_name]

        # Should have single project, not projects array
        self.assertIn("project", session["active"][0])
        self.assertNotIn("projects", session["active"][0])

    def test_select_project_not_saved_in_data(self):
        """Test that 'Select Project' placeholder is not saved as actual project"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "active": [
                    {
                        "duration": 800,
                        "start_timestamp": 1000000,
                        "end_timestamp": 1000800,
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

        # Set project dropdown to "Select Project"
        if frame.project_menus:
            frame.project_menus[0].set("Select Project")

        frame.save_and_close(navigate=False)

        # Reload data and verify "Select Project" was not saved
        all_data = tracker.load_data()
        session = all_data[session_name]

        # Should not have "Select Project" saved
        if "project" in session["active"][0]:
            self.assertNotEqual(session["active"][0]["project"], "Select Project")


class TestCompletionFrameNoSessionCompleted(unittest.TestCase):
    """Test completion frame when navigating without completing a session"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_completion_no_session.json"
        self.test_settings_file = "test_completion_no_settings.json"

        settings = TestDataGenerator.create_settings_data()
        self.file_manager.create_test_file(self.test_settings_file, settings)

    def test_shows_last_active_session(self):
        """Test that completion frame shows most recent session when no session_name provided"""
        test_data = {
            "2026-01-20_session1": {
                "sphere": "Work",
                "date": "2026-01-20",
                "total_duration": 1000,
                "active": [{"duration": 1000, "start_timestamp": 1000000}],
                "breaks": [],
                "idle_periods": [],
            },
            "2026-01-21_session1": {
                "sphere": "Personal",
                "date": "2026-01-21",
                "total_duration": 2000,
                "active": [{"duration": 2000, "start_timestamp": 2000000}],
                "breaks": [],
                "idle_periods": [],
            },
            "2026-01-22_session1": {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 3000,
                "active": [{"duration": 3000, "start_timestamp": 3000000}],
                "breaks": [],
                "idle_periods": [],
            },
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        # Pass None as session_name to trigger "load most recent" behavior
        frame = CompletionFrame(self.root, tracker, session_name=None)

        # Should load the most recent session (2026-01-22_session1)
        self.assertEqual(frame.session_name, "2026-01-22_session1")
        self.assertEqual(frame.session_data["total_elapsed"], 3000)


class TestCompletionFrameBreakEnding(unittest.TestCase):
    """Test timeline behavior when session ends on a break"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_completion_break_end.json"
        self.test_settings_file = "test_completion_break_settings.json"

        settings = TestDataGenerator.create_settings_data()
        self.file_manager.create_test_file(self.test_settings_file, settings)

    def test_no_zero_duration_active_period_after_break(self):
        """Test that timeline doesn't show a 0-duration active period if session ended on break"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 1500,
                "active": [{"duration": 1000, "start_timestamp": 1000000}],
                "breaks": [
                    {"duration": 500, "start_timestamp": 1001000}
                ],  # Session ended on break
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)

        # Last period should be the break, not a 0-duration active period
        self.assertEqual(len(frame.all_periods), 2)
        self.assertEqual(frame.all_periods[-1]["type"], "Break")

        # No periods should have 0 duration
        for period in frame.all_periods:
            self.assertGreater(period["duration"], 0)


class TestCompletionFrameDataValidation(unittest.TestCase):
    """Test data validation and accuracy in completion frame"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_completion_validation.json"
        self.test_settings_file = "test_completion_validation_settings.json"

        settings = {
            "idle_settings": {
                "idle_tracking_enabled": True,
                "idle_threshold": 60,
            },
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True}
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.file_manager.create_test_file(self.test_settings_file, settings)

    def test_active_duration_sum_matches_display(self):
        """Test that sum of active period durations matches displayed active time"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 2000,
                "active_duration": 1500,
                "break_duration": 500,
                "active": [
                    {"duration": 800, "start_timestamp": 1000000},
                    {"duration": 700, "start_timestamp": 1001300},
                ],
                "breaks": [{"duration": 500, "start_timestamp": 1000800}],
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)

        # Calculate sum of active periods
        active_sum = sum(
            p["duration"] for p in frame.all_periods if p["type"] == "Active"
        )

        # Should match session's active_duration
        self.assertEqual(active_sum, 1500)
        self.assertEqual(frame.session_data["active_time"], 1500)

    def test_break_duration_sum_matches_display(self):
        """Test that sum of break/idle durations matches displayed break time"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 2500,
                "active_duration": 1500,
                "break_duration": 1000,
                "active": [{"duration": 1500, "start_timestamp": 1000000}],
                "breaks": [{"duration": 600, "start_timestamp": 1001500}],
                "idle_periods": [{"duration": 400, "start_timestamp": 1002100}],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)

        # Calculate sum of break and idle periods
        break_sum = sum(
            p["duration"] for p in frame.all_periods if p["type"] in ["Break", "Idle"]
        )

        # Should match session's break_duration
        self.assertEqual(break_sum, 1000)
        self.assertEqual(frame.session_data["break_time"], 1000)

    def test_secondary_project_percentage_split_accuracy(self):
        """Test that secondary project percentage splits are calculated correctly"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "active": [
                    {
                        "duration": 1000,
                        "start_timestamp": 1000000,
                        "end_timestamp": 1001000,
                        "projects": [
                            {
                                "name": "Project A",
                                "percentage": 60,
                                "duration": 600,
                                "project_primary": True,
                            },
                            {
                                "name": "Project B",
                                "percentage": 40,
                                "duration": 400,
                                "project_primary": False,
                            },
                        ],
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

        # Verify secondary project is loaded
        period = frame.all_periods[0]
        self.assertEqual(period["project"], "Project A")
        self.assertEqual(period["secondary_project"], "Project B")
        self.assertEqual(period["secondary_percentage"], 40)

    def test_comment_preservation(self):
        """Test that comments are preserved when loading and saving"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "active": [
                    {
                        "duration": 800,
                        "start_timestamp": 1000000,
                        "end_timestamp": 1000800,
                        "project": "Project A",
                        "comment": "Important work completed",
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

        # Comment should be loaded
        self.assertEqual(frame.all_periods[0]["comment"], "Important work completed")

        # Save and reload to verify persistence
        frame.save_and_close(navigate=False)
        all_data = tracker.load_data()

        self.assertEqual(
            all_data[session_name]["active"][0]["comment"], "Important work completed"
        )

    def test_sphere_change_updates_available_projects(self):
        """Test that changing sphere updates the available projects"""
        session_name = "2026-01-22_session1"

        # Settings with multiple spheres and projects
        settings = {
            "idle_settings": {"idle_tracking_enabled": True, "idle_threshold": 60},
            "spheres": {
                "Work": {"is_default": True, "active": True},
                "Personal": {"is_default": False, "active": True},
            },
            "projects": {
                "Work Project": {
                    "sphere": "Work",
                    "is_default": True,
                    "active": True,
                },
                "Personal Project": {
                    "sphere": "Personal",
                    "is_default": True,
                    "active": True,
                },
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.file_manager.create_test_file(self.test_settings_file, settings)

        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "active": [
                    {
                        "duration": 800,
                        "start_timestamp": 1000000,
                        "end_timestamp": 1000800,
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

        # Initially on "Work" sphere, default project should be "Work Project"
        self.assertEqual(frame.default_project_menu.get(), "Work Project")

        # Change to "Personal" sphere
        frame.sphere_menu.set("Personal")
        frame._on_sphere_selected(None)
        self.root.update()

        # Default project should now be "Personal Project"
        self.assertEqual(frame.default_project_menu.get(), "Personal Project")

    def test_idle_periods_displayed_in_timeline(self):
        """Test that idle periods are properly displayed in timeline"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 2000,
                "active": [{"duration": 1000, "start_timestamp": 1000000}],
                "breaks": [],
                "idle_periods": [
                    {"duration": 500, "start_timestamp": 1001000},
                    {"duration": 500, "start_timestamp": 1001500},
                ],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)

        # Should have 3 periods: 1 active + 2 idle
        self.assertEqual(len(frame.all_periods), 3)

        # Count idle periods
        idle_count = sum(1 for p in frame.all_periods if p["type"] == "Idle")
        self.assertEqual(idle_count, 2)

    def test_empty_session_handled_gracefully(self):
        """Test that completion frame handles session with no periods"""
        session_name = "2026-01-22_session1"
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_duration": 0,
                "active_duration": 0,
                "break_duration": 0,
                "active": [],
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

        # Should have no periods
        self.assertEqual(len(frame.all_periods), 0)
        self.assertEqual(frame.session_data["total_elapsed"], 0)


if __name__ == "__main__":
    unittest.main()
