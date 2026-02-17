"""
Integration test for completion frame failure when defaults reference renamed items

Bug reproduction:
1. Create session with periods (active, break, active, idle, active, idle, active)
2. Save in completion frame: Sphere=General, Project=Work, Action=Resting
3. Go to settings and rename:
   - Sphere "General" → "Sphere A"
   - Project "Work" → "Project A" (set as default)
   - Action "Resting" → "Action A" (NOT set as default)
4. Try to open completion frame → CRASH

Root cause: default_action_menu.set(default_break_action) fails when
default_break_action refers to renamed action that's no longer in the values list.

Expected: Should handle renamed defaults gracefully without crashing.
"""

import unittest
import tkinter as tk
import sys
import os
import json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from src.completion_frame import CompletionFrame
from test_helpers import TestFileManager, TestDataGenerator


class TestCompletionFrameRenameBug(unittest.TestCase):
    """Test completion frame handles renamed default items without crashing"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        # ❌ DO NOT USE: self.addCleanup(self.root.destroy)

        # Create initial settings with default items
        settings = {
            "idle_settings": {
                "idle_tracking_enabled": True,
                "idle_threshold": 300,
                "idle_break_threshold": 60,
            },
            "screenshot_settings": {
                "enabled": False,
                "capture_on_focus_change": True,
                "min_seconds_between_captures": 10,
                "screenshot_path": "screenshots",
            },
            "spheres": {"General": {"is_default": True, "active": True}},
            "projects": {
                "Work": {"sphere": "General", "is_default": True, "active": True}
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
            "active_actions": {"Working": {"is_default": True, "active": True}},
        }

        self.test_settings_file = self.file_manager.create_test_file(
            "test_settings.json", settings
        )
        self.test_data_file = self.file_manager.create_test_file("test_data.json", {})

    def tearDown(self):
        """Clean up after tests"""
        from test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_completion_frame_opens_after_renaming_non_default_action(self):
        """Test that completion frame can open even when saved action name was renamed

        Reproduces the exact bug scenario:
        1. Session created with periods assigned to "Resting" action
        2. Settings changed: "Resting" renamed to "Action A" but NOT set as default
        3. Completion frame should handle this gracefully without crash

        Bug: TclError when trying to set combobox to value not in values list
        """
        # Step 1: Create tracker and session with periods
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        # Create session with multiple periods
        base_time = datetime.now()
        session_name = base_time.strftime("%Y-%m-%d_%H-%M-%S")

        session_data = {
            session_name: {
                "date": base_time.strftime("%Y-%m-%d"),
                "start_time": base_time.strftime("%H:%M:%S"),
                "start_timestamp": base_time.timestamp(),
                "sphere": "General",  # Initially assigned
                "active": [
                    {"start": 0.0, "end": 5.0, "project": "Work"},
                    {"start": 10.0, "end": 15.0, "project": "Work"},
                    {"start": 25.0, "end": 30.0, "project": "Work"},
                ],
                "breaks": [
                    {
                        "start": 5.0,
                        "end": 10.0,
                        "action": "Resting",  # Using old action name
                    }
                ],
                "idle_periods": [
                    {
                        "start": 15.0,
                        "end": 20.0,
                        "action": "Resting",  # Using old action name
                    },
                    {
                        "start": 20.0,
                        "end": 25.0,
                        "action": "Resting",  # Using old action name
                    },
                ],
                "end_time": (base_time + timedelta(seconds=30)).strftime("%H:%M:%S"),
                "end_timestamp": (base_time + timedelta(seconds=30)).timestamp(),
                "total_duration": 30.0,
                "active_duration": 15.0,
                "break_duration": 5.0,
            }
        }

        # Save session data
        tracker.save_data(session_data)

        # Step 2: Rename items in settings
        # Rename "General" → "Sphere A"
        # Rename "Work" → "Project A" (and keep as default)
        # Rename "Resting" → "Action A" (but DON'T set as default - this causes bug)
        settings = tracker.get_settings()

        # Update sphere name (dict format: {"General": {...}})
        sphere_data = settings["spheres"].pop("General")
        settings["spheres"]["Sphere A"] = sphere_data

        # Update project name (dict format: {"Work": {...}})
        project_data = settings["projects"].pop("Work")
        project_data["sphere"] = "Sphere A"
        project_data["is_default"] = True
        settings["projects"]["Project A"] = project_data

        # Update action name BUT keep DEFAULT_BREAK_ACTION pointing to old name
        # This simulates: user renames "Resting" to "Action A" but does NOT
        # set it as default (so default_break_action still has old value "Resting")
        action_data = settings["break_actions"].pop("Resting")
        action_data["is_default"] = False  # NOT the default
        settings["break_actions"]["Action A"] = action_data

        # The stale reference: default_break_action still says "Resting" which
        # no longer exists in break_actions keys. This is the bug!
        # (In the real scenario, the settings frame updates the name but may
        #  not update the default_break_action key if action is not default)
        # Note: default_break_action key may not exist yet - we inject it stale
        settings["default_break_action"] = "Resting"  # Stale - "Resting" renamed away

        # Save settings to file
        with open(self.test_settings_file, "w") as f:
            json.dump(settings, f, indent=2)

        # Reload tracker settings from file (simulates user navigating to settings and back)
        tracker.settings = tracker.get_settings()

        # Step 3: Try to open completion frame - should NOT crash
        # This is where the bug manifests: default_action_menu.set(default_break_action)
        # tries to set "Resting" but values list only has ["Action A", ...]
        try:
            completion_frame = CompletionFrame(self.root, tracker, session_name)
            # If we get here without exception, test passes
            self.assertIsNotNone(completion_frame)

            # Verify the frame was created successfully
            self.assertTrue(hasattr(completion_frame, "default_action_menu"))

            # Verify it fell back to a valid value (should use first available or empty)
            current_value = completion_frame.default_action_menu.get()
            # Should either be empty or one of the valid actions
            valid_actions = ["Action A", "Break", ""]
            self.assertIn(
                current_value,
                valid_actions,
                f"Default action should be a valid value, got: {current_value}",
            )

        except tk.TclError as e:
            self.fail(
                f"Completion frame crashed with TclError when opening after rename: {e}\n"
                "Bug: Cannot set combobox to renamed default action value"
            )

    def test_completion_frame_preserves_existing_assignments_after_rename(self):
        """Test that existing assignments in session survive rename operations

        Even though action was renamed, the session data still has old name.
        Completion frame should display and allow editing without data loss.
        """
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file

        base_time = datetime.now()
        session_name = base_time.strftime("%Y-%m-%d_%H-%M-%S")

        # Create session with specific assignments
        session_data = {
            session_name: {
                "date": base_time.strftime("%Y-%m-%d"),
                "start_time": base_time.strftime("%H:%M:%S"),
                "start_timestamp": base_time.timestamp(),
                "sphere": "General",
                "active": [{"start": 0.0, "end": 5.0, "project": "Work"}],
                "breaks": [{"start": 5.0, "end": 10.0, "action": "Resting"}],
                "idle_periods": [],
                "end_time": (base_time + timedelta(seconds=10)).strftime("%H:%M:%S"),
                "end_timestamp": (base_time + timedelta(seconds=10)).timestamp(),
                "total_duration": 10.0,
                "active_duration": 5.0,
                "break_duration": 5.0,
            }
        }
        tracker.save_data(session_data)

        # Rename all items (dict format)
        settings = tracker.get_settings()

        sphere_data = settings["spheres"].pop("General")
        settings["spheres"]["Sphere A"] = sphere_data

        project_data = settings["projects"].pop("Work")
        project_data["sphere"] = "Sphere A"
        settings["projects"]["Project A"] = project_data

        action_data = settings["break_actions"].pop("Resting")
        settings["break_actions"]["Action A"] = action_data

        settings["default_break_action"] = "Action A"  # This one IS updated correctly

        # Save settings to file
        with open(self.test_settings_file, "w") as f:
            json.dump(settings, f, indent=2)

        # Reload tracker settings from file (simulates user navigating back)
        tracker.settings = tracker.get_settings()

        # Open completion frame - should handle gracefully
        try:
            completion_frame = CompletionFrame(self.root, tracker, session_name)
            self.assertIsNotNone(completion_frame)

            # Verify session data still intact (even with old names)
            session = tracker.load_data()[session_name]
            self.assertEqual(session["sphere"], "General")  # Old name preserved
            self.assertEqual(
                session["active"][0]["project"], "Work"
            )  # Old name preserved
            self.assertEqual(
                session["breaks"][0]["action"], "Resting"
            )  # Old name preserved

        except tk.TclError as e:
            self.fail(f"Should handle rename gracefully: {e}")


if __name__ == "__main__":
    unittest.main()
