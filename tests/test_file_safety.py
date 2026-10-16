"""
Tests for Crash-Safe File Helpers

Verifies src/file_safety.py: atomic JSON writes, preserving a data file that
cannot be read, and the rotating daily backup of data.json. Regression tests
for the May 27 crash that left data.json as 243 KB of null bytes.
Pure file-system tests, no Tkinter required.
"""

import glob
import json
import os
import re
import sys
import tempfile
import unittest
from datetime import date
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.file_safety import (
    create_daily_backup,
    preserve_unreadable_file,
    write_json_atomically,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RETENTION_COUNT = 14


class TestFileSafetyImport(unittest.TestCase):
    """Import smoke test"""

    def test_import(self):
        """Test that the file_safety module loads"""
        from src import file_safety

        self.assertIsNotNone(file_safety)


class TestWriteJsonAtomically(unittest.TestCase):
    """A failed write must never leave a truncated or half-written file"""

    def setUp(self):
        """Create a temp folder holding a valid data file"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.file_path = os.path.join(self.temp_dir.name, "data.json")

        original_data = {"session_1": {"date": "2026-05-26", "total_duration": 3600}}
        with open(self.file_path, "w") as f:
            json.dump(original_data, f, indent=2)
        with open(self.file_path, "rb") as f:
            self.original_bytes = f.read()

    def _read_bytes(self):
        with open(self.file_path, "rb") as f:
            return f.read()

    def test_new_data_is_written_and_readable(self):
        """Test that the new data replaces the old data"""
        new_data = {"session_2": {"date": "2026-10-08"}}

        write_json_atomically(self.file_path, new_data)

        with open(self.file_path) as f:
            self.assertEqual(json.load(f), new_data)

    def test_creates_file_that_does_not_exist_yet(self):
        """Test that a missing file is created"""
        new_path = os.path.join(self.temp_dir.name, "settings.json")

        write_json_atomically(new_path, {"spheres": {}})

        with open(new_path) as f:
            self.assertEqual(json.load(f), {"spheres": {}})

    def test_disk_full_mid_write_leaves_existing_file_intact(self):
        """Test that a write dying partway keeps the previous file byte-for-byte"""
        disk_full = OSError(28, "No space left on device")

        with patch("json.dump", side_effect=disk_full):
            with self.assertRaises(OSError):
                write_json_atomically(self.file_path, {"session_2": {}})

        self.assertEqual(self._read_bytes(), self.original_bytes)

    def test_unserializable_data_leaves_existing_file_intact(self):
        """Test that json.dump failing after partial output keeps the old file"""
        with self.assertRaises(TypeError):
            write_json_atomically(self.file_path, {"a": 1, "b": object()})

        self.assertEqual(self._read_bytes(), self.original_bytes)

    def test_failed_write_leaves_no_temp_files(self):
        """Test that the temp file is removed when the write fails"""
        with self.assertRaises(TypeError):
            write_json_atomically(self.file_path, {"b": object()})

        self.assertEqual(os.listdir(self.temp_dir.name), ["data.json"])


class TestPreserveUnreadableFile(unittest.TestCase):
    """An unreadable data file is copied aside before anything replaces it"""

    def setUp(self):
        """Create a zeroed data file like the one left by the May 27 crash"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.file_path = os.path.join(self.temp_dir.name, "data.json")
        self.zeroed_bytes = b"\x00" * 1024
        with open(self.file_path, "wb") as f:
            f.write(self.zeroed_bytes)

    def test_copy_has_identical_bytes(self):
        """Test that the preserved copy is an exact copy"""
        preserved_path = preserve_unreadable_file(self.file_path)

        with open(preserved_path, "rb") as f:
            self.assertEqual(f.read(), self.zeroed_bytes)

    def test_copy_is_timestamped_next_to_original(self):
        """Test that the copy sits beside the original with a timestamped name"""
        preserved_path = preserve_unreadable_file(self.file_path)

        self.assertEqual(
            os.path.dirname(os.path.abspath(preserved_path)), self.temp_dir.name
        )
        self.assertRegex(
            os.path.basename(preserved_path), r"^data\.json\.unreadable_\d{8}_\d{6}$"
        )


class TestCreateDailyBackup(unittest.TestCase):
    """One backup per day, written from data just saved, pruned to a window"""

    def setUp(self):
        """Create a temp folder for the data file and its backups"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.data_file = os.path.join(self.temp_dir.name, "data.json")
        self.backup_folder = os.path.join(self.temp_dir.name, "backups")
        self.today = date(2026, 10, 8)

    def _backup(self, data, day):
        return create_daily_backup(
            self.data_file, data, self.backup_folder, RETENTION_COUNT, today=day
        )

    def _daily_backups(self):
        return sorted(
            name
            for name in os.listdir(self.backup_folder)
            if name.startswith("data.json.daily_")
        )

    def test_first_save_of_day_writes_backup_of_saved_data(self):
        """Test that the first save of the day writes a dated backup"""
        backup_path = self._backup({"session_1": {}}, self.today)

        self.assertEqual(os.path.basename(backup_path), "data.json.daily_20261008")
        with open(backup_path) as f:
            self.assertEqual(json.load(f), {"session_1": {}})

    def test_later_save_same_day_keeps_first_backup(self):
        """Test that later saves the same day do not overwrite the backup"""
        self._backup({"session_1": {}}, self.today)

        result = self._backup({"bad_data": {}}, self.today)

        self.assertIsNone(result)
        backup_path = os.path.join(self.backup_folder, "data.json.daily_20261008")
        with open(backup_path) as f:
            self.assertEqual(json.load(f), {"session_1": {}})

    def test_next_day_writes_new_backup(self):
        """Test that a new day gets its own backup"""
        self._backup({"session_1": {}}, date(2026, 10, 8))
        self._backup({"session_2": {}}, date(2026, 10, 9))

        self.assertEqual(
            self._daily_backups(),
            ["data.json.daily_20261008", "data.json.daily_20261009"],
        )

    def test_keeps_only_newest_retention_count(self):
        """Test that the oldest daily backups are pruned"""
        for day in range(1, RETENTION_COUNT + 3):
            self._backup({"day": day}, date(2026, 9, day))

        backups = self._daily_backups()
        self.assertEqual(len(backups), RETENTION_COUNT)
        self.assertEqual(backups[0], "data.json.daily_20260903")
        self.assertEqual(backups[-1], "data.json.daily_20260916")

    def test_pruning_never_touches_other_backups(self):
        """Test that pre-deletion backups and other files' backups survive"""
        os.makedirs(self.backup_folder)
        other_files = ["data.json.backup_20260526_180133", "other.json.daily_20200101"]
        for name in other_files:
            open(os.path.join(self.backup_folder, name), "w").close()

        for day in range(1, RETENTION_COUNT + 3):
            self._backup({"day": day}, date(2026, 9, day))

        for name in other_files:
            self.assertTrue(os.path.exists(os.path.join(self.backup_folder, name)))


class TestNoNonAtomicJsonWrites(unittest.TestCase):
    """Every rewrite of data.json / settings.json goes through write_json_atomically.

    open(path, "w") empties the file before writing, so a crash or full disk
    mid-write loses the whole file. That is how data.json was zeroed on May 27.
    """

    def test_no_direct_writes_to_data_or_settings_file(self):
        """Test that no source file opens the data or settings file with 'w'"""
        direct_write = re.compile(
            r"open\(\s*[\w.]*(?:data_file|settings_file)\s*,\s*[\"']w[\"']"
        )
        source_files = [os.path.join(PROJECT_ROOT, "time_tracker.py")] + glob.glob(
            os.path.join(PROJECT_ROOT, "src", "*.py")
        )

        for source_file in source_files:
            with open(source_file, encoding="utf-8") as f:
                match = direct_write.search(f.read())
            self.assertIsNone(
                match,
                f"{os.path.basename(source_file)} rewrites a JSON file in place: "
                f"{match.group(0) if match else ''}",
            )


if __name__ == "__main__":
    unittest.main()
