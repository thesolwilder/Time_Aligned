"""
Test button navigation and frame transitions
Tests that buttons properly navigate between frames
"""

import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from time_tracker import TimeTracker
from frames.completion_frame import CompletionFrame
from test_helpers import TestFileManager


class TestButtonNavigation(unittest.TestCase):
    """Test that buttons properly navigate between frames"""

    def setUp(self):
        """Set up test fixtures"""
        from test_helpers import TestDataGenerator

        self.file_manager = TestFileManager()
        self.test_data_file = "test_navigation_data.json"
        self.test_settings_file = "test_navigation_settings.json"

        # Create test settings file
        settings = TestDataGenerator.create_settings_data()
        self.file_manager.create_test_file(self.test_settings_file, settings)

        self.root = tk.Tk()
        self.tracker = TimeTracker(self.root)

        # Override file paths to use test files
        self.tracker.data_file = self.test_data_file
        self.tracker.settings_file = self.test_settings_file

    def tearDown(self):
        """Clean up after tests"""
        try:
            self.root.destroy()
        except:
            pass

        # Clean up test files
        self.file_manager.cleanup()

        # Also clean up any test files that might have been created in parent directory
        import os

        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for test_file in [self.test_data_file, self.test_settings_file]:
            test_path = os.path.join(parent_dir, test_file)
            if os.path.exists(test_path):
                os.remove(test_path)

    def test_save_and_close_returns_to_main(self):
        """Test that Save & Complete button returns to main frame"""
        # Create a mock session
        self.tracker.session_name = "test_session"
        self.tracker.session_active = False

        # Save test session data
        test_data = {
            "test_session": {
                "sphere": "Work",
                "date": "2026-01-20",
                "start_time": "10:00:00",
                "start_timestamp": 1234567890,
                "end_timestamp": 1234571490,
                "breaks": [],
                "idle_periods": [],
                "active": [],
            }
        }
        self.tracker.save_data(test_data, merge=False)

        # Show completion frame
        self.tracker.show_completion_frame(3600, 3600, 0, 1234567890, 1234571490)

        # Verify completion frame is shown
        self.assertIsNotNone(self.tracker.completion_frame)
        self.assertIsNotNone(self.tracker.completion_container)

        # Call save_and_close
        self.tracker.completion_frame.save_and_close()
        self.root.update()  # Process pending events

        # Verify main frame is shown
        self.assertIsNone(self.tracker.completion_container)
        self.assertIsNone(self.tracker.session_name)

        # Verify main frame container is visible
        self.root.update()  # Ensure frame is mapped
        self.assertTrue(self.tracker.main_frame_container.winfo_ismapped())

    def test_skip_and_close_returns_to_main(self):
        """Test that Skip button returns to main frame"""
        # Create a mock session
        self.tracker.session_name = "test_session"
        self.tracker.session_active = False

        # Save test session data
        test_data = {
            "test_session": {
                "sphere": "Work",
                "date": "2026-01-20",
                "start_time": "10:00:00",
                "start_timestamp": 1234567890,
                "end_timestamp": 1234571490,
                "breaks": [],
                "idle_periods": [],
                "active": [],
            }
        }
        self.tracker.save_data(test_data, merge=False)

        # Show completion frame
        self.tracker.show_completion_frame(3600, 3600, 0, 1234567890, 1234571490)

        # Verify completion frame is shown
        self.assertIsNotNone(self.tracker.completion_frame)
        self.assertIsNotNone(self.tracker.completion_container)

        # Call skip_and_close
        self.tracker.completion_frame.skip_and_close()
        self.root.update()  # Process pending events

        # Verify main frame is shown
        self.assertIsNone(self.tracker.completion_container)
        self.assertIsNone(self.tracker.session_name)

        # Verify main frame container is visible
        self.root.update()  # Ensure frame is mapped
        self.assertTrue(self.tracker.main_frame_container.winfo_ismapped())

    def test_delete_session_from_completion_returns_to_main(self):
        """Test that Delete Session from end session flow returns to main"""
        # Create a mock session
        self.tracker.session_name = "test_session"
        self.tracker.session_active = False

        # Save test session data with TWO sessions (so deleting one doesn't empty the file)
        test_data = {
            "test_session": {
                "sphere": "Work",
                "date": "2026-01-20",
                "start_time": "10:00:00",
                "start_timestamp": 1234567890,
                "end_timestamp": 1234571490,
                "breaks": [],
                "idle_periods": [],
                "active": [],
            },
            "other_session": {
                "sphere": "Personal",
                "date": "2026-01-19",
                "start_time": "09:00:00",
                "start_timestamp": 1234467890,
                "end_timestamp": 1234471490,
                "breaks": [],
                "idle_periods": [],
                "active": [],
            },
        }
        self.tracker.save_data(test_data, merge=False)

        # Show completion frame
        self.tracker.show_completion_frame(3600, 3600, 0, 1234567890, 1234571490)

        # Mock the messagebox to auto-confirm and shutil.copy2 to avoid creating backup files
        with patch("tkinter.messagebox.askyesno", return_value=True):
            with patch("tkinter.messagebox.showinfo"):
                with patch("shutil.copy2"):
                    # Call delete
                    self.tracker.completion_frame._delete_session()
                    self.root.update()  # Process pending events

        # Verify session was deleted
        all_data = self.tracker.load_data()
        self.assertNotIn("test_session", all_data)
        # But other session should still exist
        self.assertIn("other_session", all_data)

        # Verify returned to main frame
        self.root.update()  # Ensure frame is mapped
        self.assertIsNone(self.tracker.completion_container)
        self.assertTrue(self.tracker.main_frame_container.winfo_ismapped())

    def test_delete_session_from_session_view_reloads(self):
        """Test that Delete Session from session view reloads next session"""
        # Create multiple sessions
        test_data = {
            "session1": {
                "sphere": "Work",
                "date": "2026-01-20",
                "start_time": "10:00:00",
                "start_timestamp": 1234567890,
                "end_timestamp": 1234571490,
                "breaks": [],
                "idle_periods": [],
                "active": [],
            },
            "session2": {
                "sphere": "Work",
                "date": "2026-01-20",
                "start_time": "14:00:00",
                "start_timestamp": 1234581490,
                "end_timestamp": 1234585090,
                "breaks": [],
                "idle_periods": [],
                "active": [],
            },
        }
        self.tracker.save_data(test_data, merge=False)

        # Open session view
        self.tracker.open_session_view()

        # Verify session view is open
        self.assertIsNotNone(self.tracker.session_view_frame)

        # Get initial session name
        initial_session = self.tracker.session_view_frame.session_name

        # Mock the messagebox to auto-confirm
        with patch("tkinter.messagebox.askyesno", return_value=True):
            with patch("tkinter.messagebox.showinfo"):
                # Call delete
                self.tracker.session_view_frame._delete_session()

        # Session should have been deleted
        all_data = self.tracker.load_data()
        self.assertNotIn(initial_session, all_data)

        # Should still be in session view with different session
        self.assertIsNotNone(self.tracker.session_view_frame)

    def test_analysis_button_opens_analysis(self):
        """Test that Analysis button opens analysis frame"""
        # Ensure no active session
        self.tracker.session_active = False

        # Click analysis link
        self.tracker.open_analysis()
        self.root.update()  # Process pending events

        # Verify analysis frame is shown
        self.assertIsNotNone(self.tracker.analysis_frame)
        self.root.update()  # Ensure frame is mapped
        self.assertTrue(self.tracker.analysis_frame.winfo_ismapped())

        # Verify main frame is hidden
        self.assertFalse(self.tracker.main_frame_container.winfo_ismapped())

    def test_back_to_tracker_from_settings(self):
        """Test that Back to Tracker from settings returns to main"""
        # Open settings
        self.tracker.open_settings()
        self.root.update()  # Process pending events

        # Verify settings is shown
        self.assertIsNotNone(self.tracker.settings_frame)

        # Close settings
        self.tracker.close_settings()
        self.root.update()  # Process pending events

        # Verify main frame is shown
        self.assertIsNone(self.tracker.settings_frame)
        self.root.update()  # Ensure frame is mapped
        self.assertTrue(self.tracker.main_frame_container.winfo_ismapped())

    def test_back_to_tracker_from_analysis(self):
        """Test that Back to Tracker from analysis returns to main"""
        # Open analysis
        self.tracker.session_active = False
        self.tracker.open_analysis()
        self.root.update()  # Process pending events

        # Verify analysis is shown
        self.assertIsNotNone(self.tracker.analysis_frame)

        # Close analysis
        self.tracker.close_analysis()
        self.root.update()  # Process pending events

        # Verify main frame is shown
        self.assertIsNone(self.tracker.analysis_frame)
        self.root.update()  # Ensure frame is mapped
        self.assertTrue(self.tracker.main_frame_container.winfo_ismapped())


if __name__ == "__main__":
    unittest.main()
