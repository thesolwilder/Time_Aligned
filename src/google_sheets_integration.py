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
from tkinter import messagebox
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.constants import DEFAULT_SETTINGS_FILE

# Scopes for Google Sheets API
# Use read-only scope for viewing, full scope for editing
SCOPES_FULL = ["https://www.googleapis.com/auth/spreadsheets"]
SCOPES_READONLY = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def escape_for_sheets(text):
    """
    Escape text for safe upload to Google Sheets.
    Prevents formula injection and XSS attacks.

    Args:
        text: The text to escape

    Returns:
        Escaped text string safe for Google Sheets
    """
    if not text:
        return ""

    text = str(text)

    # Prevent formula injection - formulas start with =, +, -, @, or |
    if text and text[0] in ("=", "+", "-", "@", "|"):
        text = "'" + text  # Prefix with single quote to treat as text

    # Escape HTML/XML special characters to prevent XSS
    text = text.replace("<", "&lt;").replace(">", "&gt;")

    return text


class GoogleSheetsUploader:
    """Handles uploading session data to Google Sheets"""

    def __init__(self, settings_file=DEFAULT_SETTINGS_FILE, read_only=False):
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
        """Load settings from file with proper error handling.

        Returns:
            dict: Settings dictionary, or empty dict if file doesn't exist or is invalid
        """
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            # Settings file missing is acceptable - use defaults
            return {}
        except json.JSONDecodeError as e:
            messagebox.showerror(
                "Settings Error",
                f"Invalid JSON in settings file:\n{self.settings_file}\n\n{str(e)}",
            )
            return {}
        except PermissionError:
            messagebox.showerror(
                "Settings Error",
                f"Permission denied reading settings file:\n{self.settings_file}",
            )
            return {}
        except Exception as e:
            messagebox.showerror(
                "Settings Error",
                f"Unexpected error loading settings:\n{type(e).__name__}: {str(e)}",
            )
            return {}

    def is_enabled(self):
        """Check if Google Sheets upload is enabled in settings.

        Guard method called before any Google Sheets API operations to check
        if user has enabled the integration.

        Called from 6+ locations:
        - upload_session() - Guard before upload attempt
        - Session completion checks
        - UI elements (enable/disable upload buttons)
        - Test setup verification

        Returns:
            Boolean - True if enabled in settings, False otherwise

        Note:
            Returns False if google_sheets section missing from settings.
            Does NOT check if credentials are valid, only if feature enabled.
        """
        return self.settings.get("google_sheets", {}).get("enabled", False)

    def get_spreadsheet_id(self):
        """Get Google Sheets spreadsheet ID with security validation.

        Retrieves spreadsheet ID from environment variable (preferred for security)
        or settings file (fallback). Validates format to prevent injection attacks.

        Called from 12+ locations:
        - All Google Sheets API operations
        - Upload session validation
        - Settings verification
        - Test setup

        Lookup priority:
        1. Environment variable: GOOGLE_SHEETS_SPREADSHEET_ID (most secure)
        2. Settings file: settings["google_sheets"]["spreadsheet_id"]

        Security:
        - Validates ID format via _is_valid_spreadsheet_id()
        - Rejects IDs with dangerous characters (prevents injection)
        - Google Sheets IDs are 44-char alphanumeric with hyphens/underscores

        Returns:
            String spreadsheet ID if valid, empty string if missing/invalid

        Note:
            Environment variable preferred to avoid storing sensitive IDs in settings.json.
            Empty string return signals caller to skip Google Sheets operations.
        """
        # Try environment variable first (more secure)
        spreadsheet_id = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", "")

        # Fall back to settings file
        if not spreadsheet_id:
            spreadsheet_id = self.settings.get("google_sheets", {}).get(
                "spreadsheet_id", ""
            )

        # Validate spreadsheet ID format (should be alphanumeric, hyphens, underscores)
        if spreadsheet_id and not self._is_valid_spreadsheet_id(spreadsheet_id):
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
        """Get Google Sheets sheet/tab name with security validation.

        Retrieves the sheet name (tab name within the spreadsheet) from settings.
        Validates to prevent injection attacks and applies length limits.

        Called from 6+ locations:
        - upload_session() - Sheet name for append operation
        - Google Sheets API calls
        - Settings verification

        Security:
        - Validates via _is_valid_sheet_name()
        - Rejects sheet names >100 characters
        - Rejects dangerous characters that could enable injection
        - Falls back to "Sessions" default if validation fails

        Returns:
            String sheet name (defaults to "Sessions" if missing/invalid)

        Note:
            Always returns a valid sheet name - never returns empty string.
            Validation prevents malicious sheet names from reaching Google API.
        """
        sheet_name = self.settings.get("google_sheets", {}).get(
            "sheet_name", "Sessions"
        )

        # Validate sheet name to prevent injection attacks
        if not self._is_valid_sheet_name(sheet_name):
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
            return False

        # Check if we have valid credentials
        if os.path.exists(token_file):
            try:
                with open(token_file, "rb") as token:
                    creds = pickle.load(token)
            except PermissionError:
                messagebox.showwarning(
                    "Google Sheets Authentication",
                    f"Permission denied reading authentication token:\n{token_file}\n\n"
                    "You may need to check file permissions or run as administrator.",
                )
                creds = None
            except (pickle.UnpicklingError, EOFError, ValueError):
                # Corrupted/invalid token file - will re-authenticate automatically
                creds = None
            except Exception:
                # Unexpected error - will attempt re-authentication
                creds = None

        # If credentials are invalid or don't exist, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as error:
                    creds = None

            if not creds:
                if not os.path.exists(credentials_file):
                    return False

                try:
                    # Use appropriate scopes based on read_only setting
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_file, self.scopes
                    )
                    creds = flow.run_local_server(port=0)
                except Exception as error:
                    return False

            # Save the credentials for the next run
            try:
                with open(token_file, "wb") as token:
                    pickle.dump(creds, token)
            except Exception as error:
                pass

        self.credentials = creds

        # Build the service
        try:
            self.service = build("sheets", "v4", credentials=self.credentials)
            return True
        except Exception as error:
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
                    "Sphere",
                    "Session Start Time",
                    "Session End Time",
                    "Session Total Duration (min)",
                    "Session Active Duration (min)",
                    "Session Break Duration (min)",
                    "Type",
                    "Project",
                    "Secondary Project",
                    "Secondary Comment",
                    "Secondary Percentage",
                    "Activity Start",
                    "Activity End",
                    "Activity Duration (min)",
                    "Activity Comment",
                    "Break Action",
                    "Secondary Action",
                    "Active Notes",
                    "Break Notes",
                    "Idle Notes",
                    "Session Notes",
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
            return False
        except Exception as e:
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
            return False

    def upload_session(self, session_data, session_id):
        """
        Upload a session to Google Sheets with detailed format matching CSV export

        Args:
            session_data: Dictionary containing session data
            session_id: Unique identifier for the session

        Returns:
            bool: True if upload successful, False otherwise
        """
        if not self.is_enabled():
            return False

        if not self.get_spreadsheet_id():
            return False

        # Authenticate if needed
        if not self.service:
            if not self.authenticate():
                return False

        # Ensure headers exist
        if not self._ensure_sheet_headers():
            return False

        try:
            # Extract session-level data
            date = session_data.get("date", "")
            sphere = session_data.get("sphere", "")
            start_time = session_data.get("start_time", "")
            end_time = session_data.get("end_time", "")

            # Convert durations from seconds to minutes
            total_duration = round(session_data.get("total_duration", 0) / 60, 2)
            active_duration = round(session_data.get("active_duration", 0) / 60, 2)
            break_duration = round(session_data.get("break_duration", 0) / 60, 2)

            # Get session comments
            session_comments = session_data.get("session_comments", {})
            active_notes = escape_for_sheets(session_comments.get("active_notes", ""))
            break_notes = escape_for_sheets(session_comments.get("break_notes", ""))
            idle_notes = escape_for_sheets(session_comments.get("idle_notes", ""))
            session_notes = escape_for_sheets(session_comments.get("session_notes", ""))

            # Process active periods, breaks, and idle periods
            active_periods = session_data.get("active", [])
            breaks = session_data.get("breaks", [])
            idle_periods = session_data.get("idle_periods", [])

            # Prepare all rows to upload
            rows = []

            # Process active periods
            if active_periods:
                for active in active_periods:
                    # Extract primary and secondary project information
                    primary_project = ""
                    secondary_project = ""
                    secondary_comment = ""
                    secondary_percentage = ""

                    if active.get("project"):
                        # Single project case
                        primary_project = escape_for_sheets(active.get("project", ""))
                    else:
                        # Multiple projects case
                        for project_item in active.get("projects", []):
                            if project_item.get("project_primary", True):
                                primary_project = escape_for_sheets(
                                    project_item.get("name", "")
                                )
                            else:
                                secondary_project = escape_for_sheets(
                                    project_item.get("name", "")
                                )
                                secondary_comment = escape_for_sheets(
                                    project_item.get("comment", "")
                                )
                                secondary_percentage = project_item.get(
                                    "percentage", ""
                                )

                    row = [
                        session_id,
                        date,
                        sphere,
                        start_time,
                        end_time,
                        total_duration,
                        active_duration,
                        break_duration,
                        "active",
                        primary_project,
                        secondary_project,
                        secondary_comment,
                        secondary_percentage,
                        active.get("start", ""),
                        active.get("end", ""),
                        round(active.get("duration", 0) / 60, 2),
                        escape_for_sheets(active.get("comment", "")),
                        "",  # break_action
                        "",  # secondary_action
                        active_notes,
                        break_notes,
                        idle_notes,
                        session_notes,
                    ]
                    rows.append(row)

            # Process breaks
            if breaks:
                for brk in breaks:
                    # Extract primary and secondary action information
                    primary_action = ""
                    secondary_action = ""
                    secondary_comment = ""
                    secondary_percentage = ""

                    if brk.get("action"):
                        # Single action case
                        primary_action = escape_for_sheets(brk.get("action", ""))
                    else:
                        # Multiple actions case
                        for action_item in brk.get("actions", []):
                            if action_item.get("action_primary", True):
                                primary_action = escape_for_sheets(
                                    action_item.get("name", "")
                                )
                            else:
                                secondary_action = escape_for_sheets(
                                    action_item.get("name", "")
                                )
                                secondary_comment = escape_for_sheets(
                                    action_item.get("comment", "")
                                )
                                secondary_percentage = action_item.get("percentage", "")

                    row = [
                        session_id,
                        date,
                        sphere,
                        start_time,
                        end_time,
                        total_duration,
                        active_duration,
                        break_duration,
                        "break",
                        "",  # project
                        "",  # secondary_project
                        secondary_comment,
                        secondary_percentage,
                        brk.get("start", ""),
                        "",  # activity_end
                        round(brk.get("duration", 0) / 60, 2),
                        escape_for_sheets(brk.get("comment", "")),
                        primary_action,
                        secondary_action,
                        active_notes,
                        break_notes,
                        idle_notes,
                        session_notes,
                    ]
                    rows.append(row)

            # Process idle periods
            if idle_periods:
                for idle in idle_periods:
                    row = [
                        session_id,
                        date,
                        sphere,
                        start_time,
                        end_time,
                        total_duration,
                        active_duration,
                        break_duration,
                        "idle",
                        "",  # project
                        "",  # secondary_project
                        "",  # secondary_comment
                        "",  # secondary_percentage
                        idle.get("start", ""),
                        idle.get("end", ""),
                        round(idle.get("duration", 0) / 60, 2),
                        "",  # activity_comment
                        "",  # break_action
                        "",  # secondary_action
                        active_notes,
                        break_notes,
                        idle_notes,
                        session_notes,
                    ]
                    rows.append(row)

            # If no active periods, breaks, or idle, create summary row
            if not active_periods and not breaks and not idle_periods:
                row = [
                    session_id,
                    date,
                    sphere,
                    start_time,
                    end_time,
                    total_duration,
                    active_duration,
                    break_duration,
                    "session_summary",
                    "",  # project
                    "",  # secondary_project
                    "",  # secondary_comment
                    "",  # secondary_percentage
                    "",  # activity_start
                    "",  # activity_end
                    0,  # activity_duration
                    "",  # activity_comment
                    "",  # break_action
                    "",  # secondary_action
                    active_notes,
                    break_notes,
                    idle_notes,
                    session_notes,
                ]
                rows.append(row)

            # Append all rows to sheet
            if rows:
                spreadsheet_id = self.get_spreadsheet_id()
                sheet_name = self.get_sheet_name()
                range_name = f"{sheet_name}!A:W"

                body = {"values": rows}

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

                return True
            else:
                return False

        except HttpError as error:
            return False
        except Exception as e:
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
