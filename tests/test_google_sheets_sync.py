"""
Tests for Google Sheets Automatic Sync

Verifies that every finished session reaches Google Sheets exactly once:
re-uploads replace a session's rows instead of duplicating them, sessions that
failed to upload are retried on the next sync, Skip uploads like Save, and the
app syncs once at startup. The Sheets API is replaced by an in-memory fake, so
nothing touches a real spreadsheet.
"""

import json
import os
import sys
import tempfile
import tkinter as tk
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.auth.exceptions import TransportError

import time_tracker
from time_tracker import TimeTracker
from src.completion_frame import CompletionFrame
from src.constants import (
    GOOGLE_SHEETS_STARTUP_SYNC_DELAY_MS,
    GOOGLE_SIGN_IN_TIMEOUT_SECONDS,
    SHEETS_UPLOAD_LOG_FILE,
)
from src.google_sheets_integration import SHEET_HEADERS, GoogleSheetsUploader
from test_helpers import TestDataGenerator, TestFileManager, safe_teardown_tk_root

SHEET_NAME = "Sessions"


def make_session(date, comment=""):
    """Build a finished session with one active period and one break (two rows)"""
    return {
        "date": date,
        "sphere": "Work",
        "start_time": "09:00:00",
        "end_time": "10:00:00",
        "start_timestamp": 1790000000,
        "end_timestamp": 1790003600,
        "total_duration": 3600,
        "active_duration": 3000,
        "break_duration": 600,
        "active": [
            {
                "start": "09:00:00",
                "end": "09:50:00",
                "duration": 3000,
                "project": "Reports",
                "comment": comment,
            }
        ],
        "breaks": [{"start": "09:50:00", "duration": 600, "action": "Resting"}],
        "idle_periods": [],
    }


def write_settings(folder, sheet_name=SHEET_NAME, file_name="settings.json"):
    """Write a settings file with Google Sheets enabled and return its path"""
    settings = TestDataGenerator.create_settings_data()
    settings["google_sheets"] = {
        "enabled": True,
        "spreadsheet_id": "test_spreadsheet_123",
        "sheet_name": sheet_name,
    }
    settings_file = os.path.join(folder, file_name)
    with open(settings_file, "w") as f:
        json.dump(settings, f)
    return settings_file


class FakeSheetsService:
    """In-memory stand-in for the Sheets API calls an upload makes.

    Holds one sheet as a list of rows (row 0 is the header). Both
    service.spreadsheets() and .values() return this object; the two get()
    calls are told apart by their arguments.
    """

    SHEET_ID = 7

    def __init__(self):
        self.rows = [list(SHEET_HEADERS)]
        self.append_count = 0
        self.append_error = None

    def spreadsheets(self):
        return self

    def values(self):
        return self

    def get(self, spreadsheetId, range=None, fields=None):
        if fields is not None:
            sheet = {"properties": {"sheetId": self.SHEET_ID, "title": SHEET_NAME}}
            result = {"sheets": [sheet]}
        elif range.endswith("!A1:Z1"):
            result = {"values": self.rows[:1]}
        else:
            result = {"values": [row[:1] for row in self.rows]}
        return Mock(execute=Mock(return_value=result))

    def append(self, spreadsheetId, range, valueInputOption, insertDataOption, body):
        def execute():
            if self.append_error:
                raise self.append_error
            self.append_count += 1
            self.rows.extend(body["values"])
            return {}

        return Mock(execute=Mock(side_effect=execute))

    def batchUpdate(self, spreadsheetId, body):
        def execute():
            for request in body["requests"]:
                span = request["deleteDimension"]["range"]
                assert span["sheetId"] == self.SHEET_ID
                del self.rows[span["startIndex"] : span["endIndex"]]
            return {}

        return Mock(execute=Mock(side_effect=execute))

    def session_ids(self):
        """Session ID of every data row, in sheet order"""
        return [row[0] for row in self.rows[1:]]


class SheetsTestCase(unittest.TestCase):
    """Base: an uploader connected to an empty in-memory sheet"""

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.temp_folder = temp_dir.name
        self.upload_log_file = os.path.join(temp_dir.name, SHEETS_UPLOAD_LOG_FILE)
        self.sheet = FakeSheetsService()
        self.uploader = GoogleSheetsUploader(write_settings(temp_dir.name))
        self.uploader.service = self.sheet

        error_patch = patch("src.google_sheets_integration.messagebox.showerror")
        self.mock_error = error_patch.start()
        self.addCleanup(error_patch.stop)


class TestUploadReplacesRows(SheetsTestCase):
    """Uploading a session replaces its rows instead of adding duplicates"""

    def test_upload_adds_rows_for_each_session(self):
        """Test that each session gets its rows appended"""
        sessions = {"s1": make_session("2026-10-01"), "s2": make_session("2026-10-02")}

        self.assertTrue(self.uploader.upload_sessions(sessions))

        self.assertEqual(self.sheet.session_ids(), ["s1", "s1", "s2", "s2"])

    def test_reupload_replaces_rows_instead_of_duplicating(self):
        """Test that saving an edited session again replaces its rows"""
        self.uploader.upload_session(make_session("2026-10-01"), "s1")

        self.uploader.upload_session(make_session("2026-10-01", "edited"), "s1")

        self.assertEqual(self.sheet.session_ids(), ["s1", "s1"])
        self.assertIn("edited", self.sheet.rows[1])

    def test_reupload_keeps_other_sessions_rows(self):
        """Test that only the re-uploaded session's rows are removed"""
        self.sheet.rows += [["s1"], ["s2", "old"], ["s3"], ["s2", "old"], ["s3"]]

        self.uploader.upload_session(make_session("2026-10-02"), "s2")

        self.assertEqual(self.sheet.session_ids(), ["s1", "s3", "s3", "s2", "s2"])
        self.assertNotIn(["s2", "old"], self.sheet.rows)

    def test_existing_duplicates_are_cleaned_up(self):
        """Test that rows duplicated by the old append-only upload are removed"""
        self.uploader.upload_session(make_session("2026-10-01"), "s1")
        self.sheet.rows += [list(row) for row in self.sheet.rows[1:]]

        self.uploader.upload_session(make_session("2026-10-01"), "s1")

        self.assertEqual(self.sheet.session_ids(), ["s1", "s1"])

    def test_failed_upload_returns_false_and_shows_error(self):
        """Test that an upload failure is reported, not silently dropped"""
        self.sheet.append_error = OSError("No internet connection")

        result = self.uploader.upload_session(make_session("2026-10-01"), "s1")

        self.assertFalse(result)
        self.mock_error.assert_called_once()


class TestSyncSessions(SheetsTestCase):
    """sync_sessions uploads what is missing or changed and retries failures"""

    def setUp(self):
        super().setUp()
        self.all_data = {
            "s1": make_session("2026-10-01"),
            "s2": make_session("2026-10-02"),
        }

    def _sync(self, skip_session_ids=()):
        return self.uploader.sync_sessions(
            self.all_data, self.upload_log_file, set(skip_session_ids)
        )

    def test_uploads_sessions_never_uploaded(self):
        """Test that sessions not in the sheet yet are uploaded"""
        self.assertEqual(self._sync(), 2)

        self.assertEqual(self.sheet.session_ids(), ["s1", "s1", "s2", "s2"])

    def test_unchanged_sessions_are_not_uploaded_again(self):
        """Test that a second sync with no changes makes no upload"""
        self._sync()

        self.assertEqual(self._sync(), 0)

        self.assertEqual(self.sheet.append_count, 1)

    def test_changed_session_is_reuploaded_alone(self):
        """Test that only the edited session is uploaded again, replaced"""
        self._sync()
        self.all_data["s2"] = make_session("2026-10-02", "edited")

        self.assertEqual(self._sync(), 1)

        self.assertEqual(self.sheet.session_ids(), ["s1", "s1", "s2", "s2"])
        self.assertTrue(any("edited" in row for row in self.sheet.rows))

    def test_failed_sync_is_retried_next_time(self):
        """Test that sessions that failed to upload (offline) go up next sync"""
        self.sheet.append_error = OSError("No internet connection")
        self.assertIsNone(self._sync())

        self.sheet.append_error = None
        self.assertEqual(self._sync(), 2)

        self.assertEqual(self.sheet.session_ids(), ["s1", "s1", "s2", "s2"])

    def test_session_in_progress_is_not_uploaded_until_finished(self):
        """Test that the session still being tracked is skipped"""
        self._sync(skip_session_ids={"s2"})
        self.assertEqual(self.sheet.session_ids(), ["s1", "s1"])

        self.assertEqual(self._sync(), 1)

        self.assertEqual(self.sheet.session_ids(), ["s1", "s1", "s2", "s2"])

    def test_lost_upload_log_reuploads_without_duplicates(self):
        """Test that the upload log is only a cache: losing it is harmless"""
        self._sync()
        os.remove(self.upload_log_file)

        self._sync()

        self.assertEqual(self.sheet.session_ids(), ["s1", "s1", "s2", "s2"])

    def test_unfinished_session_is_not_uploaded(self):
        """Test that a session with no end (a stub or a crash) is left out"""
        unfinished = make_session("2026-10-03")
        del unfinished["end_timestamp"]
        self.all_data["s3"] = unfinished

        self._sync()

        self.assertEqual(self.sheet.session_ids(), ["s1", "s1", "s2", "s2"])

    def test_new_spreadsheet_or_tab_gets_every_session(self):
        """Test that changing the destination re-sends sessions already logged"""
        self._sync()
        new_tab_sheet = FakeSheetsService()
        uploader = GoogleSheetsUploader(
            write_settings(self.temp_folder, "NewTab", "new_tab_settings.json")
        )
        uploader.service = new_tab_sheet

        uploaded = uploader.sync_sessions(self.all_data, self.upload_log_file, set())

        self.assertEqual(uploaded, 2)
        self.assertEqual(new_tab_sheet.session_ids(), ["s1", "s1", "s2", "s2"])


class TestSignInNeverBlocksAutomaticSync(SheetsTestCase):
    """Automatic syncs never open the browser sign-in, which blocks the UI.

    The browser sign-in waits for Google's reply on the Tk thread; offline,
    or with the tab closed, the reply never comes and the app freezes.
    """

    def setUp(self):
        super().setUp()
        self.uploader.service = None  # not signed in yet
        self.token_file = os.path.join(self.temp_folder, "token.pickle")
        credentials_file = os.path.join(self.temp_folder, "credentials.json")
        open(credentials_file, "w").close()
        environment = patch.dict(
            os.environ,
            {
                "GOOGLE_SHEETS_TOKEN_FILE": self.token_file,
                "GOOGLE_SHEETS_CREDENTIALS_FILE": credentials_file,
            },
        )
        environment.start()
        self.addCleanup(environment.stop)
        flow_patch = patch("src.google_sheets_integration.InstalledAppFlow")
        self.mock_flow = flow_patch.start()
        self.addCleanup(flow_patch.stop)
        self.all_data = {"s1": make_session("2026-10-01")}

    def _sync(self):
        return self.uploader.sync_sessions(self.all_data, self.upload_log_file, set())

    def test_missing_login_leaves_sessions_due_without_browser(self):
        """Test that no saved login means 'sign in needed', not a browser"""
        self.assertIsNone(self._sync())

        self.mock_flow.from_client_secrets_file.assert_not_called()
        self.assertTrue(self.uploader.sign_in_needed)
        self.assertFalse(os.path.exists(self.upload_log_file))

    @patch("src.google_sheets_integration.pickle.load")
    def test_offline_refresh_waits_without_browser(self, mock_load):
        """Test that an offline token refresh retries later, no browser"""
        open(self.token_file, "wb").close()
        expired_login = Mock(valid=False, expired=True, refresh_token="refresh")
        expired_login.refresh.side_effect = TransportError("No internet connection")
        mock_load.return_value = expired_login

        self.assertIsNone(self._sync())

        self.mock_flow.from_client_secrets_file.assert_not_called()
        self.assertTrue(self.uploader.offline)
        self.assertFalse(self.uploader.sign_in_needed)

    @patch("src.google_sheets_integration.build")
    def test_test_connection_sign_in_has_a_time_limit(self, mock_build):
        """Test that the user-started sign-in gives up instead of waiting forever"""
        self.assertTrue(self.uploader.authenticate())

        sign_in = self.mock_flow.from_client_secrets_file.return_value
        sign_in.run_local_server.assert_called_once_with(
            port=0, timeout_seconds=GOOGLE_SIGN_IN_TIMEOUT_SECONDS
        )


class TestSyncTriggers(unittest.TestCase):
    """Save, Skip and app startup all trigger a sync"""

    def setUp(self):
        """Set up a tracker with one finished session"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        session_data = TestDataGenerator.create_session_data()
        self.session_name = list(session_data.keys())[0]
        self.test_data_file = self.file_manager.create_test_file(
            "test_sheets_sync_data.json", session_data
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_sheets_sync_settings.json", TestDataGenerator.create_settings_data()
        )
        self.tracker = TimeTracker(self.root)
        self.tracker.data_file = self.test_data_file
        self.tracker.settings_file = self.test_settings_file

    def tearDown(self):
        """Clean up after tests"""
        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def _open_completion_frame(self):
        frame = CompletionFrame(self.root, self.tracker, self.session_name)
        self.root.update()
        return frame

    def test_save_triggers_sync(self):
        """Test that Save & Complete syncs to Google Sheets"""
        frame = self._open_completion_frame()

        with patch.object(self.tracker, "sync_google_sheets") as mock_sync:
            frame.save_and_close()

        mock_sync.assert_called_once()

    def test_skip_triggers_sync(self):
        """Test that Skip also syncs, so skipped sessions are uploaded"""
        frame = self._open_completion_frame()

        with patch.object(self.tracker, "sync_google_sheets") as mock_sync:
            frame.skip_and_close()

        mock_sync.assert_called_once()

    def test_skip_uploads_session_end_to_end(self):
        """Test Skip -> tracker -> uploader -> sheet, with the upload log saved"""
        sheet = FakeSheetsService()
        self.tracker.settings_file = write_settings(self.file_manager.test_data_dir)
        self.file_manager.test_files.append(self.tracker.settings_file)
        upload_log_file = os.path.join(
            self.file_manager.test_data_dir, SHEETS_UPLOAD_LOG_FILE
        )
        self.file_manager.test_files.append(upload_log_file)

        def connect_to_fake_sheet(uploader, interactive=True):
            uploader.service = sheet
            return True

        frame = self._open_completion_frame()
        with patch(
            "src.google_sheets_integration.GoogleSheetsUploader.authenticate",
            connect_to_fake_sheet,
        ):
            frame.skip_and_close()

        self.assertIn(self.session_name, sheet.session_ids())
        with open(upload_log_file) as f:
            self.assertIn(self.session_name, json.load(f)["sessions"])

    @patch("src.google_sheets_integration.GoogleSheetsUploader.sync_sessions")
    def test_sync_sends_all_sessions_and_log_next_to_data(self, mock_sync_sessions):
        """Test that the tracker passes its sessions and upload log path"""
        self.tracker.sync_google_sheets()

        expected_log_file = os.path.join(
            self.file_manager.test_data_dir, SHEETS_UPLOAD_LOG_FILE
        )
        mock_sync_sessions.assert_called_once_with(
            self.tracker.load_data(), expected_log_file, set()
        )

    @patch("time_tracker.messagebox.showwarning")
    @patch(
        "src.google_sheets_integration.GoogleSheetsUploader.sync_sessions",
        side_effect=TypeError("bad duration in an old session"),
    )
    def test_sync_error_is_reported_not_raised(self, mock_sync_sessions, mock_warning):
        """Test that an upload error never escapes into Save or Skip"""
        self.tracker.sync_google_sheets()
        self.tracker.sync_google_sheets()

        mock_warning.assert_called_once()

    @patch("time_tracker.messagebox.showwarning")
    def test_sign_in_needed_is_reported_once_per_run(self, mock_warning):
        """Test that a needed sign-in is pointed out once, not on every Save"""

        def needs_sign_in(uploader, *args):
            uploader.sign_in_needed = True

        with patch.object(
            GoogleSheetsUploader, "sync_sessions", autospec=True, side_effect=needs_sign_in
        ):
            self.tracker.sync_google_sheets()
            self.tracker.sync_google_sheets()

        mock_warning.assert_called_once()
        self.assertIn("Test Connection", mock_warning.call_args[0][1])

    @patch("src.google_sheets_integration.GoogleSheetsUploader.sync_sessions")
    def test_sync_skips_session_being_tracked(self, mock_sync_sessions):
        """Test that an active session is excluded from the sync"""
        self.tracker.session_active = True
        self.tracker.session_name = self.session_name

        self.tracker.sync_google_sheets()

        skipped_session_ids = mock_sync_sessions.call_args[0][2]
        self.assertEqual(skipped_session_ids, {self.session_name})


class TestStartupSync(unittest.TestCase):
    """The app retries pending uploads shortly after it starts"""

    @patch("time_tracker._claim_single_instance", return_value=object())
    @patch("time_tracker.TimeTracker")
    @patch("time_tracker.tk.Tk")
    def test_main_schedules_sync_after_startup(
        self, mock_tk, mock_tracker_class, mock_claim
    ):
        """Test that main() schedules one sync after the window opens"""
        time_tracker.main()

        mock_tk.return_value.after.assert_called_once_with(
            GOOGLE_SHEETS_STARTUP_SYNC_DELAY_MS,
            mock_tracker_class.return_value.sync_google_sheets,
        )


if __name__ == "__main__":
    unittest.main()
