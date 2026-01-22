"""
Priority Tests for Analysis Frame

Tests for critical functionality: CSV export, midnight-spanning sessions,
secondary project aggregation, and card range customization.
"""

import unittest
import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime, timedelta
import sys
import os
import csv
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from analysis_frame import AnalysisFrame
from test_helpers import TestFileManager, TestDataGenerator


class TestAnalysisCSVExport(unittest.TestCase):
    """Test CSV export functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_csv_data.json"
        self.test_settings_file = "test_csv_settings.json"

        settings = {
            "idle_settings": {"idle_tracking_enabled": True, "idle_threshold": 60},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True}
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.file_manager.create_test_file(self.test_settings_file, settings)

    def test_csv_export_creates_file(self):
        """Test that CSV export creates a file with correct data"""
        today = datetime.now().strftime("%Y-%m-%d")
        test_data = {
            f"{today}_session1": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {
                        "duration": 1800,
                        "project": "Project A",
                        "start": "09:00:00",
                        "comment": "Morning work",
                    }
                ],
                "breaks": [
                    {
                        "duration": 600,
                        "action": "Resting",
                        "start": "09:30:00",
                        "comment": "Coffee",
                    }
                ],
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)

        csv_file = "test_export.csv"
        self.file_manager.test_files.append(csv_file)  # Track for cleanup

        # Mock the file dialog to return our test file
        with patch("tkinter.filedialog.asksaveasfilename", return_value=csv_file):
            with patch("tkinter.messagebox.showinfo") as mock_info:
                analysis.export_to_csv()

        # Verify file was created
        self.assertTrue(os.path.exists(csv_file))

        # Verify CSV contents
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 2)  # 1 active + 1 break

        # Check active period
        active_row = rows[0]
        self.assertEqual(active_row["Type"], "Active")
        self.assertEqual(active_row["Sphere"], "Work")
        self.assertEqual(active_row["Project/Action"], "Project A")
        self.assertEqual(active_row["Duration (seconds)"], "1800")
        self.assertEqual(active_row["Comment"], "Morning work")

        # Check break period
        break_row = rows[1]
        self.assertEqual(break_row["Type"], "Break")
        self.assertEqual(break_row["Project/Action"], "Resting")
        self.assertEqual(break_row["Duration (seconds)"], "600")

    def test_csv_export_respects_filters(self):
        """Test that CSV export respects sphere and project filters"""
        today = datetime.now().strftime("%Y-%m-%d")
        test_data = {
            f"{today}_session1": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {"duration": 1000, "project": "Project A", "start": "09:00:00"},
                    {"duration": 500, "project": "Project B", "start": "09:20:00"},
                ],
                "breaks": [],
                "idle_periods": [],
            }
        }

        # Add Project B to settings
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)
        settings["projects"]["Project B"] = {
            "sphere": "Work",
            "is_default": False,
            "active": True,
        }
        with open(self.test_settings_file, "w") as f:
            json.dump(settings, f, indent=2)

        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)
        analysis.sphere_var.set("Work")
        analysis.project_var.set("Project A")  # Filter to Project A only

        csv_file = "test_filtered.csv"
        self.file_manager.test_files.append(csv_file)  # Track for cleanup

        with patch("tkinter.filedialog.asksaveasfilename", return_value=csv_file):
            with patch("tkinter.messagebox.showinfo"):
                analysis.export_to_csv()

        # Verify only Project A was exported
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["Project/Action"], "Project A")

    def test_csv_export_no_data(self):
        """Test CSV export with no data shows info message"""
        self.file_manager.create_test_file(self.test_data_file, {})

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)

        with patch("tkinter.messagebox.showinfo") as mock_info:
            analysis.export_to_csv()

        mock_info.assert_called_once()
        self.assertIn("No data", mock_info.call_args[0][1])

    def test_csv_export_handles_write_error(self):
        """Test that CSV export handles write errors gracefully"""
        today = datetime.now().strftime("%Y-%m-%d")
        test_data = {
            f"{today}_session1": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {"duration": 1000, "project": "Project A", "start": "09:00:00"}
                ],
                "breaks": [],
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)

        # Mock file dialog to return invalid path
        with patch(
            "tkinter.filedialog.asksaveasfilename",
            return_value="/invalid/path/file.csv",
        ):
            with patch("tkinter.messagebox.showerror") as mock_error:
                analysis.export_to_csv()

        mock_error.assert_called_once()
        self.assertIn("Failed to export", mock_error.call_args[0][1])

    def content_frame(self):
        """Create a simple frame for testing"""
        return ttk.Frame(self.root)


class TestAnalysisSessionSpanningMidnight(unittest.TestCase):
    """Test sessions that span midnight"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_midnight_data.json"
        self.test_settings_file = "test_midnight_settings.json"

        settings = {
            "idle_settings": {"idle_tracking_enabled": False},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True}
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.file_manager.create_test_file(self.test_settings_file, settings)

    def test_session_assigned_to_start_date(self):
        """Test that sessions spanning midnight are assigned to start date"""
        # Session starts Jan 22 at 23:30, ends Jan 23 at 00:30
        start_date = "2026-01-22"
        end_date = "2026-01-23"

        test_data = {
            f"{start_date}_session1": {
                "sphere": "Work",
                "date": start_date,  # Should be assigned to start date
                "start_time": "23:30:00",
                "end_time": "00:30:00",  # Next day
                "total_duration": 3600,
                "active_duration": 3600,
                "break_duration": 0,
                "active": [{"duration": 3600, "project": "Project A"}],
                "breaks": [],
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)

        # Filter by start date should include the session
        analysis.sphere_var.set("All Spheres")
        analysis.project_var.set("All Projects")

        # Test "All Time" includes it
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 3600)

    def test_midnight_session_duration_calculation(self):
        """Test that duration calculation is correct for midnight-spanning sessions"""
        today = datetime.now()
        start_date = today.strftime("%Y-%m-%d")

        # 2-hour session crossing midnight
        test_data = {
            f"{start_date}_session1": {
                "sphere": "Work",
                "date": start_date,
                "start_time": "23:00:00",
                "end_time": "01:00:00",  # Next day
                "total_duration": 7200,  # 2 hours
                "active_duration": 6000,
                "break_duration": 1200,
                "active": [
                    {"duration": 3000, "project": "Project A"},
                    {"duration": 3000, "project": "Project A"},
                ],
                "breaks": [{"duration": 1200, "action": "Resting"}],
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)
        analysis.sphere_var.set("All Spheres")
        analysis.project_var.set("All Projects")

        active, breaks = analysis.calculate_totals("All Time")

        # Should count full durations
        self.assertEqual(active, 6000)
        self.assertEqual(breaks, 1200)

    def content_frame(self):
        """Create a simple frame for testing"""
        return ttk.Frame(self.root)


class TestAnalysisMultipleSecondaryProjects(unittest.TestCase):
    """Test aggregation of sessions with multiple secondary projects"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_secondary_data.json"
        self.test_settings_file = "test_secondary_settings.json"

        settings = {
            "idle_settings": {"idle_tracking_enabled": False},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True},
                "Project B": {"sphere": "Work", "is_default": False, "active": True},
                "Project C": {"sphere": "Work", "is_default": False, "active": True},
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.file_manager.create_test_file(self.test_settings_file, settings)

    def test_secondary_projects_aggregated_correctly(self):
        """Test that periods with secondary projects are aggregated correctly"""
        today = datetime.now().strftime("%Y-%m-%d")

        # Period with 60/40 split between Project A and Project B
        # Note: Analysis frame currently counts full duration when filtering by project in projects array
        test_data = {
            f"{today}_session1": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {
                        "duration": 1000,
                        "project": "Project A",  # Also include single project field for compatibility
                        "projects": [
                            {
                                "name": "Project A",
                                "percentage": 60,
                                "duration": 600,
                                "project_primary": True,
                            },
                            {
                                "name": "Project B",
                                "percentage": 40,
                                "duration": 400,
                                "project_primary": False,
                            },
                        ],
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)
        analysis.sphere_var.set("All Spheres")

        # Note: Current implementation counts full period duration if project is found in projects array
        # This test documents current behavior
        analysis.project_var.set("Project A")
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 1000)  # Gets full duration

        analysis.project_var.set("Project B")
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 1000)  # Gets full duration

        # All Projects should get 1000 seconds total
        analysis.project_var.set("All Projects")
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 1000)

    def test_multiple_periods_with_different_splits(self):
        """Test multiple periods with different secondary project splits"""
        today = datetime.now().strftime("%Y-%m-%d")

        # Note: Current implementation counts full period duration when project is in projects array
        test_data = {
            f"{today}_session1": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {
                        "duration": 2000,
                        "project": "Project A",
                        "projects": [
                            {
                                "name": "Project A",
                                "percentage": 70,
                                "duration": 1400,
                                "project_primary": True,
                            },
                            {
                                "name": "Project B",
                                "percentage": 30,
                                "duration": 600,
                                "project_primary": False,
                            },
                        ],
                    },
                    {
                        "duration": 1000,
                        "project": "Project B",
                        "projects": [
                            {
                                "name": "Project B",
                                "percentage": 50,
                                "duration": 500,
                                "project_primary": True,
                            },
                            {
                                "name": "Project C",
                                "percentage": 50,
                                "duration": 500,
                                "project_primary": False,
                            },
                        ],
                    },
                ],
                "breaks": [],
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)
        analysis.sphere_var.set("All Spheres")

        # Current behavior: counts full duration of periods where project is found
        analysis.project_var.set("Project A")
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 2000)  # Full duration of first period

        # Project B: in both periods
        analysis.project_var.set("Project B")
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 3000)  # Both periods (2000 + 1000)

        # Project C: in second period
        analysis.project_var.set("Project C")
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 1000)  # Full duration of second period

    def content_frame(self):
        """Create a simple frame for testing"""
        return ttk.Frame(self.root)


class TestAnalysisCardRangeCustomization(unittest.TestCase):
    """Test card range customization and persistence"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_card_data.json"
        self.test_settings_file = "test_card_settings.json"

        # Settings without analysis_settings initially
        settings = {
            "idle_settings": {"idle_tracking_enabled": False},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True}
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.file_manager.create_test_file(self.test_settings_file, settings)
        self.file_manager.create_test_file(self.test_data_file, {})

    def test_default_card_ranges(self):
        """Test that default card ranges are loaded correctly"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)

        # Should have default ranges
        self.assertEqual(len(analysis.card_ranges), 3)
        self.assertIn("Last 7 Days", analysis.card_ranges)
        self.assertIn("Last 30 Days", analysis.card_ranges)
        self.assertIn("All Time", analysis.card_ranges)

    def test_card_ranges_persist_to_settings(self):
        """Test that card range changes are saved to settings file"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)

        # Modify card ranges
        analysis.card_ranges = ["Last 14 Days", "This Month", "All Time"]
        analysis.save_card_ranges()

        # Read settings file and verify
        with open(self.test_settings_file, "r") as f:
            saved_settings = json.load(f)

        self.assertIn("analysis_settings", saved_settings)
        self.assertEqual(
            saved_settings["analysis_settings"]["card_ranges"],
            ["Last 14 Days", "This Month", "All Time"],
        )

    def test_custom_card_ranges_loaded_on_init(self):
        """Test that custom saved card ranges are loaded on initialization"""
        # Save custom card ranges to settings first
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)
        settings["analysis_settings"] = {
            "card_ranges": ["This Week (Mon-Sun)", "This Month", "Last Month"]
        }
        with open(self.test_settings_file, "w") as f:
            json.dump(settings, f, indent=2)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)

        # Should load custom ranges
        self.assertEqual(
            analysis.card_ranges, ["This Week (Mon-Sun)", "This Month", "Last Month"]
        )

    def test_save_card_ranges_error_handling(self):
        """Test that save_card_ranges handles write errors gracefully"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)
        analysis.card_ranges = ["Last 7 Days", "Last 14 Days", "All Time"]

        # Mock the file write to raise an error
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            with patch("tkinter.messagebox.showerror") as mock_error:
                analysis.save_card_ranges()

            mock_error.assert_called_once()
            self.assertIn("Failed to save settings", mock_error.call_args[0][1])

    def content_frame(self):
        """Create a simple frame for testing"""
        return ttk.Frame(self.root)


if __name__ == "__main__":
    unittest.main()
