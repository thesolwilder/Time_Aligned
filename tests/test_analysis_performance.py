"""
Performance Tests for Analysis Frame

Tests to verify that the analysis frame performs well with large datasets.
"""

import unittest
import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime, timedelta
import sys
import os
import time
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from src.analysis_frame import AnalysisFrame
from tests.test_helpers import TestFileManager, TestDataGenerator, safe_teardown_tk_root


class TestAnalysisFramePerformance(unittest.TestCase):
    """Test performance of analysis frame with large datasets"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)

        settings = {
            "idle_settings": {"idle_tracking_enabled": True, "idle_threshold": 60},
            "spheres": {"Work": {"is_default": True, "active": True}},
            "projects": {
                "Active Project": {
                    "sphere": "Work",
                    "is_default": True,
                    "active": True,
                }
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }

        self.test_data_file = self.file_manager.create_test_file(
            "test_performance_data.json", {}
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_performance_settings.json", settings
        )

    def tearDown(self):
        """Clean up after tests"""
        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_update_timeline_performance_with_large_dataset(self):
        """
        Test that update_timeline() completes in reasonable time with large dataset.

        Reproduces bug: After CSV export of large dataset, clicking 'Show Timeline'
        on a card causes the program to freeze.
        """
        # Create VERY large dataset: 500 sessions with 3 periods each = 1500 periods
        # This is more realistic for a "large dataset" that could cause freezing
        today = datetime.now()
        test_data = {}
        for i in range(500):
            session_date = (today - timedelta(days=i % 365)).strftime("%Y-%m-%d")
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

        # Set filters to show all data
        analysis.status_filter.set("all")
        analysis.sphere_var.set("All Spheres")
        analysis.project_var.set("All Projects")
        analysis.selected_card = 2  # All Time

        # First update_timeline call (simulates initial display)
        start_time = time.time()
        analysis.update_timeline()
        first_update_time = time.time() - start_time

        # Force UI to update
        self.root.update()

        # Second update_timeline call (simulates clicking "Show Timeline" after export)
        start_time = time.time()
        analysis.update_timeline()
        second_update_time = time.time() - start_time

        # Force UI to update
        self.root.update()

        # Verify timelines are reasonable (should be < 5 seconds for 1500 periods)
        self.assertLess(
            first_update_time,
            5.0,
            f"First update_timeline took {first_update_time:.2f}s (should be < 5s)",
        )
        self.assertLess(
            second_update_time,
            5.0,
            f"Second update_timeline took {second_update_time:.2f}s (should be < 5s)",
        )

        # Verify timeline has data
        timeline_children = analysis.timeline_frame.winfo_children()
        self.assertGreater(
            len(timeline_children), 0, "Timeline should have rendered periods"
        )

        print(
            f"\nPerformance Results (1500 periods):"
            f"\n  First update_timeline: {first_update_time:.3f}s"
            f"\n  Second update_timeline: {second_update_time:.3f}s"
            f"\n  Timeline widgets: {len(timeline_children)}"
        )

    def test_select_card_performance_after_csv_export(self):
        """
        Test that select_card() performs well after a CSV export operation.

        This specifically tests the reported bug scenario:
        1. Export large dataset to CSV
        2. Click 'Show Timeline' on a card
        3. Program should not freeze
        """
        # Create large dataset
        today = datetime.now()
        test_data = {}
        for i in range(100):
            session_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            session_key = f"{session_date}_session{i}"

            test_data[session_key] = {
                "sphere": "Work",
                "date": session_date,
                "active": [
                    {
                        "duration": 1800,
                        "project": "Active Project",
                        "start": "09:00:00",
                        "comment": f"Work session {i}",
                    }
                ],
                "breaks": [
                    {
                        "duration": 600,
                        "action": "Resting",
                        "start": "10:00:00",
                        "comment": f"Break {i}",
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

        # Step 1: Perform CSV export (simulated)
        csv_file = "test_performance_export.csv"
        self.file_manager.test_files.append(csv_file)

        with patch("tkinter.filedialog.asksaveasfilename", return_value=csv_file):
            with patch("tkinter.messagebox.showinfo"):
                analysis.export_to_csv()

        self.root.update()

        # Step 2: Click 'Show Timeline' on a card (calls select_card)
        start_time = time.time()
        analysis.select_card(0)  # Select first card
        select_card_time = time.time() - start_time

        self.root.update()

        # Verify it completes in reasonable time (< 2 seconds)
        self.assertLess(
            select_card_time,
            2.0,
            f"select_card took {select_card_time:.2f}s after CSV export (should be < 2s)",
        )

        # Verify timeline was updated
        timeline_children = analysis.timeline_frame.winfo_children()
        self.assertGreater(len(timeline_children), 0, "Timeline should have data")

        print(
            f"\nCSV Export + select_card Performance:"
            f"\n  select_card time: {select_card_time:.3f}s"
            f"\n  Timeline widgets: {len(timeline_children)}"
        )

    def test_analysis_frame_fresh_instance_after_reopen(self):
        """
        Test that reopening analysis frame creates a fresh instance, not reusing old state.

        Bug: After CSV export, closing and reopening analysis frame would reuse the same
        instance with stale state, causing freeze when clicking 'Show Timeline'.

        Fix: Always create fresh AnalysisFrame instance in open_analysis().
        """
        # Create dataset
        today = datetime.now()
        test_data = {}
        for i in range(100):
            session_date = (today - timedelta(days=i % 30)).strftime("%Y-%m-%d")
            session_key = f"{session_date}_session{i}"

            test_data[session_key] = {
                "sphere": "Work",
                "date": session_date,
                "active": [
                    {
                        "duration": 1800,
                        "project": "Active Project",
                        "start": "09:00:00",
                        "comment": f"Active {i}",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            }

        with open(self.test_data_file, "w") as f:
            json.dump(test_data, f)

        # Create tracker instance with root
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()
        tracker.session_active = False

        # Mock main_frame_container to prevent errors
        tracker.main_frame_container = ttk.Frame(self.root)

        # Step 1: Open analysis frame first time
        with patch("tkinter.messagebox.showwarning"):
            tracker.open_analysis()

        self.assertIsNotNone(tracker.analysis_frame, "Analysis frame should be created")
        first_instance_id = id(tracker.analysis_frame)

        # Step 2: Export CSV (simulates heavy operation that could corrupt state)
        csv_file = "test_instance_reuse.csv"
        self.file_manager.test_files.append(csv_file)

        with patch("tkinter.filedialog.asksaveasfilename", return_value=csv_file):
            with patch("tkinter.messagebox.showinfo"):
                tracker.analysis_frame.export_to_csv()

        # Step 3: Close analysis frame
        tracker.close_analysis()
        self.assertIsNone(
            tracker.analysis_frame, "Analysis frame should be None after close"
        )

        # Step 4: Reopen analysis frame - should create FRESH instance
        with patch("tkinter.messagebox.showwarning"):
            tracker.open_analysis()

        self.assertIsNotNone(
            tracker.analysis_frame, "Analysis frame should be recreated"
        )
        second_instance_id = id(tracker.analysis_frame)

        # CRITICAL: Verify it's a NEW instance, not the old one
        self.assertNotEqual(
            first_instance_id,
            second_instance_id,
            "Analysis frame should be a FRESH instance, not reused",
        )

        # Step 5: Click 'Show Timeline' should work without freeze
        start_time = time.time()
        tracker.analysis_frame.select_card(0)
        select_card_time = time.time() - start_time

        # Should complete quickly (no freeze from stale state)
        self.assertLess(
            select_card_time,
            2.0,
            f"select_card took {select_card_time:.2f}s on fresh instance (should be < 2s)",
        )

        print(
            f"\nFresh Instance Test:"
            f"\n  First instance ID: {first_instance_id}"
            f"\n  Second instance ID: {second_instance_id}"
            f"\n  Instances are different: {first_instance_id != second_instance_id}"
            f"\n  select_card time on fresh instance: {select_card_time:.3f}s"
        )


if __name__ == "__main__":
    unittest.main()
