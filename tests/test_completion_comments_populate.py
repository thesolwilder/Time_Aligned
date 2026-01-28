"""
Test that completion frame populates session comments when loading a session.
"""

import unittest
import sys
import os
import json
import tkinter as tk
from datetime import datetime

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.completion_frame import CompletionFrame
from time_tracker import TimeTracker


class TestCompletionCommentsPopulate(unittest.TestCase):
    """Test that session comments are populated when loading a session"""

    def setUp(self):
        """Set up test environment"""
        self.test_data_file = os.path.join(
            os.path.dirname(__file__), "test_comments_data.json"
        )

        # Create test data with session comments
        test_session_name = "2026-01-28_10-30-00"
        self.test_data = {
            test_session_name: {
                "start_timestamp": 1706438400.0,
                "end_timestamp": 1706442000.0,
                "total_duration": 3600,
                "active_duration": 2400,
                "break_duration": 600,
                "sphere": "Work",
                "session_comments": {
                    "active_notes": "Working on feature X",
                    "break_notes": "Coffee break",
                    "idle_notes": "Thinking time",
                    "session_notes": "Very productive session\nCompleted three tasks",
                },
                "active_periods": [],
                "break_periods": [],
                "idle_periods": [],
            }
        }

        # Write test data
        with open(self.test_data_file, "w") as f:
            json.dump(self.test_data, f)

        # Create tracker and set test data file
        self.root = tk.Tk()
        self.tracker = TimeTracker(self.root)
        self.tracker.data_file = self.test_data_file

    def tearDown(self):
        """Clean up test environment"""
        self.root.destroy()
        if os.path.exists(self.test_data_file):
            os.remove(self.test_data_file)

    def test_session_comments_populated_on_load(self):
        """Test that session comments are populated when loading a session"""
        # Create completion frame with the test session
        session_name = "2026-01-28_10-30-00"
        completion_frame = CompletionFrame(self.root, self.tracker, session_name)

        # Verify that session comments were loaded
        self.assertIsNotNone(completion_frame.session_comments)
        self.assertEqual(
            completion_frame.session_comments.get("active_notes"),
            "Working on feature X",
        )
        self.assertEqual(
            completion_frame.session_comments.get("break_notes"), "Coffee break"
        )
        self.assertEqual(
            completion_frame.session_comments.get("idle_notes"), "Thinking time"
        )
        self.assertEqual(
            completion_frame.session_comments.get("session_notes"),
            "Very productive session\nCompleted three tasks",
        )

    def test_comment_fields_populated_in_ui(self):
        """Test that comment fields in UI are populated with session data"""
        # Create completion frame with the test session
        session_name = "2026-01-28_10-30-00"
        completion_frame = CompletionFrame(self.root, self.tracker, session_name)

        # Force UI update
        self.root.update()

        # Verify that UI fields are populated
        self.assertEqual(completion_frame.active_notes.get(), "Working on feature X")
        self.assertEqual(completion_frame.break_notes.get(), "Coffee break")
        self.assertEqual(completion_frame.idle_notes.get(), "Thinking time")
        self.assertEqual(
            completion_frame.session_notes_text.get("1.0", tk.END).strip(),
            "Very productive session\nCompleted three tasks",
        )

    def test_empty_comments_handled_gracefully(self):
        """Test that missing session comments don't cause errors"""
        # Create session without comments
        test_session_name = "2026-01-28_11-30-00"
        self.test_data[test_session_name] = {
            "start_timestamp": 1706442000.0,
            "end_timestamp": 1706445600.0,
            "total_duration": 3600,
            "active_duration": 2400,
            "break_duration": 600,
            "sphere": "Work",
            "active_periods": [],
            "break_periods": [],
            "idle_periods": [],
        }

        # Write updated data
        with open(self.test_data_file, "w") as f:
            json.dump(self.test_data, f)

        # Reload tracker data
        self.tracker = TimeTracker(self.root)
        self.tracker.data_file = self.test_data_file

        # Create completion frame - should not raise an error
        completion_frame = CompletionFrame(self.root, self.tracker, test_session_name)
        self.root.update()

        # Verify fields are empty
        self.assertEqual(completion_frame.active_notes.get(), "")
        self.assertEqual(completion_frame.break_notes.get(), "")
        self.assertEqual(completion_frame.idle_notes.get(), "")
        self.assertEqual(
            completion_frame.session_notes_text.get("1.0", tk.END).strip(), ""
        )


if __name__ == "__main__":
    unittest.main()
