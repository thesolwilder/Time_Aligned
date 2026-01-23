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


if __name__ == "__main__":
    unittest.main()
