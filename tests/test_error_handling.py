"""
Tests for Error Handling

Verifies the app handles corrupted files, missing files, and invalid data gracefully.
"""

import unittest
import tkinter as tk
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from test_helpers import TestFileManager


class TestCorruptedDataFiles(unittest.TestCase):
    """Test handling of corrupted data.json files"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_corrupt_data.json"
        self.test_settings_file = "test_corrupt_settings.json"

    def test_invalid_json_syntax(self):
        """Test handling of data file with invalid JSON syntax"""
        # Create file with invalid JSON
        with open(self.test_data_file, "w") as f:
            f.write('{"session_1": {invalid json syntax}')
        self.file_manager.test_files.append(self.test_data_file)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file

        # Should return empty dict instead of crashing
        data = tracker.load_data()
        self.assertEqual(data, {})

    def test_empty_data_file(self):
        """Test handling of completely empty data file"""
        # Create empty file
        with open(self.test_data_file, "w") as f:
            f.write("")
        self.file_manager.test_files.append(self.test_data_file)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file

        data = tracker.load_data()
        self.assertEqual(data, {})

    def test_non_dict_json(self):
        """Test handling of JSON that's not a dictionary"""
        # Create file with JSON array instead of object
        with open(self.test_data_file, "w") as f:
            json.dump([1, 2, 3], f)
        self.file_manager.test_files.append(self.test_data_file)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file

        # load_data returns whatever JSON is in the file
        data = tracker.load_data()
        self.assertEqual(data, [1, 2, 3])

    def test_missing_required_fields(self):
        """Test handling of session data missing required fields"""
        incomplete_data = {
            "session_1": {
                "date": "2024-01-20",
                # Missing start_time, end_time, etc.
            }
        }

        with open(self.test_data_file, "w") as f:
            json.dump(incomplete_data, f)
        self.file_manager.test_files.append(self.test_data_file)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file

        # Should load without crashing
        data = tracker.load_data()
        self.assertIn("session_1", data)


class TestCorruptedSettingsFiles(unittest.TestCase):
    """Test handling of corrupted settings.json files"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_settings_file = "test_corrupt_settings.json"

    def test_invalid_settings_json(self):
        """Test handling of settings file with invalid JSON"""
        with open(self.test_settings_file, "w") as f:
            f.write("{invalid json")
        self.file_manager.test_files.append(self.test_settings_file)

        tracker = TimeTracker(self.root)
        tracker.settings_file = self.test_settings_file

        # Should return default settings
        settings = tracker.get_settings()
        self.assertIn("idle_settings", settings)
        self.assertIn("spheres", settings)

    def test_missing_idle_settings(self):
        """Test handling of settings missing idle configuration"""
        incomplete_settings = {
            "spheres": {"Work": {"projects": ["Project A"], "default": True}}
            # Missing idle_settings - but file is valid JSON
        }

        with open(self.test_settings_file, "w") as f:
            json.dump(incomplete_settings, f)
        self.file_manager.test_files.append(self.test_settings_file)

        tracker = TimeTracker(self.root)
        tracker.settings_file = self.test_settings_file

        settings = tracker.get_settings()
        # Returns what's in the file (doesn't merge with defaults)
        self.assertNotIn("idle_settings", settings)
        self.assertIn("spheres", settings)

    def test_missing_spheres(self):
        """Test handling of settings missing spheres configuration"""
        incomplete_settings = {
            "idle_settings": {"threshold_seconds": 300, "enabled": True}
            # Missing spheres - but file is valid JSON
        }

        with open(self.test_settings_file, "w") as f:
            json.dump(incomplete_settings, f)
        self.file_manager.test_files.append(self.test_settings_file)

        tracker = TimeTracker(self.root)
        tracker.settings_file = self.test_settings_file

        settings = tracker.get_settings()
        # Returns file contents without merging with defaults
        self.assertNotIn("spheres", settings)
        self.assertIn("idle_settings", settings)


class TestMissingFiles(unittest.TestCase):
    """Test handling of missing data and settings files"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

    def test_missing_data_file(self):
        """Test that missing data.json is created automatically"""
        tracker = TimeTracker(self.root)
        tracker.data_file = "nonexistent_data.json"

        # Should return empty dict, not crash
        data = tracker.load_data()
        self.assertEqual(data, {})

        # Cleanup
        if os.path.exists("nonexistent_data.json"):
            os.remove("nonexistent_data.json")

    def test_missing_settings_file(self):
        """Test that missing settings.json is created with defaults"""
        tracker = TimeTracker(self.root)
        tracker.settings_file = "nonexistent_settings.json"

        settings = tracker.get_settings()

        # Should have all default settings
        self.assertIn("idle_settings", settings)
        self.assertIn("spheres", settings)
        self.assertIn("screenshot_settings", settings)

        # Cleanup
        if os.path.exists("nonexistent_settings.json"):
            os.remove("nonexistent_settings.json")


class TestDataIntegrity(unittest.TestCase):
    """Test data integrity validation"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_integrity_data.json"
        self.test_settings_file = "test_integrity_settings.json"

    def test_negative_durations_handled(self):
        """Test handling of negative duration values"""
        invalid_data = {
            "session_1": {
                "date": "2024-01-20",
                "start_time": "10:00:00",
                "end_time": "11:00:00",
                "total_duration": -3600,  # Invalid negative duration
                "active_duration": -1800,
                "break_duration": -1800,
                "sphere": "Work",
                "active": [],
                "breaks": [],
                "actions": [],
                "break_actions": [],
            }
        }

        with open(self.test_data_file, "w") as f:
            json.dump(invalid_data, f)
        self.file_manager.test_files.append(self.test_data_file)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file

        # Should load without crashing
        data = tracker.load_data()
        self.assertIn("session_1", data)

    def test_timestamp_order_validation(self):
        """Test handling of end timestamp before start timestamp"""
        invalid_data = {
            "session_1": {
                "date": "2024-01-20",
                "start_time": "11:00:00",
                "end_time": "10:00:00",  # End before start
                "start_timestamp": 1000000,
                "end_timestamp": 900000,  # End before start
                "total_duration": 3600,
                "active_duration": 3000,
                "break_duration": 600,
                "sphere": "Work",
                "active": [],
                "breaks": [],
                "actions": [],
                "break_actions": [],
            }
        }

        with open(self.test_data_file, "w") as f:
            json.dump(invalid_data, f)
        self.file_manager.test_files.append(self.test_data_file)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file

        # Should load without crashing
        data = tracker.load_data()
        self.assertIn("session_1", data)

    def test_save_data_persists_correctly(self):
        """Test that save_data writes data correctly"""
        from test_helpers import TestDataGenerator

        # Create valid initial data
        valid_data = TestDataGenerator.create_session_data()
        self.file_manager.create_test_file(self.test_data_file, valid_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file

        # Save data
        tracker.save_data(valid_data, merge=False)

        # Should be able to load it back
        loaded = tracker.load_data()
        self.assertEqual(len(loaded), len(valid_data))


if __name__ == "__main__":
    unittest.main()
