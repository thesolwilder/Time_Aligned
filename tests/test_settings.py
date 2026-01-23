"""
Tests for Settings and Default Values - Simplified

Verifies settings persistence and default value retrieval.
"""

import unittest
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from test_helpers import TestDataGenerator, TestFileManager


class TestSettingsDefaults(unittest.TestCase):
    """Test settings management and defaults"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        # Create test settings
        self.test_settings_file = self.file_manager.create_test_file(
            "test_default_settings.json", TestDataGenerator.create_settings_data()
        )

    def tearDown(self):
        """Clean up test files"""
        self.file_manager.cleanup()

    def test_settings_file_structure(self):
        """Test that settings file has correct structure"""
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        self.assertIn("spheres", settings)
        self.assertIn("projects", settings)
        self.assertIn("idle_settings", settings)
        self.assertIn("screenshot_settings", settings)

    def test_default_sphere_exists(self):
        """Test that a default sphere is marked"""
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        # Find default sphere
        default_sphere = None
        for sphere_name, sphere_data in settings["spheres"].items():
            if sphere_data.get("is_default", False):
                default_sphere = sphere_name
                break

        self.assertIsNotNone(default_sphere)

    def test_default_project_exists(self):
        """Test that a default project is marked"""
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        # Find default project
        default_project = None
        for project_name, project_data in settings["projects"].items():
            if project_data.get("is_default", False):
                default_project = project_name
                break

        self.assertIsNotNone(default_project)

    def test_projects_have_sphere_association(self):
        """Test that projects are associated with spheres"""
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        for project_name, project_data in settings["projects"].items():
            self.assertIn("sphere", project_data)
            self.assertIsNotNone(project_data["sphere"])

    def test_idle_settings_have_thresholds(self):
        """Test that idle settings have threshold values"""
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        idle_settings = settings["idle_settings"]
        self.assertIn("idle_threshold", idle_settings)
        self.assertIn("idle_break_threshold", idle_settings)

        self.assertGreater(idle_settings["idle_threshold"], 0)
        self.assertGreater(idle_settings["idle_break_threshold"], 0)


if __name__ == "__main__":
    unittest.main()
