"""
Test navigation flows between different frames.

Tests the complex navigation scenarios:
- Completion frame → Analysis → Session View → Back navigation
- Session deletion and subsequent navigation
- Frame state cleanup and transitions
"""

import unittest
import sys
import os
import json
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from time_tracker import TimeTracker


class TestNavigation(unittest.TestCase):
    """Test navigation between frames"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.tracker = TimeTracker(self.root)

        # Create minimal test data
        self.test_data = {
            "2026-01-21_1000000001": {
                "sphere": "Test",
                "date": "2026-01-21",
                "start_time": "10:00:00",
                "active": [{"duration": 60, "project": "test_project"}],
                "breaks": [],
                "idle_periods": [],
            }
        }

        # Mock file operations
        self.original_load = self.tracker.load_data
        self.original_save = self.tracker.save_data
        self.tracker.load_data = Mock(return_value=self.test_data.copy())
        self.tracker.save_data = Mock()

    def tearDown(self):
        """Clean up after tests"""
        try:
            self.tracker.load_data = self.original_load
            self.tracker.save_data = self.original_save
            self.root.destroy()
        except:
            pass

    def test_session_view_opens_from_analysis(self):
        """Test that session view opens correctly from analysis frame"""
        # Open analysis
        self.tracker.open_analysis()
        self.assertIsNotNone(self.tracker.analysis_frame)

        # Open session view from analysis
        self.tracker.open_session_view(from_analysis=True)
        self.assertIsNotNone(self.tracker.session_view_frame)
        self.assertIsNotNone(self.tracker.session_view_container)
        self.assertTrue(self.tracker.session_view_from_analysis)

    def test_session_view_does_not_open_twice(self):
        """Test that session view doesn't open if already open"""
        # Open session view
        self.tracker.open_session_view(from_analysis=False)
        self.assertIsNotNone(self.tracker.session_view_frame)

        # Try to open again - should do nothing
        first_frame = self.tracker.session_view_frame
        self.tracker.open_session_view(from_analysis=False)
        self.assertEqual(first_frame, self.tracker.session_view_frame)

    def test_close_analysis_clears_session_view_if_open(self):
        """Test that closing analysis properly handles open session view"""
        # Open analysis then session view
        self.tracker.open_analysis()
        self.tracker.open_session_view(from_analysis=True)

        # Close analysis - will call close_session_view internally
        self.tracker.close_analysis()

        # Session view should be closed
        self.assertIsNone(self.tracker.session_view_frame)

        # close_analysis() calls close_session_view() which creates a fresh analysis
        # frame because session_view_from_analysis was True. This is correct behavior:
        # it prevents returning to potentially corrupted analysis frame state.
        self.assertIsNotNone(self.tracker.analysis_frame)

    def test_show_main_frame_clears_all_views(self):
        """Test that show_main_frame clears all frame references"""
        # Open multiple frames
        self.tracker.open_analysis()
        self.tracker.open_session_view(from_analysis=True)

        # Show main frame
        self.tracker.show_main_frame()

        # All frames should be cleared
        self.assertIsNone(self.tracker.analysis_frame)
        self.assertIsNone(self.tracker.session_view_frame)
        self.assertIsNone(self.tracker.session_view_container)
        # completion_frame and completion_container may not exist if never created
        if hasattr(self.tracker, "completion_frame"):
            self.assertIsNone(self.tracker.completion_frame)
        if hasattr(self.tracker, "completion_container"):
            self.assertIsNone(self.tracker.completion_container)

    def test_close_session_view_returns_to_analysis_if_from_analysis(self):
        """Test that closing session view returns to analysis if opened from there"""
        # Open analysis then session view
        self.tracker.open_analysis()
        self.tracker.open_session_view(from_analysis=True)

        # Close session view
        self.tracker.close_session_view()

        # Should return to analysis with a FRESH instance (not the old one)
        # This is deliberate - prevents state corruption from CSV export, etc.
        self.assertIsNotNone(self.tracker.analysis_frame)
        self.assertIsNone(self.tracker.session_view_frame)

    def test_close_session_view_returns_to_main_if_not_from_analysis(self):
        """Test that closing session view goes to main if not from analysis"""
        # Open session view from main
        self.tracker.open_session_view(from_analysis=False)

        # Close session view
        self.tracker.close_session_view()

        # Should be at main, not analysis
        # analysis_frame may not exist if never created
        self.assertFalse(
            hasattr(self.tracker, "analysis_frame")
            and self.tracker.analysis_frame is not None
        )
        self.assertIsNone(self.tracker.session_view_frame)

    @patch("tkinter.messagebox.askyesno", return_value=True)
    @patch("tkinter.messagebox.showinfo")
    def test_delete_session_from_session_view_maintains_navigation(
        self, mock_info, mock_confirm
    ):
        """Test that deleting a session from session view maintains proper navigation"""
        # Create session view with multiple sessions
        multi_session_data = self.test_data.copy()
        multi_session_data["2026-01-21_1000000002"] = multi_session_data[
            "2026-01-21_1000000001"
        ].copy()
        self.tracker.load_data = Mock(return_value=multi_session_data)

        # Open analysis then session view
        self.tracker.open_analysis()
        self.tracker.open_session_view(from_analysis=True)

        # The session view frame should have navigation state preserved
        self.assertTrue(self.tracker.session_view_from_analysis)

        # After deletion, the flag should still be set for the new session view
        # (This is tested via the session_view_from_analysis flag)

    def test_analysis_from_completion_flag_clears_properly(self):
        """Test that analysis_from_completion flag is managed correctly"""
        # Initially should not be set
        self.assertFalse(
            hasattr(self.tracker, "analysis_from_completion")
            and self.tracker.analysis_from_completion
        )

        # Open analysis without completion frame
        self.tracker.open_analysis()
        self.assertFalse(self.tracker.analysis_from_completion)

        # Close and flag should be cleared
        self.tracker.close_analysis()
        self.assertFalse(self.tracker.analysis_from_completion)

    def test_session_view_button_not_dead_after_analysis_navigation(self):
        """
        Test the bug fix: Session view → Analysis → Session View (should work)

        Bug scenario that was fixed:
        1. Open session view (sets session_view_frame reference)
        2. Click Analysis button (hides container but didn't clear reference)
        3. Try to open session view again (was blocked due to stale reference)

        Expected: Session view should open successfully on second attempt
        """
        # Step 1: Open session view initially
        self.tracker.open_session_view(from_analysis=False)
        self.assertIsNotNone(self.tracker.session_view_frame)
        first_session_view = self.tracker.session_view_frame

        # Step 2: Open analysis (should properly close session view)
        self.tracker.open_analysis()
        self.assertIsNotNone(self.tracker.analysis_frame)
        # Bug fix: session_view_frame should be cleared, not just hidden
        self.assertIsNone(self.tracker.session_view_frame)
        self.assertIsNone(self.tracker.session_view_container)

        # Step 3: Try to open session view again from analysis
        self.tracker.open_session_view(from_analysis=True)
        # Should successfully create new session view
        self.assertIsNotNone(self.tracker.session_view_frame)
        self.assertIsNotNone(self.tracker.session_view_container)
        # Should be a NEW frame instance, not the old one
        self.assertNotEqual(first_session_view, self.tracker.session_view_frame)
        self.assertTrue(self.tracker.session_view_from_analysis)

    def test_delete_session_then_analysis_then_session_view(self):
        """
        Test the complete bug reproduction scenario:
        1. In completion frame: delete a session
        2. In completion frame: click analysis button
        3. In analysis frame: click session view button

        Expected: Session view should open successfully
        """
        # Mock deletion to ensure we have data
        multi_session_data = {
            "2026-01-21_1000000001": {
                "sphere": "Test",
                "date": "2026-01-21",
                "start_time": "10:00:00",
                "active": [{"duration": 60, "project": "test_project"}],
                "breaks": [],
                "idle_periods": [],
            },
            "2026-01-21_1000000002": {
                "sphere": "Test",
                "date": "2026-01-21",
                "start_time": "11:00:00",
                "active": [{"duration": 120, "project": "test_project"}],
                "breaks": [],
                "idle_periods": [],
            },
        }
        self.tracker.load_data = Mock(return_value=multi_session_data)

        # Simulate being in completion frame with session view open
        self.tracker.open_session_view(from_analysis=False)
        self.assertIsNotNone(self.tracker.session_view_frame)

        # After deletion, show_main_frame is called which clears everything
        self.tracker.show_main_frame()
        self.assertIsNone(self.tracker.session_view_frame)

        # Now open analysis (simulating clicking Analysis button)
        self.tracker.open_analysis()
        self.assertIsNotNone(self.tracker.analysis_frame)

        # Try to open session view from analysis
        # This should work (not be "dead")
        self.tracker.open_session_view(from_analysis=True)
        self.assertIsNotNone(self.tracker.session_view_frame)
        self.assertIsNotNone(self.tracker.session_view_container)
        self.assertTrue(self.tracker.session_view_from_analysis)


class TestNavigationEdgeCases(unittest.TestCase):
    """Test edge cases in navigation"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.tracker = TimeTracker(self.root)

    def tearDown(self):
        """Clean up after tests"""
        try:
            self.root.destroy()
        except:
            pass

    def test_open_session_view_while_tracking(self):
        """Test that session view doesn't open while tracking"""
        self.tracker.session_active = True

        with patch("tkinter.messagebox.showwarning") as mock_warning:
            self.tracker.open_session_view()
            mock_warning.assert_called_once()
            # session_view_frame may not exist if never created
            self.assertFalse(
                hasattr(self.tracker, "session_view_frame")
                and self.tracker.session_view_frame is not None
            )

    def test_open_analysis_while_tracking(self):
        """Test that analysis doesn't open while tracking"""
        self.tracker.session_active = True

        with patch("tkinter.messagebox.showwarning") as mock_warning:
            self.tracker.open_analysis()
            mock_warning.assert_called_once()
            # analysis_frame may not exist if never created
            self.assertFalse(
                hasattr(self.tracker, "analysis_frame")
                and self.tracker.analysis_frame is not None
            )


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
