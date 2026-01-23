"""
Tests for Idle Tracking Functionality - Simplified

Verifies that idle detection configuration works.
"""

import unittest
import tkinter as tk
import time
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from test_helpers import TestDataGenerator, TestFileManager
from time_tracker import TimeTracker


class TestIdleTracking(unittest.TestCase):
    """Test idle detection configuration"""

    def setUp(self):
        """Set up test fixtures before each test"""
        self.file_manager = TestFileManager()

        # Create test settings with short thresholds
        settings = TestDataGenerator.create_settings_data()
        settings["idle_settings"]["idle_threshold"] = 2  # 2 seconds
        settings["idle_settings"]["idle_break_threshold"] = 10  # 10 seconds

        self.test_data_file = self.file_manager.create_test_file(
            "test_idle_data.json", {}
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_idle_settings.json", settings
        )

        # Create root window for TimeTracker
        self.root = tk.Tk()
        self.tracker = TimeTracker(self.root)
        self.tracker.settings_file = self.test_settings_file
        self.tracker.data_file = self.test_data_file

    def tearDown(self):
        """Clean up after each test"""
        if self.tracker.session_active:
            self.tracker.session_active = False
            if hasattr(self.tracker, "stop_input_monitoring"):
                self.tracker.stop_input_monitoring()
        self.root.destroy()

        # Clean up test files
        self.file_manager.cleanup()

    def test_idle_settings_loaded(self):
        """Test that idle settings are loaded correctly"""
        settings = self.tracker.get_settings()

        self.assertIn("idle_settings", settings)
        self.assertEqual(settings["idle_settings"]["idle_threshold"], 2)
        self.assertEqual(settings["idle_settings"]["idle_break_threshold"], 10)

    def test_idle_periods_structure(self):
        """Test that session has idle_periods field"""
        self.tracker.start_session()

        all_data = self.tracker.load_data()

        self.assertIn("idle_periods", all_data[self.tracker.session_name])
        self.assertIsInstance(all_data[self.tracker.session_name]["idle_periods"], list)


if __name__ == "__main__":
    unittest.main()
