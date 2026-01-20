"""
Tests for Screenshot Timing - Simplified

Verifies basic screenshot configuration and settings.
"""

import unittest
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from test_helpers import TestDataGenerator, TestFileManager


class TestScreenshotTiming(unittest.TestCase):
    """Test screenshot settings and configuration"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()
        self.test_settings_file = "test_screenshot_settings.json"

        # Create test settings
        settings = TestDataGenerator.create_settings_data()
        self.file_manager.create_test_file(self.test_settings_file, settings)

    def tearDown(self):
        """Clean up test files"""
        self.file_manager.cleanup()

    def test_screenshot_settings_exist(self):
        """Test that screenshot settings are in config"""
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        self.assertIn("screenshot_settings", settings)

        screenshot_settings = settings["screenshot_settings"]
        self.assertIn("enabled", screenshot_settings)
        self.assertIn("min_seconds_between_captures", screenshot_settings)

    def test_min_seconds_setting(self):
        """Test that min_seconds_between_captures is configurable"""
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        min_seconds = settings["screenshot_settings"]["min_seconds_between_captures"]
        self.assertIsInstance(min_seconds, (int, float))
        self.assertGreater(min_seconds, 0)


if __name__ == "__main__":
    unittest.main()
