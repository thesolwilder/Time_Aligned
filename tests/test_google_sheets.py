"""
Tests for Google Sheets Integration

Verifies Google Sheets API configuration, authentication, and data upload.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from test_helpers import TestDataGenerator, TestFileManager


class TestGoogleSheetsIntegration(unittest.TestCase):
    """Test Google Sheets integration functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)  # Ensures cleanup even if test fails
        self.test_settings_file = "test_google_settings.json"

        # Create settings with Google Sheets config
        settings = TestDataGenerator.create_settings_data()
        settings["google_sheets"] = {
            "enabled": True,
            "spreadsheet_id": "test_spreadsheet_123",
            "sheet_name": "Sessions",
            "credentials_file": "credentials.json",
        }

        self.file_manager.create_test_file(self.test_settings_file, settings)

    def tearDown(self):
        """Clean up test files"""
        self.file_manager.cleanup()

    def test_google_sheets_settings_structure(self):
        """Test that Google Sheets settings have correct structure"""
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        self.assertIn("google_sheets", settings)

        google_settings = settings["google_sheets"]
        self.assertIn("enabled", google_settings)
        self.assertIn("spreadsheet_id", google_settings)
        self.assertIn("sheet_name", google_settings)
        self.assertIn("credentials_file", google_settings)

    def test_google_sheets_can_be_disabled(self):
        """Test that Google Sheets can be disabled"""
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        # Disable Google Sheets
        settings["google_sheets"]["enabled"] = False

        with open(self.test_settings_file, "w") as f:
            json.dump(settings, f)

        # Reload and verify
        with open(self.test_settings_file, "r") as f:
            reloaded = json.load(f)

        self.assertFalse(reloaded["google_sheets"]["enabled"])

    @patch("google_sheets_integration.os.path.exists")
    @patch("google_sheets_integration.build")
    def test_uploader_initialization(self, mock_build, mock_exists):
        """Test GoogleSheetsUploader initialization"""
        try:
            from google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)

            # Verify settings loaded
            self.assertIsNotNone(uploader.settings)
            self.assertEqual(uploader.settings_file, self.test_settings_file)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("google_sheets_integration.os.path.exists")
    def test_is_enabled_check(self, mock_exists):
        """Test checking if Google Sheets upload is enabled"""
        try:
            from google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)
            self.assertTrue(uploader.is_enabled())

            # Test with disabled settings
            disabled_settings = TestDataGenerator.create_settings_data()
            disabled_settings["google_sheets"] = {"enabled": False}

            disabled_file = "test_disabled_google.json"
            self.file_manager.create_test_file(disabled_file, disabled_settings)

            uploader2 = GoogleSheetsUploader(disabled_file)
            self.assertFalse(uploader2.is_enabled())
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("google_sheets_integration.os.path.exists")
    def test_get_spreadsheet_id(self, mock_exists):
        """Test retrieving spreadsheet ID from settings"""
        try:
            from google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)
            spreadsheet_id = uploader.get_spreadsheet_id()

            self.assertEqual(spreadsheet_id, "test_spreadsheet_123")
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("google_sheets_integration.os.path.exists")
    def test_get_sheet_name(self, mock_exists):
        """Test retrieving sheet name from settings"""
        try:
            from google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)
            sheet_name = uploader.get_sheet_name()

            self.assertEqual(sheet_name, "Sessions")
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("google_sheets_integration.os.path.exists")
    @patch("google_sheets_integration.build")
    @patch("builtins.open", new_callable=mock_open)
    @patch("google_sheets_integration.pickle.load")
    def test_authenticate_with_existing_token(
        self, mock_pickle_load, mock_file, mock_build, mock_exists
    ):
        """Test authentication when valid token exists"""
        try:
            from google_sheets_integration import GoogleSheetsUploader

            # Mock existing valid credentials
            mock_creds = Mock()
            mock_creds.valid = True
            mock_creds.expired = False
            mock_pickle_load.return_value = mock_creds

            # Mock file existence
            mock_exists.return_value = True

            # Mock service build
            mock_service = Mock()
            mock_build.return_value = mock_service

            uploader = GoogleSheetsUploader(self.test_settings_file)
            result = uploader.authenticate()

            self.assertTrue(result)
            self.assertIsNotNone(uploader.credentials)
            self.assertIsNotNone(uploader.service)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("google_sheets_integration.os.path.exists")
    def test_authentication_fails_without_credentials_file(self, mock_exists):
        """Test that authentication fails gracefully without credentials file"""
        try:
            from google_sheets_integration import GoogleSheetsUploader

            # Mock that no token or credentials exist
            mock_exists.return_value = False

            uploader = GoogleSheetsUploader(self.test_settings_file)
            result = uploader.authenticate()

            self.assertFalse(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    def test_session_data_format_for_upload(self):
        """Test that session data can be formatted for Google Sheets"""
        session_data = TestDataGenerator.create_session_data()
        session = list(session_data.values())[0]

        # Verify session has fields needed for Google Sheets
        self.assertIn("sphere", session)
        self.assertIn("date", session)
        self.assertIn("start_time", session)
        self.assertIn("end_time", session)
        self.assertIn("active_duration", session)
        self.assertIn("break_duration", session)
        self.assertIn("total_duration", session)

        # Verify active periods have project info (added during completion)
        if session["active"]:
            # In real usage, projects are added during completion
            # Here we just verify the structure is ready
            self.assertIsInstance(session["active"], list)

    @patch("google_sheets_integration.os.path.exists")
    def test_spreadsheet_id_required(self, mock_exists):
        """Test that spreadsheet ID is required for upload"""
        try:
            from google_sheets_integration import GoogleSheetsUploader

            # Create settings without spreadsheet ID
            no_id_settings = TestDataGenerator.create_settings_data()
            no_id_settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "",  # Empty ID
                "sheet_name": "Sessions",
            }

            no_id_file = "test_no_spreadsheet_id.json"
            self.file_manager.create_test_file(no_id_file, no_id_settings)

            uploader = GoogleSheetsUploader(no_id_file)
            spreadsheet_id = uploader.get_spreadsheet_id()

            # Should return empty string
            self.assertEqual(spreadsheet_id, "")

            # Upload should not proceed without ID
            self.assertTrue(uploader.is_enabled())  # Enabled
            self.assertEqual(len(spreadsheet_id), 0)  # But no ID
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    def test_default_sheet_name(self):
        """Test default sheet name when not specified"""
        try:
            from google_sheets_integration import GoogleSheetsUploader

            # Create settings without sheet_name
            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "test_123",
                # No sheet_name specified
            }

            test_file = "test_default_sheet.json"
            self.file_manager.create_test_file(test_file, settings)

            uploader = GoogleSheetsUploader(test_file)
            sheet_name = uploader.get_sheet_name()

            # Should default to "Sessions"
            self.assertEqual(sheet_name, "Sessions")
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")


class TestGoogleSheetsUploadFlow(unittest.TestCase):
    """Test complete upload flow from completion to Google Sheets"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

    def tearDown(self):
        """Clean up test files"""
        self.file_manager.cleanup()

    def test_upload_method_exists(self):
        """Test that completion frame has upload method"""
        try:
            from frames.completion_frame import CompletionFrame

            # Verify the upload method exists
            self.assertTrue(hasattr(CompletionFrame, "_upload_to_google_sheets"))
        except ImportError as e:
            self.skipTest(f"Completion frame not available: {e}")

    def test_google_sheets_optional_dependency(self):
        """Test that app works without Google Sheets dependencies"""
        # Test that the app can handle missing Google API libraries
        try:
            from google_sheets_integration import GoogleSheetsUploader

            # If import succeeds, verify it handles missing credentials gracefully
            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {"enabled": False}

            test_file = "test_optional.json"
            self.file_manager.create_test_file(test_file, settings)

            uploader = GoogleSheetsUploader(test_file)
            self.assertFalse(uploader.is_enabled())
        except ImportError:
            # Expected when Google API libraries not installed
            # App should continue working without Google Sheets
            pass


class TestGoogleSheetsInputValidation(unittest.TestCase):
    """Test input validation for Google Sheets integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)

    def test_valid_spreadsheet_id(self):
        """Test that valid spreadsheet IDs are accepted"""
        try:
            from google_sheets_integration import GoogleSheetsUploader

            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                "sheet_name": "Sessions",
            }

            test_file = "test_valid_id.json"
            self.file_manager.create_test_file(test_file, settings)

            uploader = GoogleSheetsUploader(test_file)
            spreadsheet_id = uploader.get_spreadsheet_id()

            # Should return the valid ID
            self.assertEqual(
                spreadsheet_id, "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
            )
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    def test_malicious_spreadsheet_id_rejected(self):
        """Test that malicious spreadsheet IDs are rejected"""
        try:
            from google_sheets_integration import GoogleSheetsUploader

            malicious_ids = [
                "../../../etc/passwd",
                "'; DROP TABLE sessions; --",
                "<script>alert('xss')</script>",
                "../../sensitive/data",
                "C:\\Windows\\System32\\config",
            ]

            for malicious_id in malicious_ids:
                settings = TestDataGenerator.create_settings_data()
                settings["google_sheets"] = {
                    "enabled": True,
                    "spreadsheet_id": malicious_id,
                    "sheet_name": "Sessions",
                }

                test_file = "test_malicious_id.json"
                self.file_manager.create_test_file(test_file, settings)

                uploader = GoogleSheetsUploader(test_file)
                spreadsheet_id = uploader.get_spreadsheet_id()

                # Should reject malicious ID and return empty string
                self.assertEqual(
                    spreadsheet_id, "", f"Failed to reject malicious ID: {malicious_id}"
                )
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    def test_malicious_sheet_name_sanitized(self):
        """Test that malicious sheet names are sanitized"""
        try:
            from google_sheets_integration import GoogleSheetsUploader

            malicious_names = [
                "<script>alert('xss')</script>",
                "Sheet'; DROP TABLE--",
                "../../../secrets",
                "Sheet\\with\\paths",
            ]

            for malicious_name in malicious_names:
                settings = TestDataGenerator.create_settings_data()
                settings["google_sheets"] = {
                    "enabled": True,
                    "spreadsheet_id": "valid_id_123",
                    "sheet_name": malicious_name,
                }

                test_file = "test_malicious_name.json"
                self.file_manager.create_test_file(test_file, settings)

                uploader = GoogleSheetsUploader(test_file)
                sheet_name = uploader.get_sheet_name()

                # Should sanitize to default "Sessions"
                self.assertEqual(
                    sheet_name,
                    "Sessions",
                    f"Failed to sanitize malicious sheet name: {malicious_name}",
                )
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    def test_path_traversal_in_credentials_blocked(self):
        """Test that path traversal in credentials file is blocked"""
        try:
            from google_sheets_integration import GoogleSheetsUploader

            dangerous_paths = [
                "../../../etc/passwd",
                "C:\\Windows\\System32\\config\\sam",
                "~/sensitive/data.json",
                "%APPDATA%/secrets.json",
            ]

            for dangerous_path in dangerous_paths:
                settings = TestDataGenerator.create_settings_data()
                settings["google_sheets"] = {
                    "enabled": True,
                    "spreadsheet_id": "valid_id",
                    "credentials_file": dangerous_path,
                }

                test_file = "test_path_traversal.json"
                self.file_manager.create_test_file(test_file, settings)

                uploader = GoogleSheetsUploader(test_file)
                # Authentication should fail for unsafe paths
                result = uploader.authenticate()
                self.assertFalse(
                    result, f"Failed to block path traversal: {dangerous_path}"
                )
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    def test_environment_variables_override_settings(self):
        """Test that environment variables take precedence over settings file"""
        try:
            import os
            from google_sheets_integration import GoogleSheetsUploader

            # Set environment variable
            os.environ["GOOGLE_SHEETS_SPREADSHEET_ID"] = "env_spreadsheet_123"

            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "settings_spreadsheet_456",
                "sheet_name": "Sessions",
            }

            test_file = "test_env_vars.json"
            self.file_manager.create_test_file(test_file, settings)

            uploader = GoogleSheetsUploader(test_file)
            spreadsheet_id = uploader.get_spreadsheet_id()

            # Should use environment variable, not settings file
            self.assertEqual(spreadsheet_id, "env_spreadsheet_123")

            # Cleanup
            del os.environ["GOOGLE_SHEETS_SPREADSHEET_ID"]
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")


if __name__ == "__main__":
    unittest.main()
