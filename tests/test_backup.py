"""
Tests for Backup Save Functionality - Simplified

Verifies that backup saves work and data persists correctly.
"""

import unittest
import json
import os
import sys
import time
import tkinter as tk
from datetime import date
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from src.constants import DEFAULT_BACKUP_FOLDER
from test_helpers import TestDataGenerator, TestFileManager, safe_teardown_tk_root


class TestBackupSaveFunctionality(unittest.TestCase):
    """Test backup save mechanism"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        # Create test files and get full paths
        self.test_data_file = self.file_manager.create_test_file(
            "test_backup_data.json", {}
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_backup_settings.json", TestDataGenerator.create_settings_data()
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


class TestCrashSafeSaveAndDailyBackup(unittest.TestCase):
    """save_data survives a failed write and keeps a daily backup of data.json"""

    def setUp(self):
        """Set up a tracker with an empty test data file"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.test_data_file = self.file_manager.create_test_file(
            "test_daily_backup_data.json", {}
        )
        self.backup_folder = os.path.join(
            self.file_manager.test_data_dir, DEFAULT_BACKUP_FOLDER
        )
        self.tracker = TimeTracker(self.root)
        self.tracker.data_file = self.test_data_file

    def tearDown(self):
        """Clean up after tests"""
        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    @patch("time_tracker.messagebox.showerror")
    def test_disk_full_mid_save_keeps_previous_data(self, mock_error):
        """Test that a save dying partway leaves the previous data.json intact"""
        existing_data = {"session_1": {"date": "2026-05-26", "total_duration": 3600}}
        self.tracker.save_data(existing_data, merge=False)

        disk_full = OSError(28, "No space left on device")
        with patch("json.dump", side_effect=disk_full):
            self.tracker.save_data({"session_2": {"date": "2026-05-27"}})

        self.assertEqual(self.tracker.load_data(), existing_data)
        mock_error.assert_called_once()

    def test_save_writes_todays_backup_of_saved_data(self):
        """Test that saving writes today's backup next to the data file"""
        self.tracker.save_data({"session_1": {"date": "2026-10-08"}})

        backup_path = os.path.join(
            self.backup_folder,
            f"test_daily_backup_data.json.daily_{date.today():%Y%m%d}",
        )
        with open(backup_path) as f:
            self.assertEqual(json.load(f), {"session_1": {"date": "2026-10-08"}})

    @patch("time_tracker.messagebox.showwarning")
    def test_backup_failure_does_not_block_save_and_warns_once(self, mock_warning):
        """Test that a failed backup still saves the data and warns only once"""
        disk_full = OSError(28, "No space left on device")
        with patch("time_tracker.create_daily_backup", side_effect=disk_full):
            self.tracker.save_data({"session_1": {}})
            self.tracker.save_data({"session_2": {}})

        saved_data = self.tracker.load_data()
        self.assertIn("session_1", saved_data)
        self.assertIn("session_2", saved_data)
        mock_warning.assert_called_once()


if __name__ == "__main__":
    unittest.main()
