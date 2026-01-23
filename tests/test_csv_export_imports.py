"""
Import Verification Tests for CSV Export Feature

These tests verify that all required modules are properly imported.
This catches issues that mocked tests might miss.
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestCSVExportImports(unittest.TestCase):
    """Test that all required imports are present in settings_frame.py"""

    def test_settings_frame_imports_os(self):
        """Test that settings_frame imports os module"""
        import settings_frame

        self.assertTrue(
            hasattr(settings_frame, "os"),
            "settings_frame should import os module (needed for file operations)",
        )

    def test_settings_frame_imports_csv(self):
        """Test that settings_frame imports csv module"""
        import settings_frame

        self.assertTrue(
            hasattr(settings_frame, "csv"),
            "settings_frame should import csv module (needed for CSV export)",
        )

    def test_settings_frame_imports_subprocess(self):
        """Test that settings_frame imports subprocess module"""
        import settings_frame

        self.assertTrue(
            hasattr(settings_frame, "subprocess"),
            "settings_frame should import subprocess module (needed for opening folders)",
        )

    def test_settings_frame_imports_platform(self):
        """Test that settings_frame imports platform module"""
        import settings_frame

        self.assertTrue(
            hasattr(settings_frame, "platform"),
            "settings_frame should import platform module (needed for OS detection)",
        )

    def test_settings_frame_can_be_imported(self):
        """Test that settings_frame module can be imported without errors"""
        try:
            from src import settings_frame

            # If we get here, import succeeded
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import settings_frame: {e}")

    def test_settings_frame_class_exists(self):
        """Test that SettingsFrame class exists"""
        import settings_frame

        self.assertTrue(
            hasattr(settings_frame, "SettingsFrame"),
            "settings_frame should have SettingsFrame class",
        )

    def test_save_all_data_to_csv_method_exists(self):
        """Test that save_all_data_to_csv method exists"""
        from settings_frame import SettingsFrame

        self.assertTrue(
            hasattr(SettingsFrame, "save_all_data_to_csv"),
            "SettingsFrame should have save_all_data_to_csv method",
        )


if __name__ == "__main__":
    unittest.main()
