"""
Google Sheets Integration Module

This module handles uploading session data to Google Sheets.
It appends new session data to the configured spreadsheet.
"""

import os
import json
import pickle
import re
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scopes for Google Sheets API
# Use read-only scope for viewing, full scope for editing
SCOPES_FULL = ["https://www.googleapis.com/auth/spreadsheets"]
SCOPES_READONLY = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


class GoogleSheetsUploader:
    """Handles uploading session data to Google Sheets"""

    def __init__(self, settings_file="settings.json", read_only=False):
        """
        Initialize the Google Sheets uploader

        Args:
            settings_file: Path to settings file containing Google API configuration
            read_only: If True, use read-only OAuth scope (for viewing only)
        """
        self.settings_file = settings_file
        self.settings = self._load_settings()
        self.credentials = None
        self.service = None
        self.read_only = read_only
        self.scopes = SCOPES_READONLY if read_only else SCOPES_FULL

    def _load_settings(self):
        """Load settings from file"""
        try:
            with open(self.settings_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            return {}

    def is_enabled(self):
        """Check if Google Sheets upload is enabled"""
        return self.settings.get("google_sheets", {}).get("enabled", False)

    def get_spreadsheet_id(self):
        """Get the configured spreadsheet ID from settings or environment variable"""
        # Try environment variable first (more secure)
        spreadsheet_id = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", "")

        # Fall back to settings file
        if not spreadsheet_id:
            spreadsheet_id = self.settings.get("google_sheets", {}).get(
                "spreadsheet_id", ""
            )

        # Validate spreadsheet ID format (should be alphanumeric, hyphens, underscores)
        if spreadsheet_id and not self._is_valid_spreadsheet_id(spreadsheet_id):
            print(f"Warning: Invalid spreadsheet ID format: {spreadsheet_id}")
            return ""

        return spreadsheet_id

    def _is_valid_spreadsheet_id(self, spreadsheet_id):
        """Validate spreadsheet ID format to prevent injection attacks"""
        # Google Sheets IDs are typically 44 characters, alphanumeric with hyphens/underscores
        if not spreadsheet_id:
            return False
        # Allow alphanumeric, hyphens, and underscores only
        return bool(re.match(r"^[a-zA-Z0-9_-]+$", spreadsheet_id))

    def get_sheet_name(self):
        """Get the configured sheet name (tab name within spreadsheet)"""
        sheet_name = self.settings.get("google_sheets", {}).get(
            "sheet_name", "Sessions"
        )

        # Validate sheet name to prevent injection attacks
        if not self._is_valid_sheet_name(sheet_name):
            print(f"Warning: Invalid sheet name format: {sheet_name}. Using default.")
            return "Sessions"

        return sheet_name

    def _is_valid_sheet_name(self, sheet_name):
        """Validate sheet name to prevent injection attacks"""
        if not sheet_name:
            return False
        # Sheet names should be reasonable length and not contain dangerous characters
        if len(sheet_name) > 100:
            return False
        # Disallow characters that could be used for injection
        dangerous_chars = ["<", ">", '"', "'", "\\", "/", "|", "?", "*"]
        return not any(char in sheet_name for char in dangerous_chars)

    def authenticate(self):
        """
        Authenticate with Google Sheets API

        Returns:
            bool: True if authentication successful, False otherwise
        """
        creds = None

        # Use environment variable for token file location (more secure)
        token_file = os.environ.get("GOOGLE_SHEETS_TOKEN_FILE", "token.pickle")

        # Get credentials file from environment variable or settings
        credentials_file = os.environ.get(
            "GOOGLE_SHEETS_CREDENTIALS_FILE",
            self.settings.get("google_sheets", {}).get(
                "credentials_file", "credentials.json"
            ),
        )

        # Validate credentials file path to prevent path traversal
        if credentials_file and not self._is_safe_file_path(credentials_file):
            print(f"Warning: Unsafe credentials file path: {credentials_file}")
            return False

        # Check if we have valid credentials
        if os.path.exists(token_file):
            try:
                with open(token_file, "rb") as token:
                    creds = pickle.load(token)
            except Exception as e:
                print(f"Error loading token file: {e}")
                creds = None

        # If credentials are invalid or don't exist, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    creds = None

            if not creds:
                if not os.path.exists(credentials_file):
                    print(f"Credentials file not found: {credentials_file}")
                    return False

                try:
                    # Use appropriate scopes based on read_only setting
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_file, self.scopes
                    )
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"Error during OAuth flow: {e}")
                    return False

            # Save the credentials for the next run
            try:
                with open(token_file, "wb") as token:
                    pickle.dump(creds, token)
            except Exception as e:
                print(f"Error saving credentials: {e}")

        self.credentials = creds

        # Build the service
        try:
            self.service = build("sheets", "v4", credentials=self.credentials)
            return True
        except Exception as e:
            print(f"Error building Google Sheets service: {e}")
            return False

    def _is_safe_file_path(self, file_path):
        """Validate file path to prevent directory traversal attacks"""
        if not file_path:
            return False

        # Disallow path traversal patterns
        dangerous_patterns = ["..", "~", "/etc/", "C:\\Windows\\", "%", "${"]
        file_path_lower = file_path.lower()

        for pattern in dangerous_patterns:
            if pattern.lower() in file_path_lower:
                return False

        # Only allow certain file extensions
        allowed_extensions = [".json", ".pickle", ".pkl"]
        if not any(file_path.endswith(ext) for ext in allowed_extensions):
            return False

        return True

    def _ensure_sheet_headers(self):
        """
        Ensure the spreadsheet has proper headers
        Creates headers if sheet is empty
        """
        if not self.service:
            return False

        try:
            spreadsheet_id = self.get_spreadsheet_id()
            sheet_name = self.get_sheet_name()

            # Try to read the first row
            range_name = f"{sheet_name}!A1:Z1"
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )

            values = result.get("values", [])

            # If no headers exist, add them
            if not values:
                headers = [
                    "Session ID",
                    "Date",
                    "Start Time",
                    "End Time",
                    "Sphere",
                    "Project",
                    "Total Duration (min)",
                    "Active Duration (min)",
                    "Break Duration (min)",
                    "Total Actions",
                    "Break Actions",
                    "Notes",
                ]

                body = {"values": [headers]}

                self.service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=f"{sheet_name}!A1",
                    valueInputOption="RAW",
                    body=body,
                ).execute()

                return True

            return True

        except HttpError as error:
            # If sheet doesn't exist, try to create it
            if error.resp.status == 400:
                try:
                    self._create_sheet()
                    return self._ensure_sheet_headers()
                except:
                    pass
            print(f"Error ensuring headers: {error}")
            return False
        except Exception as e:
            print(f"Error ensuring headers: {e}")
            return False

    def _create_sheet(self):
        """Create a new sheet in the spreadsheet"""
        if not self.service:
            return False

        try:
            spreadsheet_id = self.get_spreadsheet_id()
            sheet_name = self.get_sheet_name()

            request_body = {
                "requests": [{"addSheet": {"properties": {"title": sheet_name}}}]
            }

            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=request_body
            ).execute()

            return True

        except Exception as e:
            print(f"Error creating sheet: {e}")
            return False

    def upload_session(self, session_data, session_id):
        """
        Upload a session to Google Sheets

        Args:
            session_data: Dictionary containing session data
            session_id: Unique identifier for the session

        Returns:
            bool: True if upload successful, False otherwise
        """
        if not self.is_enabled():
            return False

        if not self.get_spreadsheet_id():
            print("No spreadsheet ID configured")
            return False

        # Authenticate if needed
        if not self.service:
            if not self.authenticate():
                return False

        # Ensure headers exist
        if not self._ensure_sheet_headers():
            return False

        try:
            # Extract data from session
            date = session_data.get("date", "")
            start_time = session_data.get("start_time", "")
            end_time = session_data.get("end_time", "")
            sphere = session_data.get("sphere", "")
            project = session_data.get("project", "")

            # Convert durations from seconds to minutes
            total_duration = session_data.get("total_duration", 0) / 60
            active_duration = session_data.get("active_duration", 0) / 60
            break_duration = session_data.get("break_duration", 0) / 60

            # Count actions
            total_actions = len(session_data.get("actions", []))
            break_actions_list = session_data.get("break_actions", [])
            break_actions = sum(len(ba.get("actions", [])) for ba in break_actions_list)

            # Get notes if any
            notes = session_data.get("notes", "")

            # Prepare row data
            row = [
                session_id,
                date,
                start_time,
                end_time,
                sphere,
                project,
                round(total_duration, 2),
                round(active_duration, 2),
                round(break_duration, 2),
                total_actions,
                break_actions,
                notes,
            ]

            # Append to sheet
            spreadsheet_id = self.get_spreadsheet_id()
            sheet_name = self.get_sheet_name()
            range_name = f"{sheet_name}!A:L"

            body = {"values": [row]}

            result = (
                self.service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body=body,
                )
                .execute()
            )

            print(
                f"Session uploaded to Google Sheets: {result.get('updates', {}).get('updatedCells', 0)} cells updated"
            )
            return True

        except HttpError as error:
            print(f"HTTP Error uploading to Google Sheets: {error}")
            return False
        except Exception as e:
            print(f"Error uploading to Google Sheets: {e}")
            return False

    def test_connection(self):
        """
        Test the connection to Google Sheets

        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.get_spreadsheet_id():
            return (False, "No spreadsheet ID configured")

        try:
            if not self.authenticate():
                return (False, "Authentication failed")

            # Try to read spreadsheet properties
            spreadsheet_id = self.get_spreadsheet_id()
            result = (
                self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            )

            title = result.get("properties", {}).get("title", "Unknown")
            return (True, f"Connected to spreadsheet: {title}")

        except HttpError as error:
            if error.resp.status == 404:
                return (False, "Spreadsheet not found. Check the spreadsheet ID.")
            return (False, f"HTTP Error: {error}")
        except Exception as e:
            return (False, f"Error: {str(e)}")
