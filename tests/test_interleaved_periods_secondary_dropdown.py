"""
Integration test for secondary dropdown updates with interleaved period types.

Tests the bug fix for chronologically interleaved Active/Break/Idle periods.
When periods are in order like: Active → Break → Active → Idle → Active,
the secondary dropdown update logic must check period type rather than
assume all Active periods come first.
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
from src.completion_frame import CompletionFrame
from tests.test_helpers import TestFileManager


class TestInterleavedPeriodsSecondaryDropdowns(unittest.TestCase):
    """Test secondary dropdown updates with chronologically interleaved period types"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        self.addCleanup(self.root.destroy)

        test_data = {}
        settings = {
            "idle_settings": {"idle_tracking_enabled": True},
            "spheres": {
                "Work": {"is_default": True, "active": True},
                "Personal": {"is_default": False, "active": True},
            },
            "projects": {
                "Project A": {"sphere": "Work", "is_default": True, "active": True},
                "Project B": {"sphere": "Work", "is_default": False, "active": True},
                "Exercise": {"sphere": "Personal", "is_default": True, "active": True},
                "Hobby": {"sphere": "Personal", "is_default": False, "active": True},
            },
            "break_actions": {
                "Resting": {"is_default": True, "active": True},
                "Coffee": {"is_default": False, "active": True},
            },
        }

        self.test_data_file = self.file_manager.create_test_file(
            "test_interleaved_data.json", test_data
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_interleaved_settings.json", settings
        )

    def test_interleaved_periods_secondary_dropdowns_after_sphere_change(self):
        """
        Test that secondary dropdowns maintain correct options after sphere change
        with interleaved Active/Break/Idle periods.

        Scenario: Active → Break → Active → Idle → Active
        Bug: Before fix, changing sphere would update Break secondary with project options
        Fix: Now checks period type instead of assuming Active periods come first
        """
        session_name = "2026-01-22_session1"

        # Create session with interleaved periods (chronological order)
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_elapsed": 5000,
                "active_time": 3000,
                "break_time": 1000,
                "active": [
                    {
                        "duration": 1000,
                        "start_timestamp": 1737540000,  # 9:00 AM - Active #1
                        "end_timestamp": 1737541000,
                        "project": "Project A",
                    },
                    {
                        "duration": 1000,
                        "start_timestamp": 1737542200,  # 9:20 AM - Active #2
                        "end_timestamp": 1737543200,
                        "project": "Project B",
                    },
                    {
                        "duration": 1000,
                        "start_timestamp": 1737545000,  # 9:50 AM - Active #3
                        "end_timestamp": 1737546000,
                        "project": "Project A",
                    },
                ],
                "breaks": [
                    {
                        "duration": 1000,
                        "start_timestamp": 1737541000,  # 9:15 AM - Break
                        "end_timestamp": 1737542200,
                        "action": "Coffee",
                    },
                ],
                "idle_periods": [
                    {
                        "duration": 1000,
                        "start_timestamp": 1737543200,  # 9:45 AM - Idle
                        "end_timestamp": 1737545000,
                    },
                ],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)
        self.root.update()  # Allow widgets to fully initialize

        # Verify initial state
        self.assertEqual(frame.selected_sphere, "Work")
        self.assertEqual(len(frame.all_periods), 5)  # 3 Active + 1 Break + 1 Idle
        self.assertEqual(len(frame.secondary_menus), 5)

        # Verify chronological order
        self.assertEqual(frame.all_periods[0]["type"], "Active")
        self.assertEqual(frame.all_periods[1]["type"], "Break")
        self.assertEqual(frame.all_periods[2]["type"], "Active")
        self.assertEqual(frame.all_periods[3]["type"], "Idle")
        self.assertEqual(frame.all_periods[4]["type"], "Active")

        # Verify initial secondary dropdown options
        # Active periods should have project options
        active_secondary_0_values = frame.secondary_menus[0]["values"]
        self.assertIn("Project A", active_secondary_0_values)
        self.assertIn("Project B", active_secondary_0_values)
        self.assertNotIn("Coffee", active_secondary_0_values)

        # Break period should have break action options
        break_secondary_1_values = frame.secondary_menus[1]["values"]
        self.assertIn("Coffee", break_secondary_1_values)
        self.assertIn("Resting", break_secondary_1_values)
        self.assertNotIn("Project A", break_secondary_1_values)

        # Active period should have project options
        active_secondary_2_values = frame.secondary_menus[2]["values"]
        self.assertIn("Project A", active_secondary_2_values)
        self.assertIn("Project B", active_secondary_2_values)

        # Idle period should have break action options
        idle_secondary_3_values = frame.secondary_menus[3]["values"]
        self.assertIn("Coffee", idle_secondary_3_values)
        self.assertIn("Resting", idle_secondary_3_values)
        self.assertNotIn("Project A", idle_secondary_3_values)

        # Active period should have project options
        active_secondary_4_values = frame.secondary_menus[4]["values"]
        self.assertIn("Project A", active_secondary_4_values)
        self.assertIn("Project B", active_secondary_4_values)

        # Now change sphere (triggers _update_project_dropdowns with update_all=False)
        frame.sphere_menu.set("Personal")
        frame._on_sphere_selected(None)
        self.root.update()

        # Verify secondary dropdowns still have correct options after sphere change
        # Active periods should now have Personal sphere projects
        active_secondary_0_values_after = frame.secondary_menus[0]["values"]
        self.assertIn("Exercise", active_secondary_0_values_after)
        self.assertIn("Hobby", active_secondary_0_values_after)
        self.assertNotIn("Coffee", active_secondary_0_values_after)
        self.assertNotIn("Project A", active_secondary_0_values_after)

        # Break period should STILL have break action options (not project options!)
        break_secondary_1_values_after = frame.secondary_menus[1]["values"]
        self.assertIn("Coffee", break_secondary_1_values_after)
        self.assertIn("Resting", break_secondary_1_values_after)
        self.assertNotIn(
            "Exercise",
            break_secondary_1_values_after,
            "BUG: Break secondary dropdown has project options instead of break actions!",
        )
        self.assertNotIn("Hobby", break_secondary_1_values_after)

        # Active period should have Personal sphere projects
        active_secondary_2_values_after = frame.secondary_menus[2]["values"]
        self.assertIn("Exercise", active_secondary_2_values_after)
        self.assertIn("Hobby", active_secondary_2_values_after)

        # Idle period should STILL have break action options (not project options!)
        idle_secondary_3_values_after = frame.secondary_menus[3]["values"]
        self.assertIn("Coffee", idle_secondary_3_values_after)
        self.assertIn("Resting", idle_secondary_3_values_after)
        self.assertNotIn(
            "Exercise",
            idle_secondary_3_values_after,
            "BUG: Idle secondary dropdown has project options instead of break actions!",
        )
        self.assertNotIn("Hobby", idle_secondary_3_values_after)

        # Active period should have Personal sphere projects
        active_secondary_4_values_after = frame.secondary_menus[4]["values"]
        self.assertIn("Exercise", active_secondary_4_values_after)
        self.assertIn("Hobby", active_secondary_4_values_after)
        self.assertNotIn(
            "Coffee",
            active_secondary_4_values_after,
            "BUG: Active secondary dropdown has break action options instead of projects!",
        )

    def test_interleaved_periods_secondary_dropdowns_after_default_project_change(self):
        """
        Test that secondary dropdowns maintain correct options after default project change
        with interleaved periods.

        This triggers _update_project_dropdowns(update_all=True)
        """
        session_name = "2026-01-22_session1"

        # Create session with interleaved periods
        test_data = {
            session_name: {
                "sphere": "Work",
                "date": "2026-01-22",
                "total_elapsed": 3000,
                "active_time": 2000,
                "break_time": 1000,
                "active": [
                    {
                        "duration": 1000,
                        "start_timestamp": 1737540000,  # Active #1
                        "end_timestamp": 1737541000,
                        "project": "Project A",
                    },
                    {
                        "duration": 1000,
                        "start_timestamp": 1737542200,  # Active #2
                        "end_timestamp": 1737543200,
                        "project": "Project B",
                    },
                ],
                "breaks": [
                    {
                        "duration": 1000,
                        "start_timestamp": 1737541000,  # Break (between the two Active periods)
                        "end_timestamp": 1737542200,
                        "action": "Coffee",
                    },
                ],
                "idle_periods": [],
            }
        }
        self.file_manager.create_test_file(self.test_data_file, test_data)

        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()

        frame = CompletionFrame(self.root, tracker, session_name)
        self.root.update()

        # Verify chronological order: Active → Break → Active
        self.assertEqual(len(frame.all_periods), 3)
        self.assertEqual(frame.all_periods[0]["type"], "Active")
        self.assertEqual(frame.all_periods[1]["type"], "Break")
        self.assertEqual(frame.all_periods[2]["type"], "Active")

        # Change default project (triggers update_all=True)
        frame.default_project_menu.set("Project B")
        frame._on_project_selected(None, frame.default_project_menu)
        self.root.update()

        # Verify Break secondary dropdown still has break actions (not projects!)
        break_secondary_values = frame.secondary_menus[1]["values"]
        self.assertIn("Coffee", break_secondary_values)
        self.assertIn("Resting", break_secondary_values)
        self.assertNotIn(
            "Project A",
            break_secondary_values,
            "BUG: Break secondary has project options after default project change!",
        )
        self.assertNotIn("Project B", break_secondary_values)


if __name__ == "__main__":
    unittest.main()
