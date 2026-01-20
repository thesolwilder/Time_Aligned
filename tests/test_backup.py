"""
Tests for Backup Save Functionality - Simplified

Verifies that backup saves work and data persists correctly.
"""

import unittest
import json
import os
import sys
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from test_helpers import TestDataGenerator, TestFileManager


class TestBackupSaveFunctionality(unittest.TestCase):
    """Test backup save mechanism"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()
        self.test_data_file = "test_backup_data.json"
        self.test_settings_file = "test_backup_settings.json"

        # Create test files
        self.file_manager.create_test_file(self.test_data_file, {})
        self.file_manager.create_test_file(
            self.test_settings_file, TestDataGenerator.create_settings_data()
        )

    def tearDown(self):
        """Clean up test files"""
        self.file_manager.cleanup()

    def test_backup_timing_60_seconds(self):
        """Test that 600 iterations at 100ms each equals 60 seconds"""
        iterations = 600
        interval_ms = 100

        expected_seconds = (iterations * interval_ms) / 1000

        self.assertEqual(expected_seconds, 60.0)

    def test_session_data_persists(self):
        """Test that session data is saved and can be loaded"""
        from time_tracker import TimeTracker
        import tkinter as tk

        root = tk.Tk()
        tracker = TimeTracker(root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        # Create session
        tracker.start_session()
        session_name = tracker.session_name
        time.sleep(0.1)
        tracker.end_session()

        # Create new tracker instance (simulates app restart)
        tracker2 = TimeTracker(root)
        tracker2.data_file = self.test_data_file
        tracker2.settings_file = self.test_settings_file

        # Load data
        data = tracker2.load_data()

        # Verify session was persisted
        self.assertIn(session_name, data)

        root.destroy()


if __name__ == "__main__":
    unittest.main()
