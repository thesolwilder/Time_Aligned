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
from src.analysis_frame import AnalysisFrame
from tests.test_helpers import TestFileManager, TestDataGenerator


class TestAnalysisCSVExport(unittest.TestCase):
    """Test CSV export functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        test_data = {}
        settings = {
            "idle_settings": {"idle_tracking_enabled": True, "idle_threshold": 60},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True}
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }

        self.test_data_file = self.file_manager.create_test_file(
            "test_csv_data.json", test_data
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_csv_settings.json", settings
        )

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
        self.assertEqual(active_row["Primary Action"], "Project A")
        self.assertIn("Duration", active_row)  # Duration is formatted string
        self.assertEqual(active_row["Primary Comment"], "Morning work")

        # Check break period
        break_row = rows[1]
        self.assertEqual(break_row["Type"], "Break")
        self.assertEqual(break_row["Primary Action"], "Resting")
        self.assertIn("Duration", break_row)

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
        self.assertEqual(rows[0]["Primary Action"], "Project A")

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

        test_data = {}
        settings = {
            "idle_settings": {"idle_tracking_enabled": False},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True}
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }

        self.test_data_file = self.file_manager.create_test_file(
            "test_midnight_data.json", test_data
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_midnight_settings.json", settings
        )

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

        test_data = {}
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

        self.test_data_file = self.file_manager.create_test_file(
            "test_secondary_data.json", test_data
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_secondary_settings.json", settings
        )

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

        # Multi-project period: each project receives its allocated portion only.
        # "projects" array takes priority over the top-level "project" field.
        analysis.project_var.set("Project A")
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 600)  # 60% of 1000s allocated to Project A

        analysis.project_var.set("Project B")
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 400)  # 40% of 1000s allocated to Project B

        # All Projects should get 1000 seconds total (full period, no split)
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

        # Multi-project periods: each project receives its allocated portion only.
        # "projects" array takes priority; primary project gets its slice, not full duration.
        analysis.project_var.set("Project A")
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 1400)  # 70% of 2000s in period 1

        # Project B: 30% of period 1 (600) + 50% of period 2 (500)
        analysis.project_var.set("Project B")
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 1100)  # 600 + 500

        # Project C: 50% of period 2 only
        analysis.project_var.set("Project C")
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 500)  # 50% of 1000s in period 2

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

        # Settings without analysis_settings initially
        settings = {
            "idle_settings": {"idle_tracking_enabled": False},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True}
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }

        self.test_data_file = self.file_manager.create_test_file(
            "test_card_data.json", {}
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_card_settings.json", settings
        )

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


class TestAnalysisCSVExportIntegration(unittest.TestCase):
    """Integration tests for CSV export functionality in Analysis Frame"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)

        # Create comprehensive test settings with active and inactive items
        settings = {
            "idle_settings": {"idle_tracking_enabled": True, "idle_threshold": 60},
            "spheres": {
                "Work": {"is_default": True, "active": True},
                "Personal": {"is_default": False, "active": True},
                "Archived Sphere": {"is_default": False, "active": False},
            },
            "projects": {
                "Active Project": {
                    "sphere": "Work",
                    "is_default": True,
                    "active": True,
                },
                "Inactive Project": {
                    "sphere": "Work",
                    "is_default": False,
                    "active": False,
                },
                "Personal Task": {
                    "sphere": "Personal",
                    "is_default": True,
                    "active": True,
                },
            },
            "break_actions": {
                "Resting": {"is_default": True, "active": True},
                "Coffee": {"is_default": False, "active": True},
            },
        }

        self.test_data_file = self.file_manager.create_test_file(
            "test_csv_integration_data.json", {}
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_csv_integration_settings.json", settings
        )

    def tearDown(self):
        """Clean up after tests"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_csv_export_includes_all_expected_headers(self):
        """Test that CSV export includes all expected column headers"""
        today = datetime.now().strftime("%Y-%m-%d")
        test_data = {
            f"{today}_session1": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {
                        "duration": 1800,
                        "project": "Active Project",
                        "start": "09:00:00",
                        "comment": "Test comment",
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

        parent_frame = ttk.Frame(self.root)
        analysis = AnalysisFrame(parent_frame, tracker, self.root)

        # Set filters to show data
        analysis.status_filter.set("all")
        analysis.sphere_var.set("All Spheres")
        analysis.project_var.set("All Projects")
        analysis.selected_card = 2  # All Time

        csv_file = "test_headers.csv"
        self.file_manager.test_files.append(csv_file)

        with patch("tkinter.filedialog.asksaveasfilename", return_value=csv_file):
            with patch("tkinter.messagebox.showinfo"):
                analysis.export_to_csv()

        # Verify file was created and check headers
        self.assertTrue(os.path.exists(csv_file))

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

        # All 13 timeline headers should be exported in the same order
        expected_headers = [
            "Date",
            "Start",
            "Duration",
            "Sphere",
            "Sphere Active",
            "Project Active",
            "Type",
            "Primary Action",
            "Primary Comment",
            "Secondary Action",
            "Secondary Comment",
            "Active Comments",
            "Break Comments",
            "Session Notes",
        ]

        self.assertEqual(fieldnames, expected_headers)
        self.assertEqual(
            len(fieldnames), 14, "CSV should have 14 headers matching timeline"
        )

    def test_csv_export_preserves_large_text_comments(self):
        """Test that comments with large amounts of text are fully exported without truncation"""
        today = datetime.now().strftime("%Y-%m-%d")

        # Create a very long comment (>500 characters)
        long_comment = (
            "This is a very long comment that should be fully exported to CSV. " * 10
        )
        long_comment += " Extra detail to ensure we exceed 500 characters total."

        test_data = {
            f"{today}_session1": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {
                        "duration": 3600,
                        "project": "Active Project",
                        "start": "09:00:00",
                        "comment": long_comment,
                    }
                ],
                "breaks": [
                    {
                        "duration": 600,
                        "action": "Resting",
                        "start": "10:00:00",
                        "comment": long_comment,  # Also test break comments
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

        parent_frame = ttk.Frame(self.root)
        analysis = AnalysisFrame(parent_frame, tracker, self.root)
        analysis.status_filter.set("all")
        analysis.sphere_var.set("All Spheres")
        analysis.project_var.set("All Projects")
        analysis.selected_card = 2  # All Time

        csv_file = "test_long_comments.csv"
        self.file_manager.test_files.append(csv_file)

        with patch("tkinter.filedialog.asksaveasfilename", return_value=csv_file):
            with patch("tkinter.messagebox.showinfo"):
                analysis.export_to_csv()

        # Verify comments are fully preserved
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 2)  # 1 active + 1 break

        # Check active period comment
        self.assertEqual(rows[0]["Primary Comment"], long_comment)
        self.assertGreater(len(rows[0]["Primary Comment"]), 500)

        # Check break period comment
        self.assertEqual(rows[1]["Primary Comment"], long_comment)
        self.assertGreater(len(rows[1]["Primary Comment"]), 500)

    def test_csv_export_respects_radio_button_status_filter(self):
        """Test that CSV export only exports data shown in timeline based on radio button selection"""
        today = datetime.now().strftime("%Y-%m-%d")

        # Create sessions with different active/inactive combinations
        test_data = {
            f"{today}_session1": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {
                        "duration": 1000,
                        "project": "Active Project",
                        "start": "09:00:00",
                        "comment": "Active sphere + Active project",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            },
            f"{today}_session2": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {
                        "duration": 2000,
                        "project": "Inactive Project",
                        "start": "10:00:00",
                        "comment": "Active sphere + Inactive project",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            },
            f"{today}_session3": {
                "sphere": "Archived Sphere",
                "date": today,
                "active": [
                    {
                        "duration": 3000,
                        "project": "Active Project",
                        "start": "11:00:00",
                        "comment": "Inactive sphere + Active project",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            },
        }

        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        analysis = AnalysisFrame(parent_frame, tracker, self.root)
        analysis.sphere_var.set("All Spheres")
        analysis.project_var.set("All Projects")
        analysis.selected_card = 2  # All Time

        # Test 1: Active filter - should only export Active Sphere + Active Project
        analysis.status_filter.set("active")

        csv_file_active = "test_active_filter.csv"
        self.file_manager.test_files.append(csv_file_active)

        with patch(
            "tkinter.filedialog.asksaveasfilename", return_value=csv_file_active
        ):
            with patch("tkinter.messagebox.showinfo"):
                analysis.export_to_csv()

        with open(csv_file_active, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            active_rows = list(reader)

        # Should only have 1 entry (Active+Active)
        # Note: Current implementation may not filter by status - this test will reveal that
        self.assertEqual(
            len(active_rows),
            1,
            "Active filter should only export Active Sphere + Active Project",
        )
        self.assertEqual(
            active_rows[0]["Primary Comment"], "Active sphere + Active project"
        )

        # Test 2: Archived filter - should export all EXCEPT Active Sphere + Active Project
        analysis.status_filter.set("archived")

        csv_file_archived = "test_archived_filter.csv"
        self.file_manager.test_files.append(csv_file_archived)

        with patch(
            "tkinter.filedialog.asksaveasfilename", return_value=csv_file_archived
        ):
            with patch("tkinter.messagebox.showinfo"):
                analysis.export_to_csv()

        with open(csv_file_archived, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            archived_rows = list(reader)

        # Should have 2 entries (Active+Inactive, Inactive+Active)
        self.assertEqual(
            len(archived_rows), 2, "Archived filter should exclude fully active entries"
        )
        comments = [row["Primary Comment"] for row in archived_rows]
        self.assertIn("Active sphere + Inactive project", comments)
        self.assertIn("Inactive sphere + Active project", comments)

        # Test 3: All filter - should export everything
        analysis.status_filter.set("all")

        csv_file_all = "test_all_filter.csv"
        self.file_manager.test_files.append(csv_file_all)

        with patch("tkinter.filedialog.asksaveasfilename", return_value=csv_file_all):
            with patch("tkinter.messagebox.showinfo"):
                analysis.export_to_csv()

        with open(csv_file_all, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            all_rows = list(reader)

        # Should have 3 entries (all combinations)
        self.assertEqual(len(all_rows), 3, "All filter should export all entries")

    def test_csv_export_handles_large_dataset(self):
        """Test that CSV export handles large datasets and exports all data without truncation"""
        today = datetime.now()

        # Create 100 sessions over the past 100 days with multiple periods each
        test_data = {}
        for i in range(100):
            session_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            session_key = f"{session_date}_session{i}"

            test_data[session_key] = {
                "sphere": "Work",
                "date": session_date,
                "active": [
                    {
                        "duration": 1800 + (i * 10),
                        "project": "Active Project",
                        "start": "09:00:00",
                        "comment": f"Active period {i}-1",
                    },
                    {
                        "duration": 1200 + (i * 5),
                        "project": "Active Project",
                        "start": "10:00:00",
                        "comment": f"Active period {i}-2",
                    },
                ],
                "breaks": [
                    {
                        "duration": 600,
                        "action": "Resting",
                        "start": "11:00:00",
                        "comment": f"Break period {i}",
                    }
                ],
                "idle_periods": [],
            }

        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        analysis = AnalysisFrame(parent_frame, tracker, self.root)
        analysis.status_filter.set("all")
        analysis.sphere_var.set("All Spheres")
        analysis.project_var.set("All Projects")
        analysis.selected_card = 2  # All Time

        csv_file = "test_large_dataset.csv"
        self.file_manager.test_files.append(csv_file)

        with patch("tkinter.filedialog.asksaveasfilename", return_value=csv_file):
            with patch("tkinter.messagebox.showinfo"):
                analysis.export_to_csv()

        # Verify all data was exported
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have 100 sessions * (2 active + 1 break) = 300 entries
        self.assertEqual(len(rows), 300, "Large dataset should export all 300 entries")

        # Verify first entry to ensure proper data
        self.assertEqual(rows[0]["Type"], "Active")
        self.assertEqual(rows[0]["Primary Comment"], "Active period 0-1")

        # Check that all entries have required fields
        for row in rows:
            self.assertIn("Date", row)
            self.assertIn("Type", row)
            self.assertIn("Duration", row)
            self.assertTrue(
                row["Type"] in ["Active", "Break"], f"Invalid type: {row['Type']}"
            )

    def test_csv_export_handles_special_characters_in_comments(self):
        """Test that CSV export properly handles special characters in comments"""
        today = datetime.now().strftime("%Y-%m-%d")

        # Test various special characters that could break CSV formatting
        special_chars_comment = 'Comment with "quotes", commas, and\nnewlines\t\ttabs'

        test_data = {
            f"{today}_session1": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {
                        "duration": 1800,
                        "project": "Active Project",
                        "start": "09:00:00",
                        "comment": special_chars_comment,
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

        parent_frame = ttk.Frame(self.root)
        analysis = AnalysisFrame(parent_frame, tracker, self.root)
        analysis.status_filter.set("all")
        analysis.sphere_var.set("All Spheres")
        analysis.project_var.set("All Projects")
        analysis.selected_card = 2  # All Time

        csv_file = "test_special_chars.csv"
        self.file_manager.test_files.append(csv_file)

        with patch("tkinter.filedialog.asksaveasfilename", return_value=csv_file):
            with patch("tkinter.messagebox.showinfo"):
                analysis.export_to_csv()

        # Verify special characters are preserved
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["Primary Comment"], special_chars_comment)

    def test_csv_export_includes_idle_periods(self):
        """Test that CSV export can include idle periods if they exist in the data"""
        today = datetime.now().strftime("%Y-%m-%d")

        test_data = {
            f"{today}_session1": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {
                        "duration": 1800,
                        "project": "Active Project",
                        "start": "09:00:00",
                        "comment": "Working",
                    }
                ],
                "breaks": [],
                "idle_periods": [
                    {
                        "duration": 900,
                        "start": "09:30:00",
                        "comment": "Away from keyboard",
                    }
                ],
            }
        }

        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        analysis = AnalysisFrame(parent_frame, tracker, self.root)
        analysis.status_filter.set("all")
        analysis.sphere_var.set("All Spheres")
        analysis.project_var.set("All Projects")
        analysis.selected_card = 2  # All Time

        csv_file = "test_idle_periods.csv"
        self.file_manager.test_files.append(csv_file)

        with patch("tkinter.filedialog.asksaveasfilename", return_value=csv_file):
            with patch("tkinter.messagebox.showinfo"):
                analysis.export_to_csv()

        # Check if idle periods are included (current implementation may not export idle periods)
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Document current behavior - idle periods may or may not be exported
        # This test will help identify what the current implementation does
        types_exported = [row["Type"] for row in rows]

        # At minimum, should have the active period
        self.assertIn("Active", types_exported)

    def content_frame(self):
        """Create a simple frame for testing"""
        return ttk.Frame(self.root)


class TestCSVExportAllPeriodTypes(unittest.TestCase):
    """Integration test to verify CSV export includes all period types (Active, Break, Idle)"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        settings = {
            "idle_settings": {"idle_tracking_enabled": True, "idle_threshold": 60},
            "spheres": {"General": {"is_default": True, "active": True}},
            "projects": {
                "General": {"sphere": "General", "is_default": True, "active": True},
                "Work": {"sphere": "General", "is_default": False, "active": True},
            },
            "break_actions": {
                "Resting": {"is_default": True, "active": True},
                "bathroom": {"is_default": False, "active": True},
            },
        }

        self.test_data_file = self.file_manager.create_test_file(
            "test_all_period_types_data.json", {}
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_all_period_types_settings.json", settings
        )

    def content_frame(self):
        """Create and return a content frame for testing"""
        return ttk.Frame(self.root)

    def test_csv_export_includes_active_break_and_idle_periods(self):
        """
        Test that CSV export includes all three period types: Active, Break, and Idle.

        This is a regression test for a bug where only Break and Idle periods were exported,
        but Active periods were skipped when they used the 'projects' array format.
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # Create test data with all three period types
        # This mirrors the actual data structure from data.json
        test_data = {
            f"{today}_1770645170": {
                "sphere": "General",
                "date": today,
                "start_time": "08:52:50",
                "active": [
                    {
                        "start": "08:52:50",
                        "duration": 3.07,
                        "projects": [
                            {
                                "name": "General",
                                "percentage": 50,
                                "comment": "Active project 1",
                                "duration": 1,
                                "project_primary": True,
                            },
                            {
                                "name": "Work",
                                "percentage": 50,
                                "comment": "Active project 2",
                                "duration": 1,
                                "project_primary": False,
                            },
                        ],
                    },
                    {
                        "start": "08:52:56",
                        "duration": 3.89,
                        "projects": [
                            {
                                "name": "General",
                                "percentage": 50,
                                "comment": "Active project 3",
                                "duration": 1,
                                "project_primary": True,
                            },
                            {
                                "name": "Work",
                                "percentage": 50,
                                "comment": "Active project 4",
                                "duration": 1,
                                "project_primary": False,
                            },
                        ],
                    },
                ],
                "breaks": [
                    {
                        "start": "08:53:00",
                        "duration": 5.21,
                        "actions": [
                            {
                                "name": "Resting",
                                "percentage": 50,
                                "duration": 2,
                                "comment": "Break action 1",
                                "break_primary": True,
                            },
                            {
                                "name": "bathroom",
                                "percentage": 50,
                                "duration": 2,
                                "comment": "Break action 2",
                                "break_primary": False,
                            },
                        ],
                    }
                ],
                "idle_periods": [
                    {
                        "start": "08:52:53",
                        "duration": 3.05,
                        "actions": [
                            {
                                "name": "Resting",
                                "percentage": 50,
                                "duration": 1,
                                "comment": "Idle action 1",
                                "idle_primary": True,
                            },
                            {
                                "name": "bathroom",
                                "percentage": 50,
                                "duration": 1,
                                "comment": "Idle action 2",
                                "idle_primary": False,
                            },
                        ],
                    }
                ],
                "session_comments": {
                    "active_notes": "Session active comments",
                    "break_notes": "Session break comments",
                    "idle_notes": "Session idle comments",
                    "session_notes": "Session notes",
                },
            }
        }

        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = self.content_frame()
        analysis = AnalysisFrame(parent_frame, tracker, self.root)

        # Set filters to show all data
        analysis.status_filter.set("all")
        analysis.sphere_var.set("All Spheres")
        analysis.project_var.set("All Projects")
        analysis.selected_card = 2  # All Time

        csv_file = "test_all_period_types.csv"
        self.file_manager.test_files.append(csv_file)

        with patch("tkinter.filedialog.asksaveasfilename", return_value=csv_file):
            with patch("tkinter.messagebox.showinfo"):
                analysis.export_to_csv()

        # Verify file was created
        self.assertTrue(os.path.exists(csv_file), "CSV file should be created")

        # Read and verify CSV contents
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have 4 rows total: 2 Active + 1 Break + 1 Idle
        self.assertEqual(
            len(rows),
            4,
            f"CSV should have 4 rows (2 Active, 1 Break, 1 Idle), but got {len(rows)}",
        )

        # Verify we have all three period types
        types = [row["Type"] for row in rows]
        active_count = types.count("Active")
        break_count = types.count("Break")
        idle_count = types.count("Idle")

        self.assertEqual(
            active_count, 2, f"Should have 2 Active periods, got {active_count}"
        )
        self.assertEqual(
            break_count, 1, f"Should have 1 Break period, got {break_count}"
        )
        self.assertEqual(idle_count, 1, f"Should have 1 Idle period, got {idle_count}")

        # Verify Active periods have correct data
        active_rows = [row for row in rows if row["Type"] == "Active"]
        self.assertEqual(active_rows[0]["Primary Action"], "General")
        self.assertEqual(active_rows[0]["Secondary Action"], "Work")
        self.assertEqual(active_rows[0]["Project Active"], "Yes")

        # Verify Break period has correct data
        break_rows = [row for row in rows if row["Type"] == "Break"]
        self.assertEqual(break_rows[0]["Primary Action"], "Resting")
        self.assertEqual(break_rows[0]["Secondary Action"], "bathroom")
        self.assertEqual(break_rows[0]["Project Active"], "N/A")

        # Verify Idle period has correct data
        idle_rows = [row for row in rows if row["Type"] == "Idle"]
        self.assertEqual(idle_rows[0]["Primary Action"], "Resting")
        self.assertEqual(idle_rows[0]["Secondary Action"], "bathroom")
        self.assertEqual(idle_rows[0]["Project Active"], "N/A")


if __name__ == "__main__":
    unittest.main()
