"""
Tests for Analysis Frame Filtering

Tests that filtering by sphere and project works correctly in calculate_totals.
"""

import unittest
import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from src.analysis_frame import AnalysisFrame
from tests.test_helpers import TestFileManager


class TestAnalysisFrameSphereFiltering(unittest.TestCase):
    """Test that sphere filtering affects totals correctly"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        settings = {
            "idle_settings": {"idle_tracking_enabled": False},
            "spheres": {
                "Work": {"is_default": True, "active": True},
                "Personal": {"is_default": False, "active": True},
            },
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True},
                "Project B": {"sphere": "Work", "is_default": False, "active": True},
                "Exercise": {"sphere": "Personal", "is_default": True, "active": True},
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_sphere_filter_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_sphere_filter_data.json"
        )

    def test_sphere_filter_work_only(self):
        """Test filtering by Work sphere"""
        date = "2026-01-22"
        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "total_duration": 5000,
                "active_duration": 4000,
                "break_duration": 1000,
                "active": [
                    {"duration": 2000, "project": "Project A"},
                    {"duration": 2000, "project": "Project B"},
                ],
                "breaks": [{"duration": 1000}],
                "idle_periods": [],
            },
            f"{date}_session2": {
                "sphere": "Personal",
                "date": date,
                "total_duration": 2000,
                "active_duration": 2000,
                "break_duration": 0,
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

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Filter by Work sphere
        frame.sphere_var.set("Work")
        frame.project_var.set("All Projects")
        active, breaks = frame.calculate_totals("All Time")

        # Should only count Work sessions: 4000 active, 1000 break
        self.assertEqual(active, 4000)
        self.assertEqual(breaks, 1000)

    def test_sphere_filter_personal_only(self):
        """Test filtering by Personal sphere"""
        date = "2026-01-22"
        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "total_duration": 5000,
                "active_duration": 4000,
                "break_duration": 1000,
                "active": [
                    {"duration": 2000, "project": "Project A"},
                    {"duration": 2000, "project": "Project B"},
                ],
                "breaks": [{"duration": 1000}],
                "idle_periods": [],
            },
            f"{date}_session2": {
                "sphere": "Personal",
                "date": date,
                "total_duration": 2000,
                "active_duration": 2000,
                "break_duration": 0,
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

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Filter by Personal sphere
        frame.sphere_var.set("Personal")
        frame.project_var.set("All Projects")
        active, breaks = frame.calculate_totals("All Time")

        # Should only count Personal sessions: 2000 active, 0 break
        self.assertEqual(active, 2000)
        self.assertEqual(breaks, 0)

    def test_sphere_filter_all_spheres(self):
        """Test filtering by All Spheres"""
        date = "2026-01-22"
        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "total_duration": 5000,
                "active_duration": 4000,
                "break_duration": 1000,
                "active": [
                    {"duration": 2000, "project": "Project A"},
                    {"duration": 2000, "project": "Project B"},
                ],
                "breaks": [{"duration": 1000}],
                "idle_periods": [],
            },
            f"{date}_session2": {
                "sphere": "Personal",
                "date": date,
                "total_duration": 2000,
                "active_duration": 2000,
                "break_duration": 0,
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

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Filter by All Spheres
        frame.sphere_var.set("All Spheres")
        frame.project_var.set("All Projects")
        active, breaks = frame.calculate_totals("All Time")

        # Should count both: 6000 active, 1000 break
        self.assertEqual(active, 6000)
        self.assertEqual(breaks, 1000)


class TestAnalysisFrameProjectFiltering(unittest.TestCase):
    """Test that project filtering affects totals correctly"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        settings = {
            "idle_settings": {"idle_tracking_enabled": False},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True},
                "Project B": {"sphere": "Work", "is_default": False, "active": True},
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_project_filter_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_project_filter_data.json"
        )

    def test_project_filter_project_a(self):
        """Test filtering by specific project"""
        date = "2026-01-22"
        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "total_duration": 4000,
                "active_duration": 4000,
                "break_duration": 0,
                "active": [
                    {"duration": 2000, "project": "Project A"},
                    {"duration": 1000, "project": "Project B"},
                    {"duration": 1000, "project": "Project A"},
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
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Filter by Project A
        frame.sphere_var.set("All Spheres")
        frame.project_var.set("Project A")
        active, breaks = frame.calculate_totals("All Time")

        # Should count periods with Project A: 3000 active
        self.assertEqual(active, 3000)

    def test_project_filter_project_b(self):
        """Test filtering by different project"""
        date = "2026-01-22"
        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "total_duration": 4000,
                "active_duration": 4000,
                "break_duration": 0,
                "active": [
                    {"duration": 2000, "project": "Project A"},
                    {"duration": 1000, "project": "Project B"},
                    {"duration": 1000, "project": "Project A"},
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
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Filter by Project B
        frame.sphere_var.set("All Spheres")
        frame.project_var.set("Project B")
        active, breaks = frame.calculate_totals("All Time")

        # Should count periods with Project B: 1000 active
        self.assertEqual(active, 1000)


class TestAnalysisTimelineDataStructure(unittest.TestCase):
    """Test that timeline data returns correct structure with all required fields"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        settings = {
            "idle_settings": {"idle_tracking_enabled": False},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True},
                "Project B": {"sphere": "Work", "is_default": False, "active": True},
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_timeline_data_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_timeline_data.json"
        )

    def test_timeline_data_has_all_required_fields(self):
        """Test that get_timeline_data returns all required fields for each period"""
        date = "2026-01-28"
        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "start_timestamp": 1234567890,
                "end_timestamp": 1234571890,
                "total_duration": 4000,
                "active_duration": 3000,
                "break_duration": 1000,
                "active": [
                    {
                        "duration": 3000,
                        "project": "Project A",
                        "comment": "Working on feature",
                        "start": "10:30:00",
                        "start_timestamp": 1234567890,
                    }
                ],
                "breaks": [
                    {
                        "duration": 1000,
                        "action": "Resting",
                        "comment": "Coffee break",
                        "start": "11:20:00",
                        "start_timestamp": 1234570890,
                    }
                ],
                "idle_periods": [],
                "session_active_comments": "Overall session was productive",
                "session_break_idle_comments": "Needed a few breaks",
                "session_notes": "Good progress today",
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Get timeline data
        timeline_data = frame.get_timeline_data("All Time")

        # Verify we have 2 periods (1 active, 1 break)
        self.assertEqual(len(timeline_data), 2)

        # Check active period
        active_period = timeline_data[0]
        self.assertEqual(active_period["date"], date)
        self.assertEqual(active_period["period_start"], "10:30:00")
        self.assertEqual(active_period["duration"], 3000)
        self.assertEqual(active_period["type"], "Active")
        self.assertEqual(active_period["primary_project"], "Project A")
        self.assertEqual(active_period["primary_comment"], "Working on feature")
        self.assertEqual(active_period["secondary_project"], "")
        self.assertEqual(active_period["secondary_comment"], "")
        self.assertEqual(
            active_period["session_active_comments"], "Overall session was productive"
        )
        self.assertEqual(
            active_period["session_break_idle_comments"], "Needed a few breaks"
        )
        self.assertEqual(active_period["session_notes"], "Good progress today")

        # Check break period
        break_period = timeline_data[1]
        self.assertEqual(break_period["date"], date)
        self.assertEqual(break_period["period_start"], "11:20:00")
        self.assertEqual(break_period["duration"], 1000)
        self.assertEqual(break_period["type"], "Break")
        self.assertEqual(break_period["primary_project"], "Resting")
        self.assertEqual(break_period["primary_comment"], "Coffee break")
        self.assertEqual(break_period["secondary_project"], "")
        self.assertEqual(break_period["secondary_comment"], "")

    def test_timeline_data_with_secondary_project(self):
        """Test that secondary projects are properly separated from primary"""
        date = "2026-01-28"
        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "start_timestamp": 1234567890,
                "end_timestamp": 1234571890,
                "total_duration": 3000,
                "active_duration": 3000,
                "break_duration": 0,
                "active": [
                    {
                        "duration": 3000,
                        "start": "10:30:00",
                        "start_timestamp": 1234567890,
                        "projects": [
                            {
                                "name": "Project A",
                                "comment": "Primary task",
                                "project_primary": True,
                                "percentage": 70,
                            },
                            {
                                "name": "Project B",
                                "comment": "Secondary task",
                                "project_primary": False,
                                "percentage": 30,
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

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Get timeline data
        timeline_data = frame.get_timeline_data("All Time")

        # Verify we have 1 period
        self.assertEqual(len(timeline_data), 1)

        # Check that primary and secondary are separated
        period = timeline_data[0]
        self.assertEqual(period["primary_project"], "Project A")
        self.assertEqual(period["primary_comment"], "Primary task")
        self.assertEqual(period["secondary_project"], "Project B")
        self.assertEqual(period["secondary_comment"], "Secondary task")

    def test_timeline_data_with_primary_and_secondary_break(self):
        """Test that primary and secondary break actions are properly separated"""
        date = "2026-01-28"
        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "start_timestamp": 1234567890,
                "end_timestamp": 1234571890,
                "total_duration": 1000,
                "active_duration": 0,
                "break_duration": 1000,
                "active": [],
                "breaks": [
                    {
                        "duration": 1000,
                        "start": "11:20:00",
                        "start_timestamp": 1234570890,
                        "actions": [
                            {
                                "name": "Coffee",
                                "comment": "Getting coffee",
                                "break_primary": True,
                                "percentage": 60,
                            },
                            {
                                "name": "Snack",
                                "comment": "Quick snack",
                                "break_primary": False,
                                "percentage": 40,
                            },
                        ],
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
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Get timeline data
        timeline_data = frame.get_timeline_data("All Time")

        # Verify we have 1 period
        self.assertEqual(len(timeline_data), 1)

        # BUG FIX: Check that primary break action shows up (not just secondary)
        period = timeline_data[0]
        self.assertEqual(period["type"], "Break")
        self.assertEqual(period["primary_project"], "Coffee")
        self.assertEqual(period["primary_comment"], "Getting coffee")
        self.assertEqual(period["secondary_project"], "Snack")
        self.assertEqual(period["secondary_comment"], "Quick snack")

    def test_timeline_data_with_primary_and_secondary_idle(self):
        """Test that primary and secondary idle actions are properly separated"""
        date = "2026-01-28"
        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "start_timestamp": 1234567890,
                "end_timestamp": 1234571890,
                "total_duration": 1000,
                "active_duration": 0,
                "break_duration": 0,
                "active": [],
                "breaks": [],
                "idle_periods": [
                    {
                        "duration": 1000,
                        "start": "11:20:00",
                        "start_timestamp": 1234570890,
                        "end_timestamp": 1234571890,
                        "actions": [
                            {
                                "name": "Thinking",
                                "comment": "Deep thinking",
                                "idle_primary": True,
                                "percentage": 70,
                            },
                            {
                                "name": "Wandering",
                                "comment": "Mind wandering",
                                "idle_primary": False,
                                "percentage": 30,
                            },
                        ],
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
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Get timeline data
        timeline_data = frame.get_timeline_data("All Time")

        # Verify we have 1 period
        self.assertEqual(len(timeline_data), 1)

        # Check that primary idle action shows up (not just secondary)
        period = timeline_data[0]
        self.assertEqual(period["type"], "Idle")
        self.assertEqual(period["primary_project"], "Thinking")
        self.assertEqual(period["primary_comment"], "Deep thinking")
        self.assertEqual(period["secondary_project"], "Wandering")
        self.assertEqual(period["secondary_comment"], "Mind wandering")


if __name__ == "__main__":
    unittest.main()
