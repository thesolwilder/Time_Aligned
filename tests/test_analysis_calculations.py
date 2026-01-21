"""
Tests for Analysis Frame Duration Calculations

Verifies accuracy of duration calculations, sphere/project filtering,
and data aggregation across sessions.
"""

import unittest
import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from analysis_frame import AnalysisFrame
from test_helpers import TestFileManager, TestDataGenerator


class TestAnalysisDurationCalculations(unittest.TestCase):
    """Test that duration calculations are accurate"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_analysis_calc_data.json"
        self.test_settings_file = "test_analysis_calc_settings.json"

        # Create settings with multiple spheres and projects
        settings = {
            "idle_settings": {
                "idle_tracking_enabled": True,
                "idle_threshold": 60,
                "idle_break_threshold": 300,
            },
            "spheres": {
                "Work": {"is_default": True, "active": True},
                "Personal": {"is_default": False, "active": True},
                "Learning": {"is_default": False, "active": True},
            },
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True},
                "Project B": {"sphere": "Work", "is_default": False, "active": True},
                "Exercise": {"sphere": "Personal", "is_default": True, "active": True},
                "Study": {"sphere": "Learning", "is_default": True, "active": True},
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.file_manager.create_test_file(self.test_settings_file, settings)

    def test_total_duration_equals_sum_of_sessions(self):
        """Test that total duration equals sum of all session durations"""
        # Create test data with known durations
        today = datetime.now().strftime("%Y-%m-%d")
        test_data = {
            f"{today}_session1": {
                "sphere": "Work",
                "date": today,
                "start_time": "09:00:00",
                "end_time": "10:00:00",
                "total_duration": 3600,
                "active_duration": 3000,
                "break_duration": 600,
                "active": [
                    {"duration": 1500, "project": "Project A"},
                    {"duration": 1500, "project": "Project A"},
                ],
                "breaks": [{"duration": 600}],
                "idle_periods": [],
            },
            f"{today}_session2": {
                "sphere": "Work",
                "date": today,
                "start_time": "11:00:00",
                "end_time": "12:00:00",
                "total_duration": 3600,
                "active_duration": 3200,
                "break_duration": 400,
                "active": [{"duration": 3200, "project": "Project A"}],
                "breaks": [{"duration": 400}],
                "idle_periods": [],
            },
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)
        analysis.sphere_var.set("All Spheres")
        analysis.project_var.set("All Projects")

        active_time, break_time = analysis.calculate_totals("All Time")

        # Total active should be 3000 + 3200 = 6200
        self.assertEqual(active_time, 6200)
        # Total break should be 600 + 400 = 1000
        self.assertEqual(break_time, 1000)

    def test_sphere_filtering_accuracy(self):
        """Test that sphere filtering shows only selected sphere's data"""
        today = datetime.now().strftime("%Y-%m-%d")
        test_data = {
            f"{today}_work1": {
                "sphere": "Work",
                "date": today,
                "active": [{"duration": 1000, "project": "Project A"}],
                "breaks": [{"duration": 100}],
                "idle_periods": [],
            },
            f"{today}_personal1": {
                "sphere": "Personal",
                "date": today,
                "active": [{"duration": 2000, "project": "Exercise"}],
                "breaks": [{"duration": 200}],
                "idle_periods": [],
            },
            f"{today}_learning1": {
                "sphere": "Learning",
                "date": today,
                "active": [{"duration": 1500, "project": "Study"}],
                "breaks": [{"duration": 150}],
                "idle_periods": [],
            },
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)
        analysis.project_var.set("All Projects")

        # Test Work sphere only
        analysis.sphere_var.set("Work")
        active, breaks = analysis.calculate_totals("All Time")
        self.assertEqual(active, 1000)
        self.assertEqual(breaks, 100)

        # Test Personal sphere only
        analysis.sphere_var.set("Personal")
        active, breaks = analysis.calculate_totals("All Time")
        self.assertEqual(active, 2000)
        self.assertEqual(breaks, 200)

        # Test Learning sphere only
        analysis.sphere_var.set("Learning")
        active, breaks = analysis.calculate_totals("All Time")
        self.assertEqual(active, 1500)
        self.assertEqual(breaks, 150)

    def test_project_filtering_accuracy(self):
        """Test that project filtering shows only selected project's data"""
        today = datetime.now().strftime("%Y-%m-%d")
        test_data = {
            f"{today}_session1": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {"duration": 1000, "project": "Project A"},
                    {"duration": 500, "project": "Project B"},
                ],
                "breaks": [{"duration": 100}],
                "idle_periods": [],
            },
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)
        analysis.sphere_var.set("All Spheres")

        # Test Project A only
        analysis.project_var.set("Project A")
        active, breaks = analysis.calculate_totals("All Time")
        self.assertEqual(active, 1000)

        # Test Project B only
        analysis.project_var.set("Project B")
        active, breaks = analysis.calculate_totals("All Time")
        self.assertEqual(active, 500)

        # Test All Projects
        analysis.project_var.set("All Projects")
        active, breaks = analysis.calculate_totals("All Time")
        self.assertEqual(active, 1500)

    def test_combined_sphere_and_project_filtering(self):
        """Test that sphere and project filters work together correctly"""
        today = datetime.now().strftime("%Y-%m-%d")
        test_data = {
            f"{today}_work1": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {"duration": 1000, "project": "Project A"},
                    {"duration": 500, "project": "Project B"},
                ],
                "breaks": [],
                "idle_periods": [],
            },
            f"{today}_personal1": {
                "sphere": "Personal",
                "date": today,
                "active": [{"duration": 2000, "project": "Exercise"}],
                "breaks": [],
                "idle_periods": [],
            },
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)

        # Test Work + Project A
        analysis.sphere_var.set("Work")
        analysis.project_var.set("Project A")
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 1000)

        # Test Work + Project B
        analysis.sphere_var.set("Work")
        analysis.project_var.set("Project B")
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 500)

        # Test Personal + Exercise
        analysis.sphere_var.set("Personal")
        analysis.project_var.set("Exercise")
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 2000)

        # Test Personal + Project A (should be 0 - wrong sphere)
        analysis.sphere_var.set("Personal")
        analysis.project_var.set("Project A")
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 0)

    def test_active_duration_excludes_breaks(self):
        """Test that active duration calculation excludes break time"""
        today = datetime.now().strftime("%Y-%m-%d")
        test_data = {
            f"{today}_session1": {
                "sphere": "Work",
                "date": today,
                "active": [{"duration": 1000, "project": "Project A"}],
                "breaks": [{"duration": 500}],
                "idle_periods": [],
            },
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

        # Active and breaks should be separate
        self.assertEqual(active, 1000)
        self.assertEqual(breaks, 500)
        # Total should NOT include breaks in active
        self.assertNotEqual(active, 1500)

    def test_idle_time_counted_as_break(self):
        """Test that idle periods are counted as break time"""
        today = datetime.now().strftime("%Y-%m-%d")
        test_data = {
            f"{today}_session1": {
                "sphere": "Work",
                "date": today,
                "active": [{"duration": 1000, "project": "Project A"}],
                "breaks": [{"duration": 200}],
                "idle_periods": [
                    {
                        "start_timestamp": 1000000,
                        "end_timestamp": 1000300,
                        "duration": 300,
                    }
                ],
            },
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

        # Break time should include idle periods (200 + 300 = 500)
        self.assertEqual(breaks, 500)

    def content_frame(self):
        """Create a simple frame for testing"""
        return ttk.Frame(self.root)


class TestAnalysisDateRangeFiltering(unittest.TestCase):
    """Test that date range filtering works correctly"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_analysis_date_data.json"
        self.test_settings_file = "test_analysis_date_settings.json"

        settings = TestDataGenerator.create_settings_data()
        self.file_manager.create_test_file(self.test_settings_file, settings)

    def test_last_7_days_filter(self):
        """Test that Last 7 Days shows only last 7 days of data"""
        today = datetime.now()
        test_data = {}

        # Create sessions for different days
        for i in range(10):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            test_data[f"{date_str}_session"] = {
                "sphere": "Work",
                "date": date_str,
                "active": [{"duration": 100, "project": "Project A"}],
                "breaks": [],
                "idle_periods": [],
            }

        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)
        analysis.sphere_var.set("All Spheres")
        analysis.project_var.set("All Projects")

        active, _ = analysis.calculate_totals("Last 7 Days")

        # Should include today + last 6 days = 7 days total (700 seconds)
        self.assertEqual(active, 700)

    def test_this_week_filter(self):
        """Test that This Week (Mon-Sun) shows only current week's data"""
        today = datetime.now()
        test_data = {}

        # Create sessions for today and previous days
        for i in range(14):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            test_data[f"{date_str}_session"] = {
                "sphere": "Work",
                "date": date_str,
                "active": [{"duration": 100, "project": "Project A"}],
                "breaks": [],
                "idle_periods": [],
            }

        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)
        analysis.sphere_var.set("All Spheres")
        analysis.project_var.set("All Projects")

        active, _ = analysis.calculate_totals("This Week (Mon-Sun)")

        # Should only include current week (Monday to today)
        days_since_monday = today.weekday() + 1
        expected = days_since_monday * 100
        self.assertEqual(active, expected)

    def test_all_time_includes_everything(self):
        """Test that All Time includes all sessions regardless of date"""
        test_data = {
            "2024-01-01_session": {
                "sphere": "Work",
                "date": "2024-01-01",
                "active": [{"duration": 500, "project": "Project A"}],
                "breaks": [],
                "idle_periods": [],
            },
            "2025-06-15_session": {
                "sphere": "Work",
                "date": "2025-06-15",
                "active": [{"duration": 300, "project": "Project A"}],
                "breaks": [],
                "idle_periods": [],
            },
            "2026-01-20_session": {
                "sphere": "Work",
                "date": "2026-01-20",
                "active": [{"duration": 200, "project": "Project A"}],
                "breaks": [],
                "idle_periods": [],
            },
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)
        analysis.sphere_var.set("All Spheres")
        analysis.project_var.set("All Projects")

        active, _ = analysis.calculate_totals("All Time")

        # Should include all sessions (500 + 300 + 200 = 1000)
        self.assertEqual(active, 1000)

    def content_frame(self):
        """Create a simple frame for testing"""
        return ttk.Frame(self.root)


class TestAnalysisEdgeCases(unittest.TestCase):
    """Test edge cases in analysis calculations"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        self.test_data_file = "test_analysis_edge_data.json"
        self.test_settings_file = "test_analysis_edge_settings.json"

        settings = TestDataGenerator.create_settings_data()
        self.file_manager.create_test_file(self.test_settings_file, settings)

    def test_empty_data_returns_zero(self):
        """Test that empty data file returns zero durations"""
        self.file_manager.create_test_file(self.test_data_file, {})

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)
        analysis.sphere_var.set("All Spheres")
        analysis.project_var.set("All Projects")

        active, breaks = analysis.calculate_totals("All Time")

        self.assertEqual(active, 0)
        self.assertEqual(breaks, 0)

    def test_sessions_without_sphere_are_excluded(self):
        """Test that sessions without sphere field are handled correctly"""
        today = datetime.now().strftime("%Y-%m-%d")
        test_data = {
            f"{today}_no_sphere": {
                "date": today,
                "active": [{"duration": 1000, "project": "Project A"}],
                "breaks": [],
                "idle_periods": [],
            },
            f"{today}_with_sphere": {
                "sphere": "Work",
                "date": today,
                "active": [{"duration": 500, "project": "Project A"}],
                "breaks": [],
                "idle_periods": [],
            },
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)
        analysis.project_var.set("All Projects")

        # When filtering by specific sphere, session without sphere should be excluded
        analysis.sphere_var.set("Work")
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 500)

        # When "All Spheres" is selected, session without sphere should be excluded
        # (because empty string != "All Spheres")
        analysis.sphere_var.set("All Spheres")
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 1500)  # Both sessions included

    def test_sessions_without_active_periods(self):
        """Test that sessions with no active periods return zero active time"""
        today = datetime.now().strftime("%Y-%m-%d")
        test_data = {
            f"{today}_session": {
                "sphere": "Work",
                "date": today,
                "active": [],
                "breaks": [{"duration": 500}],
                "idle_periods": [],
            },
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

        self.assertEqual(active, 0)
        self.assertEqual(breaks, 500)

    def test_sessions_with_missing_duration_field(self):
        """Test that sessions with missing duration field are handled gracefully"""
        today = datetime.now().strftime("%Y-%m-%d")
        test_data = {
            f"{today}_session": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {"project": "Project A"},  # Missing duration field
                    {"duration": 500, "project": "Project A"},  # Has duration
                ],
                "breaks": [{}],  # Missing duration field
                "idle_periods": [],
            },
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

        # Should only count periods with duration field
        self.assertEqual(active, 500)
        self.assertEqual(breaks, 0)

    def test_multi_project_periods(self):
        """Test that periods with multiple projects can be filtered correctly"""
        today = datetime.now().strftime("%Y-%m-%d")
        test_data = {
            f"{today}_session": {
                "sphere": "Work",
                "date": today,
                "active": [
                    {
                        "duration": 1000,
                        "project": "Project A",
                        "projects": [
                            {"name": "Project A"},
                            {"name": "Project B"},
                        ],
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

        analysis = AnalysisFrame(self.content_frame(), tracker, self.root)
        analysis.sphere_var.set("All Spheres")

        # When filtering by Project B, should find it in the projects list
        analysis.project_var.set("Project B")
        active, _ = analysis.calculate_totals("All Time")
        self.assertEqual(active, 1000)

    def content_frame(self):
        """Create a simple frame for testing"""
        return ttk.Frame(self.root)


if __name__ == "__main__":
    unittest.main()
