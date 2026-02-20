"""
Tests for Add New Project Duplicate Name Bug Fix

Bug: When adding a project with a name that already exists in another sphere:
  1. The combobox silently set to the existing name (appeared in dropdown with no message)
  2. No project was saved to JSON for the new sphere

Correct behavior:
  - Don't include the name in the dropdown
  - Alert user that the project name already exists

Search Keywords: add new project, duplicate project name, _save_new_project,
                 completion frame, sphere project creation, project name conflict
"""

import unittest
import tkinter as tk
import json
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from src.completion_frame import CompletionFrame
from tests.test_helpers import TestFileManager


class TestAddProjectDuplicateNameBug(unittest.TestCase):
    """Tests that adding a project whose name exists in another sphere is rejected."""

    def setUp(self):
        """Set up two spheres; Project A exists only in Sphere 1."""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)
        # ❌ DO NOT ADD: self.addCleanup(self.root.destroy) — forbidden pattern

        self.settings = {
            "idle_settings": {"idle_tracking_enabled": False},
            "spheres": {
                "Sphere 1": {"is_default": True, "active": True},
                "Sphere 2": {"is_default": False, "active": True},
            },
            "projects": {
                "Project A": {
                    "sphere": "Sphere 1",
                    "is_default": True,
                    "active": True,
                },
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_dup_project_settings.json", self.settings
        )

        # Session in Sphere 2 with one active period
        self.session_name = "2026-02-19_session1"
        test_data = {
            self.session_name: {
                "sphere": "Sphere 2",
                "date": "2026-02-19",
                "total_duration": 300,
                "active_duration": 300,
                "break_duration": 0,
                "active": [
                    {
                        "duration": 300,
                        "start_timestamp": 1740000000,
                        "project": "",
                        "comment": "",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            }
        }
        self.test_data_file = self.file_manager.create_test_file(
            "test_dup_project_data.json", test_data
        )

    def tearDown(self):
        """Clean up Tkinter root using the required safe teardown pattern."""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def _create_frame(self):
        """Create a CompletionFrame for the Sphere 2 session."""
        tracker = TimeTracker(self.root)
        tracker.data_file = self.test_data_file
        tracker.settings_file = self.test_settings_file
        tracker.settings = tracker.get_settings()
        frame = CompletionFrame(self.root, tracker, self.session_name)
        self.root.update()
        return frame, tracker

    # ------------------------------------------------------------------
    # 1. Import / smoke test
    # ------------------------------------------------------------------
    def test_import(self):
        """Smoke test: CompletionFrame creates for Sphere 2 session without error."""
        frame, _ = self._create_frame()
        self.assertIsNotNone(frame)
        self.assertEqual(frame.selected_sphere, "Sphere 2")

    # ------------------------------------------------------------------
    # 2. Duplicate name → warning messagebox shown
    # ------------------------------------------------------------------
    def test_duplicate_project_name_shows_warning(self):
        """Attempting to add 'Project A' (exists in Sphere 1) should show a warning."""
        frame, _ = self._create_frame()
        combobox = frame.project_menus[0]

        combobox.config(state="normal")
        combobox.set("Project A")

        with patch("tkinter.messagebox.showwarning") as mock_warn:
            frame._save_new_project(None, combobox)

        mock_warn.assert_called_once()

    # ------------------------------------------------------------------
    # 3. Duplicate name → NOT added to Sphere 2's projects in memory
    # ------------------------------------------------------------------
    def test_duplicate_project_name_not_added_to_sphere2(self):
        """'Project A' should still belong to Sphere 1 only after failed creation."""
        frame, tracker = self._create_frame()
        combobox = frame.project_menus[0]

        combobox.config(state="normal")
        combobox.set("Project A")

        with patch("tkinter.messagebox.showwarning"):
            frame._save_new_project(None, combobox)

        project_data = tracker.settings["projects"].get("Project A", {})
        self.assertEqual(project_data.get("sphere"), "Sphere 1")

    # ------------------------------------------------------------------
    # 4. Duplicate name → NOT saved to settings JSON
    # ------------------------------------------------------------------
    def test_duplicate_project_name_not_saved_to_json(self):
        """Settings file must NOT be updated when duplicate project name attempted."""
        frame, tracker = self._create_frame()
        combobox = frame.project_menus[0]

        projects_before = dict(tracker.settings["projects"])

        combobox.config(state="normal")
        combobox.set("Project A")

        with patch("tkinter.messagebox.showwarning"):
            frame._save_new_project(None, combobox)

        with open(self.test_settings_file) as f:
            saved_settings = json.load(f)

        # Project count unchanged
        self.assertEqual(
            len(saved_settings["projects"]),
            len(projects_before),
            "No new project should be written to settings.json",
        )
        # Project A still belongs to Sphere 1 on disk
        saved_project = saved_settings["projects"].get("Project A", {})
        self.assertEqual(saved_project.get("sphere"), "Sphere 1")

    # ------------------------------------------------------------------
    # 5. Duplicate name → combobox reverts to readonly (not showing the name)
    # ------------------------------------------------------------------
    def test_duplicate_project_name_combobox_reverts_to_readonly(self):
        """Combobox must return to readonly state after a duplicate-name attempt."""
        frame, _ = self._create_frame()
        combobox = frame.project_menus[0]

        combobox.config(state="normal")
        combobox.set("Project A")

        with patch("tkinter.messagebox.showwarning"):
            frame._save_new_project(None, combobox)

        self.assertEqual(str(combobox.cget("state")), "readonly")

    # ------------------------------------------------------------------
    # 6. Duplicate name → combobox does NOT display the rejected name
    # ------------------------------------------------------------------
    def test_duplicate_project_name_not_shown_in_combobox(self):
        """Combobox must NOT display 'Project A' after a duplicate-name rejection."""
        frame, _ = self._create_frame()
        combobox = frame.project_menus[0]

        combobox.config(state="normal")
        combobox.set("Project A")

        with patch("tkinter.messagebox.showwarning"):
            frame._save_new_project(None, combobox)

        self.assertNotEqual(
            combobox.get(),
            "Project A",
            "Combobox should not show the rejected project name",
        )

    # ------------------------------------------------------------------
    # 7. Duplicate name → 'Project A' not in dropdown values for Sphere 2
    # ------------------------------------------------------------------
    def test_duplicate_project_not_in_dropdown_values(self):
        """'Project A' must NOT appear in Sphere 2's dropdown values list."""
        frame, _ = self._create_frame()
        combobox = frame.project_menus[0]

        combobox.config(state="normal")
        combobox.set("Project A")

        with patch("tkinter.messagebox.showwarning"):
            frame._save_new_project(None, combobox)

        values = list(combobox["values"])
        self.assertNotIn(
            "Project A",
            values,
            "'Project A' from Sphere 1 should not appear in Sphere 2 dropdown",
        )


if __name__ == "__main__":
    unittest.main()
