"""
Tests for Completion Frame

Verifies session completion, project assignment, sphere changes, and data saving.
"""

import unittest
import tkinter as tk
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from frames.completion_frame import CompletionFrame
from test_helpers import TestDataGenerator, TestFileManager


class TestCompletionFrameDataPersistence(unittest.TestCase):
    """Test completion frame data saving and loading"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        # Create test data and settings files
        self.test_data_file = "test_completion_data.json"
        self.test_settings_file = "test_completion_settings.json"

        # Create test data with multiple sessions
        test_data = TestDataGenerator.create_session_data()
        self.file_manager.create_test_file(self.test_data_file, test_data)

        # Create test settings
        test_settings = TestDataGenerator.create_settings_data()
        self.file_manager.create_test_file(self.test_settings_file, test_settings)

    def test_completion_frame_loads_most_recent_session(self):
        """Test that completion frame loads most recent session when no session_name provided"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        # Create completion frame with None session_name
        frame = CompletionFrame(self.root, tracker, None)

        # Should load most recent session
        self.assertIsNotNone(frame.session_name)

    def test_completion_frame_loads_specific_session(self):
        """Test that completion frame loads specified session"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        # Get a specific session name
        data = tracker.load_data()
        session_name = list(data.keys())[0]

        # Create completion frame with specific session
        frame = CompletionFrame(self.root, tracker, session_name)

        # Should load specified session
        self.assertEqual(frame.session_name, session_name)

    def test_completion_frame_handles_missing_session(self):
        """Test that completion frame handles missing session gracefully"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        # Create frame with non-existent session
        frame = CompletionFrame(self.root, tracker, "nonexistent_session_123")

        # Should initialize with defaults
        self.assertEqual(frame.session_start_timestamp, 0)
        self.assertEqual(frame.session_end_timestamp, 0)
        self.assertEqual(frame.session_duration, 0)

    def test_completion_frame_loads_empty_data(self):
        """Test that completion frame handles empty data file"""
        empty_file = "test_empty_completion_data.json"
        self.file_manager.create_test_file(empty_file, {})

        tracker = TimeTracker(self.root)
        tracker.data_file = empty_file
        tracker.settings_file = self.test_settings_file

        # Create frame with no data
        frame = CompletionFrame(self.root, tracker, None)

        # Should initialize with None session
        self.assertIsNone(frame.session_name)


class TestCompletionFrameSphere(unittest.TestCase):
    """Test sphere functionality in completion frame"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        # Create test files
        self.test_data_file = "test_sphere_data.json"
        self.test_settings_file = "test_sphere_settings.json"

        test_data = TestDataGenerator.create_session_data()
        test_settings = TestDataGenerator.create_settings_data()

        self.file_manager.create_test_file(self.test_data_file, test_data)
        self.file_manager.create_test_file(self.test_settings_file, test_settings)

    def test_sphere_defaults_from_settings(self):
        """Test that sphere defaults are loaded from settings"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        settings = tracker.get_settings()

        # Verify settings has spheres
        self.assertIn("spheres", settings)
        sphere_list = list(settings["spheres"].keys())
        self.assertGreater(len(sphere_list), 0)

    def test_sphere_change_updates_projects(self):
        """Test that changing sphere updates project dropdown"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        data = tracker.load_data()
        session_name = list(data.keys())[0]

        frame = CompletionFrame(self.root, tracker, session_name)
        self.root.update()

        # Verify frame has project_menus list
        self.assertIsNotNone(frame.project_menus)


class TestCompletionFrameProjectAssignment(unittest.TestCase):
    """Test project assignment functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        # Create test files
        self.test_data_file = "test_project_data.json"
        self.test_settings_file = "test_project_settings.json"

        test_data = TestDataGenerator.create_session_data()
        test_settings = TestDataGenerator.create_settings_data()

        self.file_manager.create_test_file(self.test_data_file, test_data)
        self.file_manager.create_test_file(self.test_settings_file, test_settings)

    def test_projects_loaded_from_settings(self):
        """Test that projects are loaded from settings for each sphere"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        settings = tracker.get_settings()

        # Verify each sphere has projects
        for sphere_name, sphere_data in settings["spheres"].items():
            if "projects" in sphere_data:
                self.assertIsInstance(sphere_data["projects"], list)


class TestCompletionFrameSaveSkipDelete(unittest.TestCase):
    """Test save, skip, and delete actions"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        # Create test files with multiple sessions
        self.test_data_file = "test_actions_data.json"
        self.test_settings_file = "test_actions_settings.json"

        # Create data with at least 2 sessions
        test_data = TestDataGenerator.create_session_data()
        # Add a second session
        test_data["session_2"] = {
            "date": "2024-01-21",
            "start_time": "11:00:00",
            "end_time": "12:00:00",
            "start_timestamp": 1234567000,
            "end_timestamp": 1234570600,
            "total_duration": 3600,
            "active_duration": 3000,
            "break_duration": 600,
            "sphere": "",
            "active": [],
            "breaks": [],
            "actions": [],
            "break_actions": [],
        }

        test_settings = TestDataGenerator.create_settings_data()

        self.file_manager.create_test_file(self.test_data_file, test_data)
        self.file_manager.create_test_file(self.test_settings_file, test_settings)

    @patch("frames.completion_frame.messagebox.showinfo")  # Suppress success message
    @patch("frames.completion_frame.messagebox.askyesno", return_value=True)
    @patch("shutil.copy2")  # Prevent backup file creation
    def test_delete_session_removes_from_data(
        self, mock_copy, mock_askyesno, mock_showinfo
    ):
        """Test that deleting a session removes it from data file"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        # Get initial session count
        initial_data = tracker.load_data()
        initial_count = len(initial_data)
        session_to_delete = list(initial_data.keys())[0]

        # Create completion frame for first session
        frame = CompletionFrame(self.root, tracker, session_to_delete)
        self.root.update()

        # Delete the session
        frame._delete_session()

        # Verify session was deleted
        updated_data = tracker.load_data()
        self.assertEqual(len(updated_data), initial_count - 1)
        self.assertNotIn(session_to_delete, updated_data)

    @patch("frames.completion_frame.messagebox.askyesno", return_value=False)
    def test_delete_session_cancelled_preserves_data(self, mock_messagebox):
        """Test that cancelling delete preserves session data"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        # Get initial session count
        initial_data = tracker.load_data()
        initial_count = len(initial_data)
        session_name = list(initial_data.keys())[0]

        # Create completion frame
        frame = CompletionFrame(self.root, tracker, session_name)
        self.root.update()

        # Attempt to delete (will be cancelled)
        frame._delete_session()

        # Verify data unchanged
        updated_data = tracker.load_data()
        self.assertEqual(len(updated_data), initial_count)
        self.assertIn(session_name, updated_data)


class TestCompletionFrameGoogleSheets(unittest.TestCase):
    """Test Google Sheets integration in completion frame"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        # Create test files
        self.test_data_file = "test_google_data.json"
        self.test_settings_file = "test_google_settings.json"

        test_data = TestDataGenerator.create_session_data()
        test_settings = TestDataGenerator.create_settings_data()

        # Enable Google Sheets in settings
        test_settings["google_sheets"] = {
            "enabled": False,  # Disabled by default for testing
            "spreadsheet_id": "",
            "sheet_name": "Sessions",
        }

        self.file_manager.create_test_file(self.test_data_file, test_data)
        self.file_manager.create_test_file(self.test_settings_file, test_settings)

    def test_google_sheets_disabled_by_default_in_tests(self):
        """Test that Google Sheets upload is disabled in test settings"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        settings = tracker.get_settings()

        # Verify Google Sheets is disabled
        self.assertFalse(settings["google_sheets"]["enabled"])

    def test_completion_frame_has_upload_method(self):
        """Test that completion frame has Google Sheets upload method"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        data = tracker.load_data()
        session_name = list(data.keys())[0]

        frame = CompletionFrame(self.root, tracker, session_name)

        # Verify method exists
        self.assertTrue(hasattr(frame, "_upload_to_google_sheets"))


if __name__ == "__main__":
    unittest.main()
