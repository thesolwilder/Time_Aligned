"""
TDD Tests: CSV Export Percentage and Duration Columns

Tests that export_to_csv() in AnalysisFrame includes:
- Primary Percentage  (100 for single project; split % for multi-project)
- Primary Duration    (full period duration for single; split duration for multi)
- Secondary Percentage (empty for single; secondary's % for multi)
- Secondary Duration   (empty for single; secondary's duration for multi)

Same logic applies to break and idle periods (actions array).

Test progression: Import → Unit → Integration
"""

import unittest
import tkinter as tk
from tkinter import ttk
import json
import csv
import os
import sys
import tempfile
from unittest.mock import patch
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from src.analysis_frame import AnalysisFrame
from tests.test_helpers import TestFileManager, safe_teardown_tk_root


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_settings():
    return {
        "idle_settings": {"idle_tracking_enabled": False, "idle_threshold": 60},
        "spheres": {"Work": {"is_default": True, "active": True}},
        "projects": {
            "ProjectA": {"sphere": "Work", "is_default": True, "active": True},
            "ProjectB": {"sphere": "Work", "is_default": False, "active": True},
        },
        "break_actions": {
            "Resting": {"is_default": True, "active": True},
            "Reading": {"is_default": False, "active": True},
        },
        "analysis_settings": {
            "card_ranges": ["Last 7 Days", "Last 14 Days", "All Time"]
        },
    }


def _today():
    return datetime.now().strftime("%Y-%m-%d")


def _make_analysis_frame(root, tracker):
    content = ttk.Frame(root)
    analysis = AnalysisFrame(content, tracker, root)
    analysis.sphere_var.set("All Spheres")
    analysis.project_var.set("All Projects")
    analysis.selected_card = 2  # "All Time"
    return analysis


def _run_export_and_read(analysis, csv_path):
    """Run export_to_csv and return rows as list of dicts."""
    with patch("tkinter.filedialog.asksaveasfilename", return_value=csv_path):
        with patch("tkinter.messagebox.showinfo"):
            analysis.export_to_csv()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


# ---------------------------------------------------------------------------
# 1. Import smoke test
# ---------------------------------------------------------------------------


class TestImport(unittest.TestCase):
    def test_import(self):
        from src import analysis_frame

        self.assertIsNotNone(analysis_frame)


# ---------------------------------------------------------------------------
# 2. Unit tests — fieldnames contain the four new columns
# ---------------------------------------------------------------------------


class TestCSVFieldnames(unittest.TestCase):
    """Verify the CSV export writes the four new column headers."""

    def setUp(self):
        self.root = tk.Tk()
        self.file_manager = TestFileManager()

        today = _today()
        data = {
            f"{today}_1000000000": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {
                        "start": "09:00:00",
                        "start_timestamp": 1000000000.0,
                        "end": "09:30:00",
                        "end_timestamp": 1000001800.0,
                        "duration": 1800,
                        "project": "ProjectA",
                        "comment": "morning work",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
                "session_comments": {
                    "active_notes": "",
                    "break_notes": "",
                    "idle_notes": "",
                    "session_notes": "",
                },
            }
        }
        settings = _make_settings()
        self.data_file = self.file_manager.create_test_file(
            "pct_fieldnames_data.json", data
        )
        self.settings_file = self.file_manager.create_test_file(
            "pct_fieldnames_settings.json", settings
        )

    def tearDown(self):
        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def _export_headers(self):
        tracker = TimeTracker(self.root)
        tracker.data_file = self.data_file
        tracker.settings_file = self.settings_file
        tracker.settings = tracker.get_settings()
        analysis = _make_analysis_frame(self.root, tracker)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            csv_path = f.name

        try:
            with patch("tkinter.filedialog.asksaveasfilename", return_value=csv_path):
                with patch("tkinter.messagebox.showinfo"):
                    analysis.export_to_csv()
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                return next(reader)  # first row = headers
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_primary_percentage_column_in_headers(self):
        self.assertIn("Primary Percentage", self._export_headers())

    def test_primary_duration_column_in_headers(self):
        self.assertIn("Primary Duration", self._export_headers())

    def test_secondary_percentage_column_in_headers(self):
        self.assertIn("Secondary Percentage", self._export_headers())

    def test_secondary_duration_column_in_headers(self):
        self.assertIn("Secondary Duration", self._export_headers())


# ---------------------------------------------------------------------------
# 3. Integration tests — single project active period
# ---------------------------------------------------------------------------


class TestSingleProjectActivePercentage(unittest.TestCase):
    """Single-project active period: 100% primary, empty secondary."""

    def setUp(self):
        self.root = tk.Tk()
        self.file_manager = TestFileManager()

        today = _today()
        # Period is 1800 seconds (30 minutes)
        self.period_duration = 1800
        data = {
            f"{today}_1000000000": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {
                        "start": "09:00:00",
                        "start_timestamp": 1000000000.0,
                        "end": "09:30:00",
                        "end_timestamp": 1000001800.0,
                        "duration": self.period_duration,
                        "project": "ProjectA",
                        "comment": "single project work",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
                "session_comments": {
                    "active_notes": "",
                    "break_notes": "",
                    "idle_notes": "",
                    "session_notes": "",
                },
            }
        }
        settings = _make_settings()
        self.data_file = self.file_manager.create_test_file(
            "single_proj_data.json", data
        )
        self.settings_file = self.file_manager.create_test_file(
            "single_proj_settings.json", settings
        )

    def tearDown(self):
        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def _export_rows(self):
        tracker = TimeTracker(self.root)
        tracker.data_file = self.data_file
        tracker.settings_file = self.settings_file
        tracker.settings = tracker.get_settings()
        analysis = _make_analysis_frame(self.root, tracker)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            csv_path = f.name

        try:
            return _run_export_and_read(analysis, csv_path)
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_single_project_primary_percentage_is_100(self):
        rows = self._export_rows()
        active_row = next(r for r in rows if r["Type"] == "Active")
        self.assertEqual(active_row["Primary Percentage"], "100")

    def test_single_project_primary_duration_equals_period_duration(self):
        """Primary Duration should match the period's total Duration column."""
        rows = self._export_rows()
        active_row = next(r for r in rows if r["Type"] == "Active")
        # Both Duration and Primary Duration represent the full period
        self.assertEqual(active_row["Primary Duration"], active_row["Duration"])

    def test_single_project_secondary_percentage_is_empty(self):
        rows = self._export_rows()
        active_row = next(r for r in rows if r["Type"] == "Active")
        self.assertEqual(active_row["Secondary Percentage"], "")

    def test_single_project_secondary_duration_is_empty(self):
        rows = self._export_rows()
        active_row = next(r for r in rows if r["Type"] == "Active")
        self.assertEqual(active_row["Secondary Duration"], "")


# ---------------------------------------------------------------------------
# 4. Integration tests — multi-project active period
# ---------------------------------------------------------------------------


class TestMultiProjectActivePercentage(unittest.TestCase):
    """Multi-project active period: stored percentage split and durations."""

    def setUp(self):
        self.root = tk.Tk()
        self.file_manager = TestFileManager()

        today = _today()
        # Period is 1000 seconds; 70% primary = 700s, 30% secondary = 300s
        total_duration = 1000
        primary_pct = 70
        secondary_pct = 30
        self.primary_duration_s = int(total_duration * primary_pct / 100)  # 700
        self.secondary_duration_s = int(total_duration * secondary_pct / 100)  # 300
        self.primary_pct = primary_pct
        self.secondary_pct = secondary_pct

        data = {
            f"{today}_1000000000": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {
                        "start": "09:00:00",
                        "start_timestamp": 1000000000.0,
                        "end": "09:16:40",
                        "end_timestamp": 1000001000.0,
                        "duration": total_duration,
                        # multi-project format (no "project" key)
                        "projects": [
                            {
                                "name": "ProjectA",
                                "percentage": primary_pct,
                                "duration": self.primary_duration_s,
                                "comment": "primary comment",
                                "project_primary": True,
                            },
                            {
                                "name": "ProjectB",
                                "percentage": secondary_pct,
                                "duration": self.secondary_duration_s,
                                "comment": "secondary comment",
                                "project_primary": False,
                            },
                        ],
                    }
                ],
                "breaks": [],
                "idle_periods": [],
                "session_comments": {
                    "active_notes": "",
                    "break_notes": "",
                    "idle_notes": "",
                    "session_notes": "",
                },
            }
        }
        settings = _make_settings()
        self.data_file = self.file_manager.create_test_file(
            "multi_proj_data.json", data
        )
        self.settings_file = self.file_manager.create_test_file(
            "multi_proj_settings.json", settings
        )

    def tearDown(self):
        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def _export_rows(self):
        tracker = TimeTracker(self.root)
        tracker.data_file = self.data_file
        tracker.settings_file = self.settings_file
        tracker.settings = tracker.get_settings()
        analysis = _make_analysis_frame(self.root, tracker)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            csv_path = f.name

        try:
            return _run_export_and_read(analysis, csv_path)
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_multi_project_primary_percentage(self):
        rows = self._export_rows()
        active_row = next(r for r in rows if r["Type"] == "Active")
        self.assertEqual(active_row["Primary Percentage"], str(self.primary_pct))

    def test_multi_project_secondary_percentage(self):
        rows = self._export_rows()
        active_row = next(r for r in rows if r["Type"] == "Active")
        self.assertEqual(active_row["Secondary Percentage"], str(self.secondary_pct))

    def test_multi_project_primary_duration_not_empty(self):
        rows = self._export_rows()
        active_row = next(r for r in rows if r["Type"] == "Active")
        self.assertNotEqual(active_row["Primary Duration"], "")

    def test_multi_project_secondary_duration_not_empty(self):
        rows = self._export_rows()
        active_row = next(r for r in rows if r["Type"] == "Active")
        self.assertNotEqual(active_row["Secondary Duration"], "")

    def test_multi_project_primary_duration_less_than_total(self):
        """Primary duration (70%) must be less than full period duration."""
        rows = self._export_rows()
        active_row = next(r for r in rows if r["Type"] == "Active")
        # Primary Duration should not equal full Duration (it's only 70%)
        self.assertNotEqual(active_row["Primary Duration"], active_row["Duration"])


# ---------------------------------------------------------------------------
# 5. Integration tests — single-action break period
# ---------------------------------------------------------------------------


class TestSingleActionBreakPercentage(unittest.TestCase):
    """Single break action: 100% primary, empty secondary."""

    def setUp(self):
        self.root = tk.Tk()
        self.file_manager = TestFileManager()

        today = _today()
        data = {
            f"{today}_1000000000": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {
                        "start": "09:00:00",
                        "start_timestamp": 1000000000.0,
                        "end": "09:30:00",
                        "end_timestamp": 1000001800.0,
                        "duration": 1800,
                        "project": "ProjectA",
                        "comment": "",
                    }
                ],
                "breaks": [
                    {
                        "start": "09:30:00",
                        "start_timestamp": 1000001800.0,
                        "end": "09:35:00",
                        "end_timestamp": 1000002100.0,
                        "duration": 300,
                        "action": "Resting",
                        "comment": "",
                    }
                ],
                "idle_periods": [],
                "session_comments": {
                    "active_notes": "",
                    "break_notes": "",
                    "idle_notes": "",
                    "session_notes": "",
                },
            }
        }
        settings = _make_settings()
        self.data_file = self.file_manager.create_test_file(
            "single_break_data.json", data
        )
        self.settings_file = self.file_manager.create_test_file(
            "single_break_settings.json", settings
        )

    def tearDown(self):
        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def _export_rows(self):
        tracker = TimeTracker(self.root)
        tracker.data_file = self.data_file
        tracker.settings_file = self.settings_file
        tracker.settings = tracker.get_settings()
        analysis = _make_analysis_frame(self.root, tracker)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            csv_path = f.name

        try:
            return _run_export_and_read(analysis, csv_path)
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_single_break_primary_percentage_is_100(self):
        rows = self._export_rows()
        break_row = next(r for r in rows if r["Type"] == "Break")
        self.assertEqual(break_row["Primary Percentage"], "100")

    def test_single_break_primary_duration_equals_period_duration(self):
        rows = self._export_rows()
        break_row = next(r for r in rows if r["Type"] == "Break")
        self.assertEqual(break_row["Primary Duration"], break_row["Duration"])

    def test_single_break_secondary_percentage_is_empty(self):
        rows = self._export_rows()
        break_row = next(r for r in rows if r["Type"] == "Break")
        self.assertEqual(break_row["Secondary Percentage"], "")

    def test_single_break_secondary_duration_is_empty(self):
        rows = self._export_rows()
        break_row = next(r for r in rows if r["Type"] == "Break")
        self.assertEqual(break_row["Secondary Duration"], "")


# ---------------------------------------------------------------------------
# 6. Integration tests — multi-action break period
# ---------------------------------------------------------------------------


class TestMultiActionBreakPercentage(unittest.TestCase):
    """Multi-action break: stored percentage split and durations."""

    def setUp(self):
        self.root = tk.Tk()
        self.file_manager = TestFileManager()

        today = _today()
        total_duration = 600  # 10 minutes
        primary_pct = 60
        secondary_pct = 40
        self.primary_pct = primary_pct
        self.secondary_pct = secondary_pct

        data = {
            f"{today}_1000000000": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {
                        "start": "09:00:00",
                        "start_timestamp": 1000000000.0,
                        "end": "09:30:00",
                        "end_timestamp": 1000001800.0,
                        "duration": 1800,
                        "project": "ProjectA",
                        "comment": "",
                    }
                ],
                "breaks": [
                    {
                        "start": "09:30:00",
                        "start_timestamp": 1000001800.0,
                        "end": "09:40:00",
                        "end_timestamp": 1000002400.0,
                        "duration": total_duration,
                        # multi-action format (no "action" key)
                        "actions": [
                            {
                                "name": "Resting",
                                "percentage": primary_pct,
                                "duration": int(total_duration * primary_pct / 100),
                                "comment": "main break",
                                "break_primary": True,
                            },
                            {
                                "name": "Reading",
                                "percentage": secondary_pct,
                                "duration": int(total_duration * secondary_pct / 100),
                                "comment": "reading too",
                                "break_primary": False,
                            },
                        ],
                    }
                ],
                "idle_periods": [],
                "session_comments": {
                    "active_notes": "",
                    "break_notes": "",
                    "idle_notes": "",
                    "session_notes": "",
                },
            }
        }
        settings = _make_settings()
        self.data_file = self.file_manager.create_test_file(
            "multi_break_data.json", data
        )
        self.settings_file = self.file_manager.create_test_file(
            "multi_break_settings.json", settings
        )

    def tearDown(self):
        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def _export_rows(self):
        tracker = TimeTracker(self.root)
        tracker.data_file = self.data_file
        tracker.settings_file = self.settings_file
        tracker.settings = tracker.get_settings()
        analysis = _make_analysis_frame(self.root, tracker)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            csv_path = f.name

        try:
            return _run_export_and_read(analysis, csv_path)
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_multi_break_primary_percentage(self):
        rows = self._export_rows()
        break_row = next(r for r in rows if r["Type"] == "Break")
        self.assertEqual(break_row["Primary Percentage"], str(self.primary_pct))

    def test_multi_break_secondary_percentage(self):
        rows = self._export_rows()
        break_row = next(r for r in rows if r["Type"] == "Break")
        self.assertEqual(break_row["Secondary Percentage"], str(self.secondary_pct))

    def test_multi_break_secondary_duration_not_empty(self):
        rows = self._export_rows()
        break_row = next(r for r in rows if r["Type"] == "Break")
        self.assertNotEqual(break_row["Secondary Duration"], "")


if __name__ == "__main__":
    unittest.main()
