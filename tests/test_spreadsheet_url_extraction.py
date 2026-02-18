"""
Tests for Google Sheets Spreadsheet ID URL Extraction

Tests that full Google Sheets URLs are automatically parsed to extract just the ID.
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestSpreadsheetIDExtraction(unittest.TestCase):
    """Test extracting spreadsheet ID from URLs"""

    def test_extract_id_from_full_url(self):
        """Test extracting ID from full Google Sheets URL"""
        from src.settings_frame import extract_spreadsheet_id_from_url

        url = "https://docs.google.com/spreadsheets/d/1qKeL8HR_zf3XQK51n43U7oBQpLgd3eziGPxrwR6DNNk/edit?gid=0#gid=0"
        expected_id = "1qKeL8HR_zf3XQK51n43U7oBQpLgd3eziGPxrwR6DNNk"

        result = extract_spreadsheet_id_from_url(url)
        self.assertEqual(result, expected_id)

    def test_extract_id_from_url_without_query_params(self):
        """Test extracting ID from URL without query parameters"""
        from src.settings_frame import extract_spreadsheet_id_from_url

        url = "https://docs.google.com/spreadsheets/d/139zivLcU4VoqZpodGkdqeKpoiQobIBDxZRxfkFoGaY4/edit"
        expected_id = "139zivLcU4VoqZpodGkdqeKpoiQobIBDxZRxfkFoGaY4"

        result = extract_spreadsheet_id_from_url(url)
        self.assertEqual(result, expected_id)

    def test_plain_id_passes_through(self):
        """Test that plain ID (not URL) passes through unchanged"""
        from src.settings_frame import extract_spreadsheet_id_from_url

        plain_id = "1qKeL8HR_zf3XQK51n43U7oBQpLgd3eziGPxrwR6DNNk"

        result = extract_spreadsheet_id_from_url(plain_id)
        self.assertEqual(result, plain_id)

    def test_extract_id_with_trailing_slash(self):
        """Test extracting ID when URL has trailing slashes"""
        from src.settings_frame import extract_spreadsheet_id_from_url

        url = "https://docs.google.com/spreadsheets/d/1qKeL8HR_zf3XQK51n43U7oBQpLgd3eziGPxrwR6DNNk/"
        expected_id = "1qKeL8HR_zf3XQK51n43U7oBQpLgd3eziGPxrwR6DNNk"

        result = extract_spreadsheet_id_from_url(url)
        self.assertEqual(result, expected_id)

    def test_extract_id_from_mobile_url(self):
        """Test extracting ID from mobile Google Sheets URL"""
        from src.settings_frame import extract_spreadsheet_id_from_url

        # Mobile URLs might have different format
        url = "https://docs.google.com/spreadsheets/d/1qKeL8HR_zf3XQK51n43U7oBQpLgd3eziGPxrwR6DNNk/edit#gid=0"
        expected_id = "1qKeL8HR_zf3XQK51n43U7oBQpLgd3eziGPxrwR6DNNk"

        result = extract_spreadsheet_id_from_url(url)
        self.assertEqual(result, expected_id)

    def test_empty_string_returns_empty(self):
        """Test that empty string returns empty"""
        from src.settings_frame import extract_spreadsheet_id_from_url

        result = extract_spreadsheet_id_from_url("")
        self.assertEqual(result, "")

    def test_invalid_url_returns_original(self):
        """Test that invalid URL returns original value"""
        from src.settings_frame import extract_spreadsheet_id_from_url

        invalid = "not a valid url or id"
        result = extract_spreadsheet_id_from_url(invalid)
        self.assertEqual(result, invalid)

    def test_extract_id_with_underscores_and_hyphens(self):
        """Test extracting ID with various valid characters"""
        from src.settings_frame import extract_spreadsheet_id_from_url

        url = "https://docs.google.com/spreadsheets/d/abc-123_XYZ-456/edit"
        expected_id = "abc-123_XYZ-456"

        result = extract_spreadsheet_id_from_url(url)
        self.assertEqual(result, expected_id)


if __name__ == "__main__":
    unittest.main()
