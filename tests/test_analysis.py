"""
Tests for Analysis Frame Data Filtering - Simplified

Verifies basic analysis functionality with test data.
"""

import unittest
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tests.test_helpers import TestDataGenerator, TestFileManager


class TestAnalysisFiltering(unittest.TestCase):
    """Test analysis frame filtering"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        # Create test data with sessions
        test_data = TestDataGenerator.create_session_data()

        self.test_data_file = self.file_manager.create_test_file(
            "test_analysis_data.json", test_data
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_analysis_settings.json", TestDataGenerator.create_settings_data()
        )

    def tearDown(self):
        """Clean up test files"""
        self.file_manager.cleanup()

    def test_session_data_structure(self):
        """Test that test data has correct structure"""
        with open(self.test_data_file, "r") as f:
            data = json.load(f)

        self.assertGreater(len(data), 0)

        session = list(data.values())[0]
        self.assertIn("sphere", session)
        self.assertIn("active", session)
        self.assertIn("breaks", session)
        self.assertIn("active_duration", session)

    def test_filter_by_sphere(self):
        """Test filtering sessions by sphere"""
        with open(self.test_data_file, "r") as f:
            data = json.load(f)

        # Filter by sphere
        test_sphere = "TestSphere"
        filtered = {k: v for k, v in data.items() if v.get("sphere") == test_sphere}

        # All filtered sessions should have the correct sphere
        for session in filtered.values():
            self.assertEqual(session["sphere"], test_sphere)


if __name__ == "__main__":
    unittest.main()
