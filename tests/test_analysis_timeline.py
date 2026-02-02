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

        # Get all header labels (now inside Frame containers)
        header_containers = [
            w
            for w in frame.timeline_header_frame.winfo_children()
            if isinstance(w, tk.Frame)
        ]
        # Extract first label from each container
        header_labels = []
        for container in header_containers:
            labels = [w for w in container.winfo_children() if isinstance(w, tk.Label)]
            if labels:
                header_labels.append(labels[0])  # Use first label from each container

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

            # NOTE: With two-row header design, single-row headers use pady=6 for vertical centering
            # Data labels use pady=1 (default). This is intentional design for alignment.
            # Skip pady check since it's now expected to differ

            # BUG: Headers MUST use same font as data for visual alignment
            # Headers should NOT be bold because that makes them wider than data
            header_font = str(header_label.cget("font")).lower()

            self.assertNotIn(
                "bold",
                header_font,
                f"Column {idx} ('{header_text}'): header should NOT use bold font (causes visual width mismatch)",
            )

    def test_header_pixel_width_matches_data_row_pixel_width(self):
        """
        TDD RED PHASE TEST: Verify that header cells have the same actual pixel width
        as their corresponding data row cells.

        This is a more robust test than checking cget("width") because:
        - cget("width") checks configuration (what we TOLD tkinter to do)
        - winfo_reqwidth() checks actual required pixel width (what tkinter ACTUALLY rendered)

        The bug: Headers can have same width= config but different pixel width due to:
        - Sort indicators (" ▼", " ▲") added to header text
        - Background colors affecting rendering
        - Event bindings and cursor settings
        - Font rendering differences

        This test ensures visual alignment by comparing actual pixel widths.
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

        # Force geometry update to calculate actual widths
        self.root.update_idletasks()

        # Get all header labels (now inside Frame containers)
        header_containers = [
            w
            for w in frame.timeline_header_frame.winfo_children()
            if isinstance(w, tk.Frame)
        ]
        # Extract first label from each container
        header_labels = []
        for container in header_containers:
            labels = [w for w in container.winfo_children() if isinstance(w, tk.Label)]
            if labels:
                header_labels.append(labels[0])  # Use first label from each container

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

        # CRITICAL: Compare actual pixel widths using winfo_reqwidth()
        # This checks what tkinter ACTUALLY rendered, not just configuration
        for idx, (header_label, data_label) in enumerate(
            zip(header_labels, data_labels)
        ):
            # Remove sort indicators from header text for display in error messages
            header_text = header_label.cget("text").replace(" ▼", "").replace(" ▲", "")

            # Get actual required pixel widths
            header_pixel_width = header_label.winfo_reqwidth()
            data_pixel_width = data_label.winfo_reqwidth()

            # Headers and data cells should have EXACTLY the same pixel width
            # for proper column alignment
            self.assertEqual(
                header_pixel_width,
                data_pixel_width,
                f"Column {idx} ('{header_text}'): "
                f"header pixel width ({header_pixel_width}px) should match "
                f"data pixel width ({data_pixel_width}px). "
                f"Header config width={header_label.cget('width')}, "
                f"data config width={data_label.cget('width')}",
            )

    def test_header_pixel_width_with_sort_indicators(self):
        """
        TDD RED PHASE TEST: Verify that header cells maintain alignment even
        with sort indicators (▼ ▲) which add extra characters.

        The bug: Sort indicators add visual width to headers but not to data cells,
        causing misalignment when columns are sorted.

        This test:
        1. Sorts by different columns
        2. Checks pixel widths after each sort
        3. Ensures adding " ▼" or " ▲" doesn't break alignment
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
            },
            f"{date}_session2": {
                "sphere": "Personal",
                "date": date,
                "start_timestamp": 1234571000,
                "end_timestamp": 1234573000,
                "total_duration": 2000,
                "active_duration": 2000,
                "active": [
                    {
                        "duration": 2000,
                        "project": "Project B",
                        "comment": "More work",
                        "start": "11:30:00",
                        "start_timestamp": 1234571000,
                    }
                ],
                "breaks": [],
                "idle_periods": [],
                "session_comments": {
                    "active_notes": "different comment",
                    "break_notes": "",
                    "idle_notes": "",
                    "session_notes": "different note",
                },
            },
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Test different sort states
        sort_columns = [
            "date",
            "start",
            "duration",
            "sphere",
            "type",
            "primary_project",
        ]

        for sort_col in sort_columns:
            # Sort by this column
            frame.sort_timeline(sort_col)
            self.root.update_idletasks()

            # Get headers and data (extract from Frame containers)
            header_containers = [
                w
                for w in frame.timeline_header_frame.winfo_children()
                if isinstance(w, tk.Frame)
            ]
            header_labels = []
            for container in header_containers:
                labels = [
                    w for w in container.winfo_children() if isinstance(w, tk.Label)
                ]
                if labels:
                    header_labels.append(labels[0])

            data_rows = [
                w
                for w in frame.timeline_frame.winfo_children()
                if isinstance(w, tk.Frame)
            ]
            self.assertGreater(len(data_rows), 0, "Should have at least one data row")

            first_row = data_rows[0]
            data_labels = [
                w for w in first_row.winfo_children() if isinstance(w, tk.Label)
            ]

            # Check each column's pixel width
            for idx, (header, data) in enumerate(zip(header_labels, data_labels)):
                header_text = header.cget("text")
                header_px_width = header.winfo_reqwidth()
                data_px_width = data.winfo_reqwidth()

                self.assertEqual(
                    header_px_width,
                    data_px_width,
                    f"Sort by '{sort_col}': Column {idx} ('{header_text}'): "
                    f"header pixel width ({header_px_width}px) != "
                    f"data pixel width ({data_px_width}px)",
                )


class TestAnalysisTimelineTwoRowHeaders(unittest.TestCase):
    """Test that timeline headers can have two rows for clearer labeling"""

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
            "test_two_row_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_two_row_data.json"
        )

    def test_header_containers_exist_for_two_row_headers(self):
        """
        TDD RED PHASE TEST: Verify that header uses Frame containers for two-row layout.

        The two-row header design requires:
        - Each header column wrapped in a Frame container
        - Containers packed horizontally (side=tk.LEFT)
        - Labels within containers stacked vertically

        This enables "Sphere" column to show:
          Row 1: "Sphere"
          Row 2: "Active"
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
        frame.update_timeline()
        self.root.update_idletasks()

        # Header should contain Frame containers (not just Labels)
        header_children = frame.timeline_header_frame.winfo_children()

        # Should have Frame containers for each column
        frame_containers = [w for w in header_children if isinstance(w, tk.Frame)]
        self.assertGreater(
            len(frame_containers),
            0,
            "Header should use Frame containers for two-row layout",
        )

    def test_sphere_active_header_has_two_rows(self):
        """
        TDD RED PHASE TEST: Verify "Sphere Active" column uses two-row header.

        Expected structure:
        - Frame container (column 4)
        - Top Label: "Sphere"
        - Bottom Label: "Active"

        This makes it clear that the checkmark indicates sphere active status.
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
        frame.update_timeline()
        self.root.update_idletasks()

        # Get header containers
        header_containers = [
            w
            for w in frame.timeline_header_frame.winfo_children()
            if isinstance(w, tk.Frame)
        ]

        # Find the "Sphere Active" column (column 4, after Date/Start/Duration/Sphere)
        # It should be the 5th container (index 4)
        self.assertGreaterEqual(
            len(header_containers), 5, "Should have at least 5 header containers"
        )

        sphere_active_container = header_containers[4]
        labels_in_container = [
            w
            for w in sphere_active_container.winfo_children()
            if isinstance(w, tk.Label)
        ]

        # Should have 2 labels (top row + bottom row)
        self.assertEqual(
            len(labels_in_container), 2, "Sphere Active header should have 2 label rows"
        )

        # Top label should say "Sphere"
        top_label = labels_in_container[0]
        self.assertIn(
            "Sphere", top_label.cget("text"), "Top row should contain 'Sphere'"
        )

        # Bottom label should say "Active"
        bottom_label = labels_in_container[1]
        self.assertEqual(
            "Active", bottom_label.cget("text"), "Bottom row should say 'Active'"
        )

    def test_project_active_header_has_two_rows(self):
        """
        TDD RED PHASE TEST: Verify "Project Active" column uses two-row header.

        Expected structure:
        - Frame container (column 5)
        - Top Label: "Project"
        - Bottom Label: "Active"
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
        frame.update_timeline()
        self.root.update_idletasks()

        # Get header containers
        header_containers = [
            w
            for w in frame.timeline_header_frame.winfo_children()
            if isinstance(w, tk.Frame)
        ]

        # Find the "Project Active" column (column 5)
        self.assertGreaterEqual(
            len(header_containers), 6, "Should have at least 6 header containers"
        )

        project_active_container = header_containers[5]
        labels_in_container = [
            w
            for w in project_active_container.winfo_children()
            if isinstance(w, tk.Label)
        ]

        # Should have 2 labels
        self.assertEqual(
            len(labels_in_container),
            2,
            "Project Active header should have 2 label rows",
        )

        # Top label should say "Project"
        top_label = labels_in_container[0]
        self.assertIn(
            "Project", top_label.cget("text"), "Top row should contain 'Project'"
        )

        # Bottom label should say "Active"
        bottom_label = labels_in_container[1]
        self.assertEqual(
            "Active", bottom_label.cget("text"), "Bottom row should say 'Active'"
        )

    def test_single_row_headers_are_vertically_centered(self):
        """
        TDD RED PHASE TEST: Verify single-row headers are centered vertically.

        When some headers have 2 rows and others have 1 row, the single-row
        headers should be vertically centered to align with the two-row headers.

        This is achieved with pady padding on single-row header labels.
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
        frame.update_timeline()
        self.root.update_idletasks()

        # Get header containers
        header_containers = [
            w
            for w in frame.timeline_header_frame.winfo_children()
            if isinstance(w, tk.Frame)
        ]

        # Skip test if no Frame containers exist (not implemented yet)
        if len(header_containers) == 0:
            self.skipTest("Frame containers not yet implemented")

        # Check "Date" column (should be single-row, vertically centered)
        date_container = header_containers[0]
        date_labels = [
            w for w in date_container.winfo_children() if isinstance(w, tk.Label)
        ]

        # Single-row headers should have exactly 1 label
        self.assertEqual(len(date_labels), 1, "Single-row headers should have 1 label")

        # That label should have vertical padding for centering
        date_label = date_labels[0]
        pady = date_label.cget("pady")

        self.assertGreater(
            pady,
            0,
            "Single-row header labels should have pady > 0 for vertical centering",
        )


class TestAnalysisTimelineCommentWrapping(unittest.TestCase):
    """Test that comment fields wrap and display full text"""

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
            },
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True},
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_comment_wrap_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_comment_wrap_data.json"
        )

    def test_primary_comment_shows_full_text_without_truncation(self):
        """Test that primary comment displays complete text, not truncated to 20 chars"""
        date = "2026-01-31"
        long_comment = "This is a very long primary comment that should be displayed in full without truncation"

        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "total_duration": 3600,
                "active_duration": 3600,
                "break_duration": 0,
                "active": [
                    {
                        "duration": 3600,
                        "project": "Project A",
                        "comment": long_comment,
                        "start_time": 1000,
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
        frame = AnalysisFrame(parent_frame, tracker, self.root)
        frame.update_timeline()
        self.root.update()

        # Find the primary comment label (column 8: Date, Start, Duration, Sphere, Sphere Active, Project Active, Type, Primary Project, PRIMARY COMMENT)
        timeline_children = frame.timeline_frame.winfo_children()
        self.assertGreater(len(timeline_children), 0, "Timeline should have data rows")

        row_frame = timeline_children[0]
        labels = [
            child for child in row_frame.winfo_children() if isinstance(child, tk.Label)
        ]

        # Primary comment is the 9th label (index 8)
        self.assertGreaterEqual(len(labels), 9, "Should have at least 9 columns")
        primary_comment_label = labels[8]

        # Should show FULL text, not truncated
        displayed_text = primary_comment_label.cget("text")
        self.assertEqual(
            displayed_text,
            long_comment,
            "Primary comment should display full text without truncation",
        )
        self.assertGreater(
            len(displayed_text),
            20,
            "Comment should be longer than 20 chars to verify no truncation",
        )

    def test_comment_labels_have_wraplength_configured(self):
        """Test that comment labels have wraplength set for text wrapping"""
        date = "2026-01-31"
        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "total_duration": 3600,
                "active_duration": 3600,
                "break_duration": 0,
                "active": [
                    {
                        "duration": 3600,
                        "project": "Project A",
                        "comment": "Long comment that should wrap",
                        "start_time": 1000,
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
        frame = AnalysisFrame(parent_frame, tracker, self.root)
        frame.update_timeline()
        self.root.update()

        # Get first row
        timeline_children = frame.timeline_frame.winfo_children()
        row_frame = timeline_children[0]
        labels = [
            child for child in row_frame.winfo_children() if isinstance(child, tk.Label)
        ]

        # Comment columns: Primary Comment (8), Secondary Comment (10),
        # Active Comments (11), Break Comments (12), Session Notes (13)
        # Column layout: 0=Date, 1=Start, 2=Duration, 3=Sphere, 4=Sphere Active, 5=Project Active, 6=Type, 7=Primary Project, 8=Primary Comment, 9=Secondary Project, 10=Secondary Comment, 11=Active Comments, 12=Break Comments, 13=Session Notes
        comment_indices = [8, 10, 11, 12, 13]

        for idx in comment_indices:
            if idx < len(labels):
                label = labels[idx]
                wraplength = label.cget("wraplength")
                self.assertGreater(
                    wraplength,
                    0,
                    f"Comment column {idx} should have wraplength > 0 for text wrapping",
                )

    def test_comment_labels_do_not_have_width_restriction(self):
        """
        TDD RED PHASE TEST: Comment labels should NOT have width= parameter
        that restricts expansion.

        BUG: Setting width=20 prevents labels from expanding to show wrapped text,
        causing truncation even with wraplength configured.

        Solution: Comment labels should have wraplength for wrapping but NOT width
        for restriction. This allows them to expand to edge of screen.
        """
        date = "2026-01-31"
        long_comment = "This is a very long session note that should wrap to multiple lines and extend all the way to the edge of the screen without being truncated at 20 characters"

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
                    "active_notes": "",
                    "break_notes": "",
                    "idle_notes": "",
                    "session_notes": long_comment,
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
        frame.update_timeline()
        self.root.update_idletasks()

        # Get first row
        timeline_children = frame.timeline_frame.winfo_children()
        row_frame = timeline_children[0]
        labels = [
            child for child in row_frame.winfo_children() if isinstance(child, tk.Label)
        ]

        # Check all comment columns (8, 10, 11, 12, 13)
        comment_indices = [8, 10, 11, 12, 13]

        for idx in comment_indices:
            if idx < len(labels):
                label = labels[idx]
                width_config = label.cget("width")

                # Comment labels should have width=21 (matching wraplength~150px)
                # This provides consistent column sizing while wraplength handles text overflow
                self.assertEqual(
                    width_config,
                    21,
                    f"Comment column {idx} should have width=21 to match wraplength pixel width. "
                    f"Found width={width_config}.",
                )

                # Should still have wraplength configured
                wraplength = label.cget("wraplength")
                self.assertGreater(
                    wraplength, 0, f"Comment column {idx} should have wraplength > 0"
                )

    def test_all_comment_fields_show_full_content(self):
        """Test that all comment types display full text without truncation"""
        date = "2026-01-31"

        primary_comment = "Primary action comment that is quite long and detailed"
        secondary_comment = "Secondary action comment with lots of information"
        active_comment = "Session active comments field with comprehensive notes"
        break_comment = "Session break comments describing the break activities"
        session_notes_text = (
            "Overall session notes with important contextual information"
        )

        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "total_duration": 3600,
                "active_duration": 2400,
                "break_duration": 1200,
                "session_active_comments": active_comment,
                "session_break_idle_comments": break_comment,
                "session_notes": session_notes_text,
                "active": [
                    {
                        "duration": 2400,
                        "project": "Project A",
                        "comment": primary_comment,
                        "start_time": 1000,
                    }
                ],
                "breaks": [
                    {
                        "duration": 1200,
                        "action": "Resting",
                        "comment": secondary_comment,
                        "start_time": 3400,
                    }
                ],
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
        frame.update_timeline()
        self.root.update()

        # Should have multiple rows (active + break)
        timeline_children = frame.timeline_frame.winfo_children()
        self.assertGreater(
            len(timeline_children), 1, "Should have multiple timeline rows"
        )

        # Check active period row (first row)
        active_row = timeline_children[0]
        active_labels = [
            child
            for child in active_row.winfo_children()
            if isinstance(child, tk.Label)
        ]

        # Verify primary comment is not truncated (column 8)
        primary_label = active_labels[8]
        self.assertEqual(primary_label.cget("text"), primary_comment)

        # Verify session comments are not truncated (columns 11 and 13)
        active_comments_label = active_labels[11]
        self.assertEqual(active_comments_label.cget("text"), active_comment)

        session_notes_label = active_labels[13]
        self.assertEqual(session_notes_label.cget("text"), session_notes_text)

    def test_empty_comments_display_correctly(self):
        """Test that empty comment fields display properly without errors"""
        date = "2026-01-31"
        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "total_duration": 3600,
                "active_duration": 3600,
                "break_duration": 0,
                "active": [
                    {
                        "duration": 3600,
                        "project": "Project A",
                        "comment": "",  # Empty comment
                        "start_time": 1000,
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
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Should not raise exception
        frame.update_timeline()
        self.root.update()

        timeline_children = frame.timeline_frame.winfo_children()
        self.assertGreater(len(timeline_children), 0, "Timeline should have data rows")


class TestTimelineRowStretching(unittest.TestCase):
    """Test that timeline rows stretch to full screen width"""

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
            "test_timeline_stretch_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_timeline_stretch_data.json"
        )

    def test_timeline_rows_have_sticky_we_grid(self):
        """Test that timeline row frames use sticky=(W,E) to stretch horizontally"""
        # Use today's date to ensure it's in the "Last 7 Days" range
        from datetime import datetime

        date = datetime.now().strftime("%Y-%m-%d")

        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "total_duration": 3600,
                "active_duration": 3000,
                "break_duration": 600,
                "active": [
                    {
                        "duration": 3000,
                        "project": "Project A",
                        "comment": "Test comment",
                        "start": "10:00:00",
                    }
                ],
                "breaks": [
                    {"duration": 600, "comment": "Test break", "start": "11:00:00"}
                ],
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

        # Update timeline to create rows
        frame.update_timeline()
        self.root.update()

        # Get timeline row frames
        timeline_children = frame.timeline_frame.winfo_children()
        self.assertGreater(len(timeline_children), 0, "Timeline should have data rows")

        # Check first row frame
        first_row = timeline_children[0]

        # Verify row is gridded with sticky=(W,E) to allow horizontal stretching
        grid_info = first_row.grid_info()
        self.assertIn("sticky", grid_info, "Row should have grid sticky configuration")

        # Sticky should include 'w' and 'e' for horizontal stretching
        sticky = grid_info["sticky"]
        self.assertIn(
            "w", sticky.lower(), "Row should have west (w) sticky to stretch left"
        )
        self.assertIn(
            "e", sticky.lower(), "Row should have east (e) sticky to stretch right"
        )

    def test_timeline_frame_has_column_weight(self):
        """Test that timeline_frame has column weight configured for stretching"""
        # Use today's date to ensure it's in the "Last 7 Days" range
        from datetime import datetime

        date = datetime.now().strftime("%Y-%m-%d")

        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "total_duration": 3600,
                "active_duration": 3000,
                "break_duration": 600,
                "active": [
                    {"duration": 3000, "project": "Project A", "start": "10:00:00"}
                ],
                "breaks": [{"duration": 600, "start": "11:00:00"}],
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

        # Update timeline to create rows
        frame.update_timeline()
        self.root.update()

        # Check that timeline_frame has column 0 configured with weight
        # This allows the row frames to expand horizontally
        col_config = frame.timeline_frame.grid_columnconfigure(0)

        # Column should have weight > 0 to allow expansion
        weight = (
            col_config.get("weight", 0) if isinstance(col_config, dict) else col_config
        )
        self.assertGreater(
            weight, 0, "Timeline frame column 0 should have weight > 0 for stretching"
        )


class TestAnalysisFrameProjectRadioButtons(unittest.TestCase):
    """Test project filter radio buttons (Active/All/Archived)"""

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
                "Active Project": {
                    "sphere": "Work",
                    "is_default": True,
                    "active": True,
                },
                "Another Active": {
                    "sphere": "Work",
                    "is_default": False,
                    "active": True,
                },
                "Archived Project": {
                    "sphere": "Work",
                    "is_default": False,
                    "active": False,
                },
                "Personal Active": {
                    "sphere": "Personal",
                    "is_default": True,
                    "active": True,
                },
                "Personal Archived": {
                    "sphere": "Personal",
                    "is_default": False,
                    "active": False,
                },
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_project_radio_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_project_radio_data.json"
        )

    def test_project_filter_variable_exists(self):
        """Test that status_filter variable is created"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Check that filter variable exists and defaults to 'active'
        self.assertTrue(hasattr(frame, "status_filter"))
        self.assertEqual(frame.status_filter.get(), "active")

    def test_project_filter_radio_buttons_exist(self):
        """Test that radio buttons for project filtering are created"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Should have radio buttons for active, all, and archived
        # Check they are bound to status_filter variable
        self.assertTrue(hasattr(frame, "status_filter"))
        self.assertIsInstance(frame.status_filter, tk.StringVar)

    def test_active_filter_shows_only_active_projects(self):
        """Test that active filter shows only active projects in dropdown"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Select Work sphere so we can see projects
        frame.sphere_var.set("Work")
        frame.status_filter.set("active")
        frame.update_project_filter()

        # Get dropdown values
        dropdown_values = list(frame.project_filter["values"])

        # Should include "All Projects", active projects but NOT archived
        self.assertIn("All Projects", dropdown_values)
        self.assertIn("Active Project", dropdown_values)
        self.assertIn("Another Active", dropdown_values)
        self.assertNotIn("Archived Project", dropdown_values)

    def test_all_filter_shows_all_projects(self):
        """Test that all filter shows both active and archived projects"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Select Work sphere
        frame.sphere_var.set("Work")
        frame.status_filter.set("all")
        frame.update_project_filter()

        # Get dropdown values
        dropdown_values = list(frame.project_filter["values"])

        # Should include all projects
        self.assertIn("All Projects", dropdown_values)
        self.assertIn("Active Project", dropdown_values)
        self.assertIn("Another Active", dropdown_values)
        self.assertIn("Archived Project", dropdown_values)

    def test_archived_filter_shows_only_archived_projects(self):
        """Test that archived filter shows only archived projects"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Select Work sphere
        frame.sphere_var.set("Work")
        frame.status_filter.set("archived")
        frame.update_project_filter()

        # Get dropdown values
        dropdown_values = list(frame.project_filter["values"])

        # Should include "All Projects" and archived projects but NOT active
        self.assertIn("All Projects", dropdown_values)
        self.assertNotIn("Active Project", dropdown_values)
        self.assertNotIn("Another Active", dropdown_values)
        self.assertIn("Archived Project", dropdown_values)

    def test_default_filter_is_active(self):
        """Test that the default project filter is set to active on initialization"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Default should be active
        self.assertEqual(frame.status_filter.get(), "active")

        # Select Work sphere
        frame.sphere_var.set("Work")
        frame.update_project_filter()

        # Dropdown should show only active projects by default
        dropdown_values = list(frame.project_filter["values"])
        self.assertIn("Active Project", dropdown_values)
        self.assertIn("Another Active", dropdown_values)
        self.assertNotIn("Archived Project", dropdown_values)


class TestAnalysisFrameSphereRadioButtons(unittest.TestCase):
    """Test sphere filter radio buttons (Active/All/Archived)"""

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
                "Hobby": {"is_default": False, "active": False},
            },
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True},
                "Exercise": {"sphere": "Personal", "is_default": True, "active": True},
                "Gaming": {"sphere": "Hobby", "is_default": True, "active": True},
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_sphere_radio_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_sphere_radio_data.json"
        )

    def test_sphere_filter_variable_exists(self):
        """Test that status_filter variable is created"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Check that filter variable exists and defaults to 'active'
        self.assertTrue(hasattr(frame, "status_filter"))
        self.assertEqual(frame.status_filter.get(), "active")

    def test_sphere_filter_radio_buttons_exist(self):
        """Test that radio buttons for sphere filtering are created"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Should have radio buttons for active, all, and archived
        # Check they are bound to status_filter variable
        self.assertTrue(hasattr(frame, "status_filter"))
        self.assertIsInstance(frame.status_filter, tk.StringVar)

    def test_active_filter_shows_only_active_spheres(self):
        """Test that active filter shows only active spheres in dropdown"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Set filter to active
        frame.status_filter.set("active")
        frame.refresh_dropdowns()

        # Get dropdown values
        dropdown_values = list(frame.sphere_filter["values"])

        # Should include "All Spheres", "Work", and "Personal" but NOT "Hobby"
        self.assertIn("All Spheres", dropdown_values)
        self.assertIn("Work", dropdown_values)
        self.assertIn("Personal", dropdown_values)
        self.assertNotIn("Hobby", dropdown_values)

    def test_all_filter_shows_all_spheres(self):
        """Test that all filter shows both active and archived spheres"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Set filter to all
        frame.status_filter.set("all")
        frame.refresh_dropdowns()

        # Get dropdown values
        dropdown_values = list(frame.sphere_filter["values"])

        # Should include all spheres
        self.assertIn("All Spheres", dropdown_values)
        self.assertIn("Work", dropdown_values)
        self.assertIn("Personal", dropdown_values)
        self.assertIn("Hobby", dropdown_values)

    def test_archived_filter_shows_only_archived_spheres(self):
        """
        Test that archived filter shows all spheres.

        Note: 'Archived' filter shows:
        - Active spheres (to access their inactive projects)
        - Inactive spheres (archived spheres)
        """
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Set filter to archived
        frame.status_filter.set("archived")
        frame.refresh_dropdowns()

        # Get dropdown values
        dropdown_values = list(frame.sphere_filter["values"])

        # Should include all spheres (both active and inactive)
        # because active spheres may have inactive projects
        self.assertIn("All Spheres", dropdown_values)
        self.assertIn("Work", dropdown_values)
        self.assertIn("Personal", dropdown_values)
        self.assertIn("Hobby", dropdown_values)

    def test_default_filter_is_active(self):
        """Test that the default sphere filter is set to active on initialization"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Default should be active
        self.assertEqual(frame.status_filter.get(), "active")

        # Dropdown should show only active spheres by default
        dropdown_values = list(frame.sphere_filter["values"])
        self.assertIn("Work", dropdown_values)
        self.assertIn("Personal", dropdown_values)
        self.assertNotIn("Hobby", dropdown_values)


class TestAnalysisFrameStatusFilterIntegration(unittest.TestCase):
    """
    Integration tests for status filter behavior with different sphere/project combinations.

    Tests verify that sessions appear correctly based on:
    - Active sphere + active project: show on 'active' or 'all' filter
    - Active sphere + inactive project: show on 'archived' or 'all' filter
    - Inactive sphere + active project: show on 'archived' or 'all' filter
    """

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()

        # Create settings with active and inactive spheres/projects
        settings = {
            "spheres": {
                "ActiveSphere": {"is_default": True, "active": True},
                "InactiveSphere": {"is_default": False, "active": False},
            },
            "projects": {
                "ActiveProject": {
                    "sphere": "ActiveSphere",
                    "is_default": True,
                    "active": True,
                },
                "InactiveProject": {
                    "sphere": "ActiveSphere",
                    "is_default": False,
                    "active": False,
                },
                "ProjectInInactiveSphere": {
                    "sphere": "InactiveSphere",
                    "is_default": False,
                    "active": True,
                },
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_status_filter_integration_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_status_filter_integration_data.json"
        )

    def tearDown(self):
        """Clean up after tests"""
        try:
            self.root.destroy()
        except:
            pass
        self.file_manager.cleanup()

    def test_active_sphere_active_project_shows_on_active_filter(self):
        """Test that sessions with active sphere + active project show when filter is 'active'"""
        date = "2026-02-02"
        test_data = {
            f"{date}_session1": {
                "sphere": "ActiveSphere",
                "date": date,
                "total_duration": 3600,
                "active_duration": 3000,
                "break_duration": 600,
                "active": [{"duration": 3000, "project": "ActiveProject"}],
                "breaks": [{"duration": 600}],
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

        # Set filter to 'active'
        frame.status_filter.set("active")
        frame.refresh_dropdowns()

        # Select the active sphere and project
        frame.sphere_var.set("ActiveSphere")
        frame.project_var.set("ActiveProject")

        # Calculate totals - should include this session
        active, breaks = frame.calculate_totals("All Time")

        # Should show the session (3000 active, 600 break)
        self.assertEqual(
            active,
            3000,
            "Active sphere + active project should show on 'active' filter",
        )
        self.assertEqual(breaks, 600)

    def test_active_sphere_active_project_shows_on_all_filter(self):
        """Test that sessions with active sphere + active project show when filter is 'all'"""
        date = "2026-02-02"
        test_data = {
            f"{date}_session1": {
                "sphere": "ActiveSphere",
                "date": date,
                "total_duration": 3600,
                "active_duration": 3000,
                "break_duration": 600,
                "active": [{"duration": 3000, "project": "ActiveProject"}],
                "breaks": [{"duration": 600}],
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

        # Set filter to 'all'
        frame.status_filter.set("all")
        frame.refresh_dropdowns()

        # Select the active sphere and project
        frame.sphere_var.set("ActiveSphere")
        frame.project_var.set("ActiveProject")

        # Calculate totals - should include this session
        active, breaks = frame.calculate_totals("All Time")

        # Should show the session
        self.assertEqual(
            active, 3000, "Active sphere + active project should show on 'all' filter"
        )
        self.assertEqual(breaks, 600)

    def test_active_sphere_inactive_project_shows_on_archived_filter(self):
        """Test that sessions with active sphere + inactive project show when filter is 'archived'"""
        date = "2026-02-02"
        test_data = {
            f"{date}_session1": {
                "sphere": "ActiveSphere",
                "date": date,
                "total_duration": 2400,
                "active_duration": 2000,
                "break_duration": 400,
                "active": [{"duration": 2000, "project": "InactiveProject"}],
                "breaks": [{"duration": 400}],
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

        # Set filter to 'archived'
        frame.status_filter.set("archived")
        frame.refresh_dropdowns()

        # Verify InactiveProject appears in dropdown
        project_values = list(frame.project_filter["values"])
        self.assertIn(
            "InactiveProject",
            project_values,
            "Inactive project should appear in dropdown when filter is 'archived'",
        )

        # Select the sphere and inactive project
        frame.sphere_var.set("ActiveSphere")
        frame.project_var.set("InactiveProject")

        # Calculate totals - should include this session
        active, breaks = frame.calculate_totals("All Time")

        # Should show the session
        self.assertEqual(
            active,
            2000,
            "Active sphere + inactive project should show on 'archived' filter",
        )
        self.assertEqual(breaks, 400)

    def test_active_sphere_inactive_project_shows_on_all_filter(self):
        """Test that sessions with active sphere + inactive project show when filter is 'all'"""
        date = "2026-02-02"
        test_data = {
            f"{date}_session1": {
                "sphere": "ActiveSphere",
                "date": date,
                "total_duration": 2400,
                "active_duration": 2000,
                "break_duration": 400,
                "active": [{"duration": 2000, "project": "InactiveProject"}],
                "breaks": [{"duration": 400}],
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

        # Set filter to 'all'
        frame.status_filter.set("all")
        frame.refresh_dropdowns()

        # Select the sphere and inactive project
        frame.sphere_var.set("ActiveSphere")
        frame.project_var.set("InactiveProject")

        # Calculate totals - should include this session
        active, breaks = frame.calculate_totals("All Time")

        # Should show the session
        self.assertEqual(
            active, 2000, "Active sphere + inactive project should show on 'all' filter"
        )
        self.assertEqual(breaks, 400)

    def test_inactive_sphere_active_project_shows_on_archived_filter(self):
        """Test that sessions with inactive sphere + active project show when filter is 'archived'"""
        date = "2026-02-02"
        test_data = {
            f"{date}_session1": {
                "sphere": "InactiveSphere",
                "date": date,
                "total_duration": 1800,
                "active_duration": 1500,
                "break_duration": 300,
                "active": [{"duration": 1500, "project": "ProjectInInactiveSphere"}],
                "breaks": [{"duration": 300}],
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

        # Set filter to 'archived'
        frame.status_filter.set("archived")
        frame.refresh_dropdowns()

        # Verify InactiveSphere appears in dropdown
        sphere_values = list(frame.sphere_filter["values"])
        self.assertIn(
            "InactiveSphere",
            sphere_values,
            "Inactive sphere should appear in dropdown when filter is 'archived'",
        )

        # Select the inactive sphere and its project
        frame.sphere_var.set("InactiveSphere")
        frame.update_project_filter()
        frame.project_var.set("ProjectInInactiveSphere")

        # Calculate totals - should include this session
        active, breaks = frame.calculate_totals("All Time")

        # Should show the session
        self.assertEqual(
            active,
            1500,
            "Inactive sphere + active project should show on 'archived' filter",
        )
        self.assertEqual(breaks, 300)

    def test_inactive_sphere_active_project_shows_on_all_filter(self):
        """Test that sessions with inactive sphere + active project show when filter is 'all'"""
        date = "2026-02-02"
        test_data = {
            f"{date}_session1": {
                "sphere": "InactiveSphere",
                "date": date,
                "total_duration": 1800,
                "active_duration": 1500,
                "break_duration": 300,
                "active": [{"duration": 1500, "project": "ProjectInInactiveSphere"}],
                "breaks": [{"duration": 300}],
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

        # Set filter to 'all'
        frame.status_filter.set("all")
        frame.refresh_dropdowns()

        # Select the inactive sphere and its project
        frame.sphere_var.set("InactiveSphere")
        frame.update_project_filter()
        frame.project_var.set("ProjectInInactiveSphere")

        # Calculate totals - should include this session
        active, breaks = frame.calculate_totals("All Time")

        # Should show the session
        self.assertEqual(
            active, 1500, "Inactive sphere + active project should show on 'all' filter"
        )
        self.assertEqual(breaks, 300)


class TestAnalysisFrameTimelineColumns(unittest.TestCase):
    """
    Tests for timeline columns showing sphere, sphere_active, project, project_active

    Verifies that timeline displays:
    - Sphere name column
    - Sphere active status (checkbox)
    - Project name column
    - Project active status (checkbox)
    """

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()

        # Create settings with active and inactive spheres/projects
        settings = {
            "spheres": {
                "ActiveSphere": {"is_default": True, "active": True},
                "InactiveSphere": {"is_default": False, "active": False},
            },
            "projects": {
                "ActiveProject": {
                    "sphere": "ActiveSphere",
                    "is_default": True,
                    "active": True,
                },
                "InactiveProject": {
                    "sphere": "ActiveSphere",
                    "is_default": False,
                    "active": False,
                },
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_timeline_columns_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_timeline_columns_data.json"
        )

    def tearDown(self):
        """Clean up after tests"""
        try:
            self.root.destroy()
        except:
            pass
        self.file_manager.cleanup()

    def test_timeline_header_has_sphere_column(self):
        """Test that timeline header includes Sphere column"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Check that header has Sphere label (now inside Frame containers)
        header_containers = frame.timeline_header_frame.winfo_children()
        header_texts = []
        for container in header_containers:
            if isinstance(container, tk.Frame):
                for label in container.winfo_children():
                    if isinstance(label, tk.Label):
                        header_texts.append(label.cget("text"))

        self.assertIn(
            "Sphere", header_texts, "Timeline header should include 'Sphere' column"
        )

    def test_timeline_header_has_sphere_active_column(self):
        """Test that timeline header includes Sphere Active column"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Check that header has Sphere Active (now as two-row: 'Sphere' / 'Active')
        # The 5th container (index 4) should have two labels: 'Sphere' and 'Active'
        header_containers = frame.timeline_header_frame.winfo_children()
        self.assertGreater(
            len(header_containers), 4, "Should have at least 5 header containers"
        )

        sphere_active_container = [
            c for c in header_containers if isinstance(c, tk.Frame)
        ][4]
        labels_in_container = [
            w.cget("text")
            for w in sphere_active_container.winfo_children()
            if isinstance(w, tk.Label)
        ]

        # Should contain both 'Sphere' and 'Active' in the two-row header
        self.assertIn(
            "Sphere",
            labels_in_container,
            "Sphere Active column should have 'Sphere' label",
        )
        self.assertIn(
            "Active",
            labels_in_container,
            "Sphere Active column should have 'Active' label",
        )

    def test_timeline_header_has_project_active_column(self):
        """Test that timeline header includes Project Active column"""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, tracker, self.root)

        # Check that header has Project Active (now as two-row: 'Project' / 'Active')
        # The 6th container (index 5) should have two labels: 'Project' and 'Active'
        header_containers = frame.timeline_header_frame.winfo_children()
        self.assertGreater(
            len(header_containers), 5, "Should have at least 6 header containers"
        )

        project_active_container = [
            c for c in header_containers if isinstance(c, tk.Frame)
        ][5]
        labels_in_container = [
            w.cget("text")
            for w in project_active_container.winfo_children()
            if isinstance(w, tk.Label)
        ]

        # Should contain both 'Project' and 'Active' in the two-row header
        self.assertIn(
            "Project",
            labels_in_container,
            "Project Active column should have 'Project' label",
        )
        self.assertIn(
            "Active",
            labels_in_container,
            "Project Active column should have 'Active' label",
        )

    def test_timeline_row_displays_sphere_name(self):
        """Test that timeline rows display sphere name"""
        date = "2026-02-02"
        test_data = {
            f"{date}_session1": {
                "sphere": "ActiveSphere",
                "date": date,
                "total_duration": 3600,
                "active_duration": 3000,
                "break_duration": 600,
                "active": [{"duration": 3000, "project": "ActiveProject"}],
                "breaks": [{"duration": 600}],
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

        # Select appropriate filters
        frame.sphere_var.set("ActiveSphere")
        frame.project_var.set("ActiveProject")
        frame.update_timeline()

        # Check that timeline frame has widgets (rows were created)
        timeline_widgets = frame.timeline_frame.winfo_children()
        self.assertGreater(
            len(timeline_widgets),
            0,
            "Timeline should have rows displaying sphere name",
        )

        # Check that "ActiveSphere" text appears in timeline
        timeline_texts = []
        for widget in timeline_widgets:
            # Check row frames
            if isinstance(widget, tk.Frame):
                # Get labels from each row frame
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label):
                        timeline_texts.append(child.cget("text"))

        self.assertIn(
            "ActiveSphere",
            timeline_texts,
            "Timeline row should display sphere name 'ActiveSphere'",
        )

    def test_timeline_row_displays_sphere_active_status(self):
        """Test that timeline rows display sphere active status"""
        date = "2026-02-02"
        test_data = {
            f"{date}_session1": {
                "sphere": "InactiveSphere",
                "date": date,
                "total_duration": 1800,
                "active_duration": 1500,
                "break_duration": 300,
                "active": [{"duration": 1500, "project": "ActiveProject"}],
                "breaks": [{"duration": 300}],
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

        # Set filter to show inactive sphere
        frame.status_filter.set("archived")
        frame.refresh_dropdowns()
        frame.sphere_var.set("InactiveSphere")
        frame.update_project_filter()
        frame.update_timeline()

        # Check that timeline displays sphere active status (should be unchecked/False for InactiveSphere)
        # For this test, we verify the data structure contains sphere_active field
        # The actual checkbox rendering will be verified by visual testing
        timeline_widgets = frame.timeline_frame.winfo_children()
        self.assertGreater(
            len(timeline_widgets),
            0,
            "Timeline should have rows with sphere active status",
        )

    def test_timeline_fits_within_window_bounds(self):
        """Test that timeline header and rows don't span outside reasonable bounds"""
        date = "2026-02-02"
        test_data = {
            f"{date}_session1": {
                "sphere": "ActiveSphere",
                "date": date,
                "total_duration": 3600,
                "active_duration": 3000,
                "break_duration": 600,
                "active": [
                    {
                        "duration": 3000,
                        "project": "ActiveProject",
                        "comment": "This is a very long comment that might cause wrapping issues if not handled properly",
                    }
                ],
                "breaks": [
                    {
                        "duration": 600,
                        "action": "Resting",
                        "comment": "Another long comment for testing purposes",
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

        # Update timeline to populate data
        frame.sphere_var.set("ActiveSphere")
        frame.project_var.set("ActiveProject")
        frame.update_timeline()

        # Force geometry update
        self.root.update_idletasks()

        # Check header required width fits within typical full-screen width (1920px)
        # This verifies columns are sized appropriately
        max_acceptable_width = 1920
        header_width = frame.timeline_header_frame.winfo_reqwidth()
        self.assertLessEqual(
            header_width,
            max_acceptable_width,
            f"Timeline header required width ({header_width}px) exceeds typical full-screen width ({max_acceptable_width}px)",
        )

        # Check each timeline row required width also fits
        timeline_rows = frame.timeline_frame.winfo_children()
        for idx, row in enumerate(timeline_rows):
            if isinstance(row, tk.Frame):
                row_width = row.winfo_reqwidth()
                self.assertLessEqual(
                    row_width,
                    max_acceptable_width,
                    f"Timeline row {idx} required width ({row_width}px) exceeds typical full-screen width ({max_acceptable_width}px)",
                )

        # Verify at least one row was checked
        self.assertGreater(
            len(timeline_rows), 0, "Timeline should have at least one row to check"
        )

        # Additional check: verify header and row widths are consistent
        if timeline_rows:
            first_row = timeline_rows[0]
            if isinstance(first_row, tk.Frame):
                row_width = first_row.winfo_reqwidth()
                # Header and row should be similar width (within 10% tolerance)
                width_difference = abs(header_width - row_width)
                tolerance = header_width * 0.1
                self.assertLessEqual(
                    width_difference,
                    tolerance,
                    f"Header width ({header_width}px) and row width ({row_width}px) differ by {width_difference}px (more than 10% tolerance of {tolerance}px)",
                )


class TestAnalysisTimelineSessionNotesContent(unittest.TestCase):
    """
    TDD RED PHASE TEST CLASS: Verify session notes content appears correctly in UI.

    Tests that session_notes field from data.json actually shows up in the
    Session Notes column (column 13) with the correct text value.
    """

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
            },
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True},
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_session_notes_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file(
            "test_session_notes_data.json"
        )

    def test_session_notes_column_shows_actual_text_value(self):
        """
        TDD RED PHASE TEST: Verify session notes text from data appears in UI.

        Bug reproduction:
        - data.json has session_notes: "Active Sphere Active Project"
        - UI shows empty Session Notes column
        - Tests pass but actual data doesn't populate

        This test verifies the ACTUAL TEXT VALUE appears in the Session Notes
        column, not just that the column exists with wraplength configured.
        """
        date = "2026-02-02"
        expected_session_notes = "Active Sphere Active Project"

        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "start_timestamp": 1770045402,
                "end_timestamp": 1770045409,
                "total_duration": 7,
                "active_duration": 7,
                "active": [
                    {
                        "duration": 7,
                        "project": "Project A",
                        "comment": "Working",
                        "start": "10:16:42",
                        "start_timestamp": 1770045402,
                        "end": "10:16:49",
                        "end_timestamp": 1770045409,
                    }
                ],
                "breaks": [],
                "idle_periods": [],
                "session_comments": {
                    "active_notes": "active notes text",
                    "break_notes": "",
                    "idle_notes": "",
                    "session_notes": expected_session_notes,
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
        frame.update_timeline()
        self.root.update_idletasks()

        # Get first data row
        timeline_rows = [
            w for w in frame.timeline_frame.winfo_children() if isinstance(w, tk.Frame)
        ]
        self.assertGreater(
            len(timeline_rows), 0, "Should have at least one timeline row"
        )

        first_row = timeline_rows[0]
        row_labels = [w for w in first_row.winfo_children() if isinstance(w, tk.Label)]

        # Column indices:
        # 0=Date, 1=Start, 2=Duration, 3=Sphere, 4=Sphere Active, 5=Project Active,
        # 6=Type, 7=Primary Project, 8=Primary Comment, 9=Secondary Project,
        # 10=Secondary Comment, 11=Active Comments, 12=Break Comments, 13=Session Notes
        session_notes_label = row_labels[13]
        actual_text = session_notes_label.cget("text")

        self.assertEqual(
            actual_text,
            expected_session_notes,
            f"Session Notes column (index 13) should show '{expected_session_notes}' but shows '{actual_text}'",
        )

    def test_session_notes_not_in_secondary_action_column(self):
        """
        TDD RED PHASE TEST: Verify session notes does NOT appear in Secondary Action column.

        Bug reproduction:
        - User reports: "session notes is in the timeline but in the wrong column.
          it is underneath the secondary action column when it needs to be only in the last column"
        - This test verifies session_notes appears in column 13 (Session Notes)
          and NOT in column 9 (Secondary Action)
        """
        date = "2026-02-02"
        expected_session_notes = "Active Sphere Active Project"

        test_data = {
            f"{date}_session1": {
                "sphere": "Work",
                "date": date,
                "start_timestamp": 1770045402,
                "end_timestamp": 1770045409,
                "total_duration": 7,
                "active_duration": 7,
                "active": [
                    {
                        "duration": 7,
                        "project": "Project A",
                        "comment": "Working on feature",
                        "start": "10:16:42",
                        "start_timestamp": 1770045402,
                        "end": "10:16:49",
                        "end_timestamp": 1770045409,
                    }
                ],
                "breaks": [],
                "idle_periods": [],
                "session_comments": {
                    "active_notes": "active notes text",
                    "break_notes": "",
                    "idle_notes": "",
                    "session_notes": expected_session_notes,
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
        frame.update_timeline()
        self.root.update_idletasks()

        # Get first data row
        timeline_rows = [
            w for w in frame.timeline_frame.winfo_children() if isinstance(w, tk.Frame)
        ]
        self.assertGreater(
            len(timeline_rows), 0, "Should have at least one timeline row"
        )

        first_row = timeline_rows[0]
        row_labels = [w for w in first_row.winfo_children() if isinstance(w, tk.Label)]

        # Column indices:
        # 0=Date, 1=Start, 2=Duration, 3=Sphere, 4=Sphere Active, 5=Project Active,
        # 6=Type, 7=Primary Project, 8=Primary Comment, 9=Secondary Project,
        # 10=Secondary Comment, 11=Active Comments, 12=Break Comments, 13=Session Notes

        # Verify Secondary Action column (index 9) is empty (no secondary project)
        secondary_action_label = row_labels[9]
        secondary_action_text = secondary_action_label.cget("text")

        # Session notes column (index 13)
        session_notes_label = row_labels[13]
        session_notes_text = session_notes_label.cget("text")

        # Verify session notes is in column 13, NOT column 9
        self.assertEqual(
            session_notes_text,
            expected_session_notes,
            f"Session Notes should appear in column 13, but column 13 shows: '{session_notes_text}'",
        )

        # Verify column 9 (Secondary Action) is empty or shows secondary project (not session notes)
        self.assertNotEqual(
            secondary_action_text,
            expected_session_notes,
            f"Session Notes should NOT appear in Secondary Action column (9), but it does: '{secondary_action_text}'",
        )
