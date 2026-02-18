"""
Tests for Screenshot Capture Module

Verifies screenshot configuration, monitoring lifecycle, and settings updates.
"""

import unittest
import json
import os
import sys
import time
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from test_helpers import TestDataGenerator, TestFileManager
from src.screenshot_capture import ScreenshotCapture


class TestScreenshotSettings(unittest.TestCase):
    """Test screenshot settings and configuration"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        # Create test settings
        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_screenshot_settings.json", settings
        )

        # Create test data file
        self.test_data_file = self.file_manager.create_test_file(
            "test_screenshot_data.json", {}
        )

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


class TestScreenshotCaptureInit(unittest.TestCase):
    """Test ScreenshotCapture initialization"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file("test_data.json", {})

    def tearDown(self):
        """Clean up test files"""
        self.file_manager.cleanup()

    def test_init_loads_settings(self):
        """Test that ScreenshotCapture loads settings on initialization"""
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        capture = ScreenshotCapture(settings, self.test_data_file)

        # Verify settings loaded
        self.assertEqual(capture.settings, settings)
        self.assertTrue(capture.enabled)  # TestDataGenerator defaults to True
        self.assertTrue(capture.capture_on_focus_change)  # Default is True
        self.assertEqual(
            capture.min_seconds_between_captures, 5
        )  # TestDataGenerator default

    def test_init_with_enabled_screenshots(self):
        """Test initialization when screenshots are enabled"""
        settings = TestDataGenerator.create_settings_data()
        settings["screenshot_settings"]["enabled"] = True

        with open(self.test_settings_file, "w") as f:
            json.dump(settings, f)

        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        capture = ScreenshotCapture(settings, self.test_data_file)

        self.assertTrue(capture.enabled)
        self.assertFalse(
            capture.monitoring
        )  # Not started until start_monitoring called

    def test_init_state_variables(self):
        """Test that state variables are initialized correctly"""
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        capture = ScreenshotCapture(settings, self.test_data_file)

        # Verify state tracking
        self.assertFalse(capture.monitoring)
        self.assertIsNone(capture.monitor_thread)
        self.assertIsNone(capture.last_window_title)
        self.assertIsNone(capture.last_window_process)
        self.assertEqual(capture.last_capture_time, 0)

        # Verify session info
        self.assertIsNone(capture.current_session_key)
        self.assertIsNone(capture.current_period_type)
        self.assertIsNone(capture.current_period_index)
        self.assertIsNone(capture.current_screenshot_folder)
        self.assertEqual(capture.current_period_screenshots, [])


class TestScreenshotMonitoring(unittest.TestCase):
    """Test screenshot monitoring lifecycle"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        settings = TestDataGenerator.create_settings_data()
        settings["screenshot_settings"]["enabled"] = True

        self.test_settings_file = self.file_manager.create_test_file(
            "test_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file("test_data.json", {})

    def tearDown(self):
        """Clean up test files"""
        self.file_manager.cleanup()

    def test_start_monitoring_when_enabled(self):
        """Test that monitoring starts when enabled"""
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        capture = ScreenshotCapture(settings, self.test_data_file)

        self.assertFalse(capture.monitoring)

        capture.start_monitoring()

        self.assertTrue(capture.monitoring)
        self.assertIsNotNone(capture.monitor_thread)
        self.assertTrue(capture.monitor_thread.daemon)  # Should be daemon thread

        # Clean up
        capture.stop_monitoring()

    def test_start_monitoring_when_disabled(self):
        """Test that monitoring does not start when disabled"""
        settings = TestDataGenerator.create_settings_data()
        settings["screenshot_settings"]["enabled"] = False

        with open(self.test_settings_file, "w") as f:
            json.dump(settings, f)

        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        capture = ScreenshotCapture(settings, self.test_data_file)

        capture.start_monitoring()

        self.assertFalse(capture.monitoring)
        self.assertIsNone(capture.monitor_thread)

    def test_start_monitoring_idempotent(self):
        """Test that calling start_monitoring twice doesn't create multiple threads"""
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        capture = ScreenshotCapture(settings, self.test_data_file)

        capture.start_monitoring()
        first_thread = capture.monitor_thread

        capture.start_monitoring()  # Call again
        second_thread = capture.monitor_thread

        self.assertIs(first_thread, second_thread)  # Same thread object

        # Clean up
        capture.stop_monitoring()

    def test_stop_monitoring(self):
        """Test that monitoring stops cleanly"""
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        capture = ScreenshotCapture(settings, self.test_data_file)

        capture.start_monitoring()
        self.assertTrue(capture.monitoring)

        capture.stop_monitoring()

        self.assertFalse(capture.monitoring)
        # Thread should be joined (stopped)


class TestScreenshotSessionManagement(unittest.TestCase):
    """Test screenshot session and period management"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file("test_data.json", {})

    def tearDown(self):
        """Clean up test files"""
        self.file_manager.cleanup()

    @patch("os.makedirs")
    def test_set_current_session_creates_folder(self, mock_makedirs):
        """Test that set_current_session creates screenshot folder"""
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        capture = ScreenshotCapture(settings, self.test_data_file)

        session_key = "2026-02-16_143022"
        capture.set_current_session(session_key, "active", 0)

        # Verify state updated
        self.assertEqual(capture.current_session_key, session_key)
        self.assertEqual(capture.current_period_type, "active")
        self.assertEqual(capture.current_period_index, 0)
        self.assertEqual(capture.current_period_screenshots, [])

        # Verify folder path constructed
        expected_path = os.path.join(
            settings["screenshot_settings"]["screenshot_path"],
            "2026-02-16",
            "session_143022",
            "period_active_0",
        )
        self.assertEqual(capture.current_screenshot_folder, expected_path)

        # Verify makedirs called
        mock_makedirs.assert_called_once_with(expected_path, exist_ok=True)

    def test_set_current_session_with_none_clears_folder(self):
        """Test that passing None session_key clears screenshot folder"""
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        capture = ScreenshotCapture(settings, self.test_data_file)

        # First set a session
        capture.set_current_session("2026-02-16_143022", "active", 0)
        self.assertIsNotNone(capture.current_screenshot_folder)

        # Now clear it
        capture.set_current_session(None, "active", 0)

        self.assertIsNone(capture.current_screenshot_folder)

    def test_get_screenshot_folder_path(self):
        """Test get_screenshot_folder_path returns current folder"""
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        capture = ScreenshotCapture(settings, self.test_data_file)

        # Initially None
        self.assertIsNone(capture.get_screenshot_folder_path())

        # After setting session
        with patch("os.makedirs"):
            capture.set_current_session("2026-02-16_143022", "break", 1)

        folder = capture.get_screenshot_folder_path()
        self.assertIsNotNone(folder)
        self.assertIn("2026-02-16", folder)
        self.assertIn("session_143022", folder)
        self.assertIn("period_break_1", folder)

    def test_get_current_period_screenshots_returns_copy(self):
        """Test that get_current_period_screenshots returns defensive copy"""
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        capture = ScreenshotCapture(settings, self.test_data_file)

        # Add some screenshots internally
        capture.current_period_screenshots.append({"filepath": "test1.png"})
        capture.current_period_screenshots.append({"filepath": "test2.png"})

        # Get copy
        screenshots = capture.get_current_period_screenshots()

        # Verify it's a copy (same content, different object)
        self.assertEqual(len(screenshots), 2)
        self.assertEqual(screenshots[0]["filepath"], "test1.png")

        # Modify the copy
        screenshots.append({"filepath": "test3.png"})

        # Verify original not modified
        self.assertEqual(len(capture.current_period_screenshots), 2)


class TestScreenshotSettingsUpdate(unittest.TestCase):
    """Test screenshot settings hot-reload"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        settings = TestDataGenerator.create_settings_data()
        settings["screenshot_settings"]["enabled"] = False

        self.test_settings_file = self.file_manager.create_test_file(
            "test_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file("test_data.json", {})

    def tearDown(self):
        """Clean up test files"""
        self.file_manager.cleanup()

    def test_update_settings_reloads_config(self):
        """Test that update_settings reloads all screenshot configuration"""
        with open(self.test_settings_file, "r") as f:
            old_settings = json.load(f)

        capture = ScreenshotCapture(old_settings, self.test_data_file)

        # Verify initial state
        self.assertFalse(capture.enabled)  # We explicitly set to False in setUp
        self.assertEqual(
            capture.min_seconds_between_captures, 5
        )  # TestDataGenerator default

        # Create new settings
        new_settings = TestDataGenerator.create_settings_data()
        new_settings["screenshot_settings"]["enabled"] = True
        new_settings["screenshot_settings"]["min_seconds_between_captures"] = 20
        new_settings["screenshot_settings"]["screenshot_path"] = "custom_path"

        # Update
        capture.update_settings(new_settings)

        # Verify updated
        self.assertTrue(capture.enabled)
        self.assertEqual(capture.min_seconds_between_captures, 20)
        self.assertEqual(capture.screenshot_base_path, "custom_path")

    def test_update_settings_starts_monitoring_when_enabled(self):
        """Test that update_settings starts monitoring when enabled changes to True"""
        with open(self.test_settings_file, "r") as f:
            old_settings = json.load(f)

        capture = ScreenshotCapture(old_settings, self.test_data_file)

        self.assertFalse(capture.monitoring)

        # Enable screenshots
        new_settings = TestDataGenerator.create_settings_data()
        new_settings["screenshot_settings"]["enabled"] = True

        capture.update_settings(new_settings)

        # Monitoring should start
        self.assertTrue(capture.monitoring)
        self.assertIsNotNone(capture.monitor_thread)

        # Clean up
        capture.stop_monitoring()

    def test_update_settings_stops_monitoring_when_disabled(self):
        """Test that update_settings stops monitoring when enabled changes to False"""
        # Start with enabled
        settings = TestDataGenerator.create_settings_data()
        settings["screenshot_settings"]["enabled"] = True

        with open(self.test_settings_file, "w") as f:
            json.dump(settings, f)

        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        capture = ScreenshotCapture(settings, self.test_data_file)
        capture.start_monitoring()

        self.assertTrue(capture.monitoring)

        # Disable screenshots
        new_settings = TestDataGenerator.create_settings_data()
        new_settings["screenshot_settings"]["enabled"] = False

        capture.update_settings(new_settings)

        # Monitoring should stop
        self.assertFalse(capture.monitoring)


if __name__ == "__main__":
    unittest.main()
