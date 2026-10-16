"""
Tests for App Startup Safeguards

Verifies how the app starts: the built exe always uses its own folder for
data (whatever the shortcut's "Start in" says), only one copy can run at a
time, and global keyboard shortcuts are opt-in because they fire in every
program (Ctrl+Shift+E opens the Explorer in VS Code but ended the session).
"""

import os
import sys
import tkinter as tk
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time_tracker
from time_tracker import TimeTracker
from test_helpers import safe_teardown_tk_root


class TestAppFolder(unittest.TestCase):
    """The built exe reads and writes its data next to itself"""

    @patch("time_tracker.os.chdir")
    def test_built_exe_runs_from_its_own_folder(self, mock_chdir):
        """Test that a frozen (PyInstaller) app switches to the exe's folder"""
        exe_path = os.path.join("C:\\", "Apps", "TimeAligned", "TimeAligned.exe")
        with patch.object(time_tracker.sys, "frozen", True, create=True):
            with patch.object(time_tracker.sys, "executable", exe_path):
                time_tracker._use_app_folder()

        mock_chdir.assert_called_once_with(os.path.dirname(exe_path))

    @patch("time_tracker.os.chdir")
    def test_source_run_keeps_working_directory(self, mock_chdir):
        """Test that running from source (python time_tracker.py) is unchanged"""
        time_tracker._use_app_folder()

        mock_chdir.assert_not_called()


class TestSingleInstance(unittest.TestCase):
    """A second copy of the app must not start"""

    def test_second_copy_is_refused(self):
        """Test that the single-instance lock can only be held once"""
        test_lock_name = f"Local\\TimeAlignedTest_{os.getpid()}"
        with patch.object(time_tracker, "SINGLE_INSTANCE_MUTEX_NAME", test_lock_name):
            first = time_tracker._claim_single_instance()
            second = time_tracker._claim_single_instance()

        self.assertIsNotNone(first)
        self.assertIsNone(second)

    @patch("time_tracker.messagebox.showinfo")
    @patch("time_tracker.TimeTracker")
    @patch("time_tracker.tk.Tk")
    @patch("time_tracker._claim_single_instance", return_value=None)
    def test_main_exits_when_already_running(
        self, mock_claim, mock_tk, mock_tracker_class, mock_info
    ):
        """Test that main() tells the user and starts no tracker"""
        time_tracker.main()

        mock_tracker_class.assert_not_called()
        mock_info.assert_called_once()
        mock_tk.return_value.mainloop.assert_not_called()


class TestGlobalShortcutsSetting(unittest.TestCase):
    """Global keyboard shortcuts run only when turned on in Settings"""

    def setUp(self):
        """Set up a tracker"""
        self.root = tk.Tk()
        self.tracker = TimeTracker(self.root)
        self.tracker.stop_global_hotkeys()

    def tearDown(self):
        """Clean up after tests"""
        self.tracker.stop_global_hotkeys()
        safe_teardown_tk_root(self.root)

    @patch("time_tracker.keyboard.GlobalHotKeys")
    def test_shortcuts_are_off_unless_enabled(self, mock_hotkeys):
        """Test that settings without the option register no shortcuts"""
        self.tracker.settings.pop("keyboard_shortcuts", None)

        self.tracker.apply_hotkey_setting()

        mock_hotkeys.assert_not_called()
        self.assertIsNone(self.tracker.hotkey_listener)

    @patch("time_tracker.keyboard.GlobalHotKeys")
    def test_enabling_starts_and_disabling_stops_shortcuts(self, mock_hotkeys):
        """Test that the setting starts and stops the shortcut listener"""
        self.tracker.settings["keyboard_shortcuts"] = {"enabled": True}
        self.tracker.apply_hotkey_setting()
        mock_hotkeys.return_value.start.assert_called_once()

        self.tracker.settings["keyboard_shortcuts"] = {"enabled": False}
        self.tracker.apply_hotkey_setting()

        mock_hotkeys.return_value.stop.assert_called_once()
        self.assertIsNone(self.tracker.hotkey_listener)

    def test_new_settings_file_has_shortcuts_off(self):
        """Test that a freshly created settings.json turns shortcuts off"""
        missing_settings = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "test_data", "no_such.json"
        )
        self.tracker.settings_file = missing_settings
        self.addCleanup(
            lambda: os.path.exists(missing_settings) and os.remove(missing_settings)
        )

        settings = self.tracker.get_settings()

        self.assertFalse(settings["keyboard_shortcuts"]["enabled"])


if __name__ == "__main__":
    unittest.main()
