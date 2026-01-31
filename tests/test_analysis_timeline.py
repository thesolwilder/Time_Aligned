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
        self.assertEqual(active_period["session_break_idle_comments"], "")
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
        # Session-level comments show contextually
        self.assertEqual(break_period["session_active_comments"], "")
        self.assertEqual(
            break_period["session_break_idle_comments"], "Needed a few breaks"
        )
        self.assertEqual(break_period["session_notes"], "Good progress today")

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

    def test_session_level_comments_appear_on_all_periods(self):
        """Test that session-level comments appear on ALL periods from that session"""
        date = "2026-01-28"
        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "start_timestamp": 1234567890,
                "end_timestamp": 1234574890,
                "total_duration": 7000,
                "active_duration": 3000,
                "break_duration": 2000,
                "active": [
                    {
                        "duration": 1500,
                        "project": "Project A",
                        "comment": "First active period",
                        "start": "10:30:00",
                        "start_timestamp": 1234567890,
                    },
                    {
                        "duration": 1500,
                        "project": "Project B",
                        "comment": "Second active period",
                        "start": "11:00:00",
                        "start_timestamp": 1234569690,
                    },
                ],
                "breaks": [
                    {
                        "duration": 1000,
                        "action": "Coffee",
                        "comment": "First break",
                        "start": "10:55:00",
                        "start_timestamp": 1234569390,
                    },
                    {
                        "duration": 1000,
                        "action": "Lunch",
                        "comment": "Second break",
                        "start": "12:00:00",
                        "start_timestamp": 1234573290,
                    },
                ],
                "idle_periods": [
                    {
                        "duration": 2000,
                        "action": "Idle",
                        "comment": "Idle time",
                        "start": "11:30:00",
                        "start_timestamp": 1234571490,
                        "end_timestamp": 1234573490,
                    }
                ],
                "session_active_comments": "Session was very productive",
                "session_break_idle_comments": "Took good breaks",
                "session_notes": "Great day overall",
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Explicitly set filters to show all data
        frame.sphere_var.set("All Spheres")
        frame.project_var.set("All Projects")

        # Get timeline data
        timeline_data = frame.get_timeline_data("All Time")

        # Verify we have 5 periods (2 active, 2 breaks, 1 idle)
        self.assertEqual(len(timeline_data), 5)

        # Session-level comments now show contextually:
        # - session_active_comments: only on Active periods
        # - session_break_idle_comments: only on Break/Idle periods
        # - session_notes: on ALL periods
        expected_session_notes = "Great day overall"

        for period in timeline_data:
            # Session notes should appear on ALL periods
            self.assertEqual(
                period["session_notes"],
                expected_session_notes,
                f"Period {period['primary_project']} missing session_notes",
            )

            # Active comments only on Active periods
            if period["type"] == "Active":
                self.assertEqual(
                    period["session_active_comments"],
                    "Session was very productive",
                    f"Active period {period['primary_project']} should have session_active_comments",
                )
                self.assertEqual(
                    period["session_break_idle_comments"],
                    "",
                    f"Active period {period['primary_project']} should NOT have session_break_idle_comments",
                )
            # Break/idle comments only on Break/Idle periods
            elif period["type"] in ["Break", "Idle"]:
                self.assertEqual(
                    period["session_active_comments"],
                    "",
                    f"{period['type']} period {period['primary_project']} should NOT have session_active_comments",
                )
                self.assertEqual(
                    period["session_break_idle_comments"],
                    "Took good breaks",
                    f"{period['type']} period {period['primary_project']} should have session_break_idle_comments",
                )


class TestAnalysisTimelineUIData(unittest.TestCase):
    """Test that timeline data from actual saved sessions displays correctly"""

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
                "learning_to_code": {
                    "sphere": "Work",
                    "is_default": True,
                    "active": True,
                }
            },
            "break_actions": {"bathroom": {"is_default": True, "active": True}},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_ui_data_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file("test_ui_data.json")

    def test_timeline_shows_session_comments_from_completion_frame_format(self):
        """
        BUG: Session comments saved by completion frame use different field names
        than what analysis frame expects, so they don't show in UI

        Completion frame saves as: session_comments.active_notes, etc.
        Analysis frame expects: session_active_comments, session_break_idle_comments, session_notes
        """
        date = "2026-01-29"
        # This is how completion_frame.py actually saves the data
        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "start_timestamp": 1234567890,
                "end_timestamp": 1234571890,
                "total_duration": 7000,
                "active_duration": 3000,
                "break_duration": 4000,
                "active": [
                    {
                        "duration": 3000,
                        "project": "learning_to_code",
                        "comment": "developing",
                        "start": "11:06:00",
                        "start_timestamp": 1234567890,
                    }
                ],
                "breaks": [
                    {
                        "duration": 4000,
                        "action": "bathroom",
                        "comment": "poop",
                        "start": "11:08:00",
                        "start_timestamp": 1234570890,
                    }
                ],
                "idle_periods": [],
                # This is how completion frame saves session comments
                "session_comments": {
                    "active_notes": "working hard",
                    "break_notes": "necessary",
                    "idle_notes": "",
                    "session_notes": "good session",
                },
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Set filters to show all data
        frame.sphere_var.set("All Spheres")
        frame.project_var.set("All Projects")

        # Get timeline data
        timeline_data = frame.get_timeline_data("All Time")

        # Should have 2 periods (1 active, 1 break)
        self.assertEqual(len(timeline_data), 2)

        # Session comments now show contextually
        active_period = timeline_data[0]
        self.assertEqual(active_period["session_active_comments"], "working hard")
        self.assertEqual(active_period["session_break_idle_comments"], "")
        self.assertEqual(active_period["session_notes"], "good session")

        break_period = timeline_data[1]
        self.assertEqual(break_period["session_active_comments"], "")
        self.assertEqual(break_period["session_break_idle_comments"], "necessary")
        self.assertEqual(break_period["session_notes"], "good session")

    def test_session_comments_show_contextually_by_period_type(self):
        """
        FEATURE: Session comments should show contextually based on period type:
        - session_active_comments: Only show during Active periods
        - session_break_idle_comments: Show during Break/Idle periods (break notes for break, idle notes for idle)
        - session_notes: Show for ALL periods
        """
        date = "2026-01-29"
        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "start_timestamp": 1234567890,
                "end_timestamp": 1234571890,
                "total_duration": 9000,
                "active_duration": 3000,
                "break_duration": 4000,
                "active": [
                    {
                        "duration": 3000,
                        "project": "drawing",
                        "comment": "active period comment",
                        "start": "11:42:00",
                        "start_timestamp": 1234567890,
                    }
                ],
                "breaks": [
                    {
                        "duration": 3000,
                        "action": "bathroom",
                        "comment": "break period comment",
                        "start": "11:43:00",
                        "start_timestamp": 1234570890,
                    }
                ],
                "idle_periods": [
                    {
                        "duration": 2000,
                        "action": "Idle",
                        "comment": "idle period comment",
                        "start": "11:44:00",
                        "start_timestamp": 1234573890,
                        "end_timestamp": 1234575890,
                    }
                ],
                "session_comments": {
                    "active_notes": "active periods comment",
                    "break_notes": "break periods comment",
                    "idle_notes": "idle periods comment",
                    "session_notes": "session notes",
                },
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Set filters to show all data
        frame.sphere_var.set("All Spheres")
        frame.project_var.set("All Projects")

        # Get timeline data
        timeline_data = frame.get_timeline_data("All Time")

        # Should have 3 periods (1 active, 1 break, 1 idle)
        self.assertEqual(len(timeline_data), 3)

        # Active period: Should show active comments and session notes, but NOT break/idle comments
        active_period = timeline_data[0]
        self.assertEqual(active_period["type"], "Active")
        self.assertEqual(
            active_period["session_active_comments"],
            "active periods comment",
            "Active period should show session_active_comments",
        )
        self.assertEqual(
            active_period["session_break_idle_comments"],
            "",
            "Active period should NOT show session_break_idle_comments",
        )
        self.assertEqual(
            active_period["session_notes"],
            "session notes",
            "Active period should show session_notes",
        )

        # Break period: Should show break comments and session notes, but NOT active/idle comments
        break_period = timeline_data[1]
        self.assertEqual(break_period["type"], "Break")
        self.assertEqual(
            break_period["session_active_comments"],
            "",
            "Break period should NOT show session_active_comments",
        )
        self.assertEqual(
            break_period["session_break_idle_comments"],
            "break periods comment",
            "Break period should show break notes in session_break_idle_comments",
        )
        self.assertEqual(
            break_period["session_notes"],
            "session notes",
            "Break period should show session_notes",
        )

        # Idle period: Should show idle comments and session notes, but NOT active/break comments
        idle_period = timeline_data[2]
        self.assertEqual(idle_period["type"], "Idle")
        self.assertEqual(
            idle_period["session_active_comments"],
            "",
            "Idle period should NOT show session_active_comments",
        )
        self.assertEqual(
            idle_period["session_break_idle_comments"],
            "idle periods comment",
            "Idle period should show idle notes in session_break_idle_comments",
        )
        self.assertEqual(
            idle_period["session_notes"],
            "session notes",
            "Idle period should show session_notes",
        )


class TestAnalysisTimelineHeaderAlignment(unittest.TestCase):
    """Test that timeline header columns are properly aligned with data rows"""

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
                "Project A": {"sphere": "Work", "is_default": True, "active": True}
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_header_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_header_data.json"
        )

    def test_header_columns_align_with_data_rows(self):
        """
        BUG: Timeline header columns should align with data row columns.
        This test verifies that:
        1. Header count matches data column count
        2. Header widths match data column widths
        3. Both use the same packing parameters (anchor, padx, pady, font)

        This test does NOT hardcode header values - it dynamically verifies
        that whatever headers exist align properly with data columns.
        """
        date = "2026-01-29"
        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "start_timestamp": 1234567890,
                "end_timestamp": 1234570890,
                "total_duration": 3000,
                "active_duration": 3000,
                "active": [
                    {
                        "duration": 3000,
                        "project": "Project A",
                        "comment": "Working",
                        "start": "10:30:00",
                        "start_timestamp": 1234567890,
                    }
                ],
                "breaks": [],
                "idle_periods": [],
                "session_comments": {
                    "active_notes": "active comment",
                    "break_notes": "",
                    "idle_notes": "",
                    "session_notes": "session note",
                },
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Update the display to create header and data rows
        frame.update_timeline()

        # Get all header labels
        header_labels = [
            w
            for w in frame.timeline_header_frame.winfo_children()
            if isinstance(w, tk.Label)
        ]

        # Get all data row labels from first row
        data_rows = [
            w for w in frame.timeline_frame.winfo_children() if isinstance(w, tk.Frame)
        ]
        self.assertGreater(len(data_rows), 0, "Should have at least one data row")

        first_row = data_rows[0]
        data_labels = [w for w in first_row.winfo_children() if isinstance(w, tk.Label)]

        # Verify header count matches data column count
        self.assertEqual(
            len(header_labels),
            len(data_labels),
            f"Header count ({len(header_labels)}) should match data column count ({len(data_labels)})",
        )

        # Verify each header aligns with corresponding data column
        for idx, (header_label, data_label) in enumerate(
            zip(header_labels, data_labels)
        ):
            # Remove sort indicators from header text for display in error messages
            header_text = header_label.cget("text").replace(" ▼", "").replace(" ▲", "")

            # Verify header width matches data column width
            header_width = header_label.cget("width")
            data_width = data_label.cget("width")

            self.assertEqual(
                header_width,
                data_width,
                f"Column {idx} ('{header_text}'): header width ({header_width}) should match data width ({data_width})",
            )

            # Verify both use same anchor
            self.assertEqual(
                header_label.cget("anchor"),
                data_label.cget("anchor"),
                f"Column {idx} ('{header_text}'): header and data should have same anchor",
            )

            # Verify both use same padx
            self.assertEqual(
                header_label.cget("padx"),
                data_label.cget("padx"),
                f"Column {idx} ('{header_text}'): header and data should have same padx",
            )

            # BUG: Headers should NOT have pady while data labels don't
            # This causes visual misalignment
            header_pady = header_label.cget("pady")
            data_pady = data_label.cget("pady")

            self.assertEqual(
                header_pady,
                data_pady,
                f"Column {idx} ('{header_text}'): header pady ({header_pady}) should match data pady ({data_pady})",
            )

            # BUG: Headers MUST use same font as data for visual alignment
            # Headers should NOT be bold because that makes them wider than data
            header_font = str(header_label.cget("font")).lower()

            self.assertNotIn(
                "bold",
                header_font,
                f"Column {idx} ('{header_text}'): header should NOT use bold font (causes visual width mismatch)",
            )


if __name__ == "__main__":
    unittest.main()
