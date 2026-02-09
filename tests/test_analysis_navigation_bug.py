"""
Test for the specific navigation bug:
Export CSV → Navigate to completion → Back to analysis → Click show timeline

This reproduces the EXACT user-reported sequence.
"""

import unittest
import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime, timedelta
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from tests.test_helpers import TestFileManager, safe_teardown_tk_root


class TestAnalysisNavigationBug(unittest.TestCase):
    """Test the specific navigation sequence that caused the freeze bug"""

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
            "test_nav_bug_data.json", {}
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_nav_bug_settings.json", settings
        )

    def tearDown(self):
        """Clean up after tests"""
        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_csv_export_then_navigate_to_completion_then_back_then_show_timeline(self):
        """
        Test the EXACT sequence that causes the freeze:
        1. Export CSV
        2. Navigate to completion frame
        3. Back to analysis frame
        4. Click show timeline for all spheres > all time

        This should NOT freeze or crash.
        """
        # Create test data
        today = datetime.now()
        test_data = {}

        for i in range(150):
            session_date = (today - timedelta(days=i % 365)).strftime("%Y-%m-%d")
            session_key = f"{session_date}_session{i}"

            test_data[session_key] = {
                "sphere": "Work",
                "date": session_date,
                "start_timestamp": 1234567890 + (i * 1000),
                "end_timestamp": 1234567890 + (i * 1000) + 7200,
                "total_duration": 7200,
                "active_duration": 5400,
                "break_duration": 1800,
                "active": [
                    {
                        "duration": 2700,
                        "project": "Active Project",
                        "start": "09:00:00",
                        "start_timestamp": 1234567890 + (i * 1000),
                        "end": "09:45:00",
                        "end_timestamp": 1234567890 + (i * 1000) + 2700,
                        "comment": f"Active {i}-1",
                    },
                    {
                        "duration": 2700,
                        "project": "Active Project",
                        "start": "10:00:00",
                        "start_timestamp": 1234567890 + (i * 1000) + 3600,
                        "end": "10:45:00",
                        "end_timestamp": 1234567890 + (i * 1000) + 6300,
                        "comment": f"Active {i}-2",
                    },
                ],
                "breaks": [
                    {
                        "duration": 900,
                        "action": "Resting",
                        "start": "11:00:00",
                        "start_timestamp": 1234567890 + (i * 1000) + 7200,
                        "comment": f"Break {i}",
                    }
                ],
                "idle_periods": [],
            }

        with open(self.test_data_file, "w") as f:
            json.dump(test_data, f)

        # Create tracker
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()
        tracker.session_active = False

        # STEP 1: Open analysis frame
        tracker.open_analysis()
        self.root.update()
        self.assertIsNotNone(tracker.analysis_frame, "Analysis frame should be created")
        first_instance_id = id(tracker.analysis_frame)

        # STEP 2: Export CSV (this corrupts the frame state)
        csv_file = self.file_manager.create_test_file("test_nav_export.csv", "")
        with patch("tkinter.filedialog.asksaveasfilename", return_value=csv_file):
            with patch("tkinter.messagebox.showinfo"):
                tracker.analysis_frame.export_to_csv()
        self.root.update()

        # STEP 3: Navigate to completion frame (session view)
        # We'll simulate this by opening session view from analysis
        tracker.open_session_view(from_analysis=True)
        self.root.update()
        self.assertIsNotNone(tracker.session_view_frame, "Session view should be open")

        # STEP 4: Navigate back to analysis frame
        # This is where the bug was - it restored the old corrupted frame
        tracker.close_session_view()
        self.root.update()

        # Verify we got a FRESH analysis frame instance, not the old one
        self.assertIsNotNone(tracker.analysis_frame, "Analysis frame should exist")
        second_instance_id = id(tracker.analysis_frame)
        self.assertNotEqual(
            first_instance_id,
            second_instance_id,
            "Analysis frame should be a NEW instance, not the old corrupted one",
        )

        # STEP 5: Set filters to All Spheres and All Time
        tracker.analysis_frame.sphere_var.set("All Spheres")
        tracker.analysis_frame.status_filter.set("all")
        tracker.analysis_frame.card_ranges[0] = "All Time"
        self.root.update()

        # STEP 6: Click "Show Timeline" - this should NOT freeze
        import time

        start_time = time.time()

        try:
            tracker.analysis_frame.select_card(0)  # All Time card
            self.root.update()
            elapsed = time.time() - start_time

            # Should complete in reasonable time (< 5 seconds)
            # Note: Individual run ~3.5-4s, full suite run ~4-5s due to accumulated overhead
            # Users intentionally wait to review data - 5s is acceptable
            self.assertLess(
                elapsed,
                5.0,
                f"select_card should complete in reasonable time, took {elapsed:.2f}s",
            )

            # Verify timeline was actually updated
            widget_count = len(tracker.analysis_frame.timeline_frame.winfo_children())
            self.assertGreater(
                widget_count, 0, "Timeline should have widgets after select_card"
            )

            print(f"\n✅ Navigation test PASSED:")
            print(f"  - Elapsed time: {elapsed:.3f}s")
            print(f"  - Timeline widgets: {widget_count}")
            print(f"  - First instance ID: {first_instance_id}")
            print(f"  - Second instance ID: {second_instance_id}")
            print(
                f"  - Fresh instance created: {first_instance_id != second_instance_id}"
            )

        except Exception as e:
            elapsed = time.time() - start_time
            self.fail(f"select_card failed after {elapsed:.2f}s with error: {e}")


if __name__ == "__main__":
    unittest.main()
