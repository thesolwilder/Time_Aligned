"""
Tests for Analysis Frame Card Status Filter (Active/All/Archived Radio Buttons)

Bug 1: Archived projects' time is calculated in cards even when "Active" radio
       button is selected.
Bug 2: Projects belonging to archived spheres have their time calculated in cards
       even when "Active" radio button is selected.

Correct behavior:
- "Active" radio: cards show time for active projects in active spheres only.
- "All" radio: cards show time for all sessions regardless of active/archived status.
- "Archived" radio: cards show time for archived projects or archived spheres only.

Search Keywords: calculate_totals, status_filter, active radio, archived radio,
                 analysis frame cards, inactive project card, archived sphere card,
                 card calculation bug
"""

import unittest
import sys
import os
import tkinter as tk
from tkinter import ttk
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.analysis_frame import AnalysisFrame
from tests.test_helpers import TestFileManager, safe_teardown_tk_root


def _make_tracker(file_manager, spheres, projects, session_data):
    """Build a Mock tracker with the required attributes for AnalysisFrame.

    Args:
        file_manager: TestFileManager instance for settings file management.
        spheres: dict mapping sphere name -> {"is_default": bool, "active": bool}
        projects: dict mapping project name -> {"sphere": str, "active": bool, ...}
        session_data: dict of session_name -> session dict (load_data return value)

    Returns:
        Mock tracker compatible with AnalysisFrame.__init__
    """
    settings = {
        "analysis_settings": {"card_ranges": ["All Time", "All Time", "All Time"]},
        "spheres": spheres,
        "projects": projects,
    }
    settings_file = file_manager.create_test_file(
        "test_card_status_settings.json", settings
    )

    tracker = Mock()
    tracker.settings = settings
    tracker.settings_file = settings_file
    tracker.load_data = Mock(return_value=session_data)

    # _get_default_sphere: return first sphere marked is_default, else first key
    default = next(
        (s for s, d in spheres.items() if d.get("is_default")),
        next(iter(spheres), "General"),
    )
    tracker._get_default_sphere = Mock(return_value=default)
    tracker.get_default_project = Mock(return_value="All Projects")

    return tracker


def _make_frame(root, tracker):
    """Create an AnalysisFrame attached to root using the given tracker.

    Do NOT call root.update() or root.update_idletasks() after construction.
    Either call flushes the geometry manager queue which maps widgets to the
    screen, firing the <Map> event on ScrollableFrame.  That triggers
    _setup_mousewheel() which calls root.bind_all("<MouseWheel>", ...).  In
    Python 3.13 that Tcl binding state is not fully cleaned up by root.destroy(),
    so the next tk.Tk() in setUp raises TclError.  Omitting the update call is
    safe because calculate_totals() only reads tracker.load_data() and the
    filter StringVars — it never needs the frame to be rendered.
    """
    parent = ttk.Frame(root)
    frame = AnalysisFrame(parent, tracker, root)
    return frame


# ---------------------------------------------------------------------------
# Import smoke test
# ---------------------------------------------------------------------------
class TestImport(unittest.TestCase):
    def test_import(self):
        """AnalysisFrame can be imported without errors."""
        from src.analysis_frame import AnalysisFrame

        self.assertIsNotNone(AnalysisFrame)


# ---------------------------------------------------------------------------
# Bug 1: Archived project, active sphere
# ---------------------------------------------------------------------------
class TestCardStatusFilterArchivedProject(unittest.TestCase):
    """Bug 1: cards must not count time for archived projects when Active is selected."""

    SPHERE = "Sphere 1"
    PROJECT = "Project A"
    DURATION = 300  # seconds

    def setUp(self):
        self.root = tk.Tk()
        self.file_manager = TestFileManager()

        spheres = {self.SPHERE: {"is_default": True, "active": True}}
        projects = {
            self.PROJECT: {
                "sphere": self.SPHERE,
                "is_default": True,
                "active": False,  # ARCHIVED PROJECT
            }
        }
        self.base_session = {
            "2026-02-19_session1": {
                "sphere": self.SPHERE,
                "date": "2026-02-19",
                "total_duration": self.DURATION,
                "active_duration": self.DURATION,
                "break_duration": 0,
                "active": [
                    {
                        "start": "12:00:00",
                        "start_timestamp": 1740002400,
                        "duration": self.DURATION,
                        "project": self.PROJECT,
                        "comment": "",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            }
        }
        self.tracker = _make_tracker(
            self.file_manager, spheres, projects, self.base_session
        )
        self.frame = _make_frame(self.root, self.tracker)

    def tearDown(self):
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_active_filter_excludes_archived_project_from_card(self):
        """Bug 1: 'Active' radio must yield 0 active time for an archived project."""
        self.frame.sphere_var.set("All Spheres")
        self.frame.project_var.set("All Projects")
        self.frame.status_filter.set("active")

        active_time, _ = self.frame.calculate_totals("All Time")

        self.assertEqual(
            active_time,
            0,
            "Active-filter cards must not count time for archived projects",
        )

    def test_all_filter_includes_archived_project_in_card(self):
        """'All' radio must count time regardless of project active status."""
        self.frame.sphere_var.set("All Spheres")
        self.frame.project_var.set("All Projects")
        self.frame.status_filter.set("all")

        active_time, _ = self.frame.calculate_totals("All Time")

        self.assertEqual(
            active_time,
            self.DURATION,
            "'All' filter must count time for archived projects",
        )

    def test_archived_filter_includes_archived_project_in_card(self):
        """'Archived' radio must count time for archived projects."""
        self.frame.sphere_var.set("All Spheres")
        self.frame.project_var.set("All Projects")
        self.frame.status_filter.set("archived")

        active_time, _ = self.frame.calculate_totals("All Time")

        self.assertEqual(
            active_time,
            self.DURATION,
            "'Archived' filter must count time for archived projects",
        )

    def test_active_filter_excludes_archived_project_break_time(self):
        """Break time in a session with an archived project (active sphere) under 'active' filter.

        Both active periods AND break time must be excluded when the session's only
        project is inactive and status_filter='active'. The session is considered
        'archived' (not active), so no time — active or break — should appear.
        """
        break_session = {
            "2026-02-19_session1": {
                "sphere": self.SPHERE,
                "date": "2026-02-19",
                "total_duration": 600,
                "active_duration": self.DURATION,
                "break_duration": 60,
                "active": [
                    {
                        "start": "12:00:00",
                        "start_timestamp": 1740002400,
                        "duration": self.DURATION,
                        "project": self.PROJECT,
                        "comment": "",
                    }
                ],
                "breaks": [
                    {
                        "start": "12:05:00",
                        "duration": 60,
                        "action": "Resting",
                    }
                ],
                "idle_periods": [],
            }
        }
        # calculate_totals() calls self.tracker.load_data() fresh each time,
        # so swapping the mock return value is enough — no second frame needed.
        self.tracker.load_data = Mock(return_value=break_session)
        self.frame.sphere_var.set("All Spheres")
        self.frame.project_var.set("All Projects")
        self.frame.status_filter.set("active")

        active_time, break_time = self.frame.calculate_totals("All Time")

        self.assertEqual(active_time, 0, "Active time must be 0 for archived project")
        self.assertEqual(
            break_time,
            0,
            "Break time must be 0: session is archived (inactive project), "
            "so no time should appear under the active filter",
        )


# ---------------------------------------------------------------------------
# Bug 2: Active project, archived sphere
# ---------------------------------------------------------------------------
class TestCardStatusFilterArchivedSphere(unittest.TestCase):
    """Bug 2: cards must not count time for projects in archived spheres with Active selected."""

    SPHERE = "Sphere 1"
    PROJECT = "Project A"
    DURATION = 300  # seconds

    def setUp(self):
        self.root = tk.Tk()
        self.file_manager = TestFileManager()

        spheres = {
            self.SPHERE: {"is_default": True, "active": False}
        }  # ARCHIVED SPHERE
        projects = {
            self.PROJECT: {
                "sphere": self.SPHERE,
                "is_default": True,
                "active": True,  # project itself is active
            }
        }
        session_data = {
            "2026-02-19_session1": {
                "sphere": self.SPHERE,
                "date": "2026-02-19",
                "total_duration": self.DURATION,
                "active_duration": self.DURATION,
                "break_duration": 0,
                "active": [
                    {
                        "start": "12:00:00",
                        "start_timestamp": 1740002400,
                        "duration": self.DURATION,
                        "project": self.PROJECT,
                        "comment": "",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            }
        }
        self.tracker = _make_tracker(self.file_manager, spheres, projects, session_data)
        self.frame = _make_frame(self.root, self.tracker)

    def tearDown(self):
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_active_filter_excludes_archived_sphere_from_card(self):
        """Bug 2: 'Active' radio must yield 0 active time for a project in an archived sphere."""
        self.frame.sphere_var.set("All Spheres")
        self.frame.project_var.set("All Projects")
        self.frame.status_filter.set("active")

        active_time, _ = self.frame.calculate_totals("All Time")

        self.assertEqual(
            active_time,
            0,
            "Active-filter cards must not count time for projects in archived spheres",
        )

    def test_all_filter_includes_archived_sphere_in_card(self):
        """'All' radio must count time regardless of sphere active status."""
        self.frame.sphere_var.set("All Spheres")
        self.frame.project_var.set("All Projects")
        self.frame.status_filter.set("all")

        active_time, _ = self.frame.calculate_totals("All Time")

        self.assertEqual(
            active_time,
            self.DURATION,
            "'All' filter must count time for projects in archived spheres",
        )

    def test_archived_filter_includes_archived_sphere_in_card(self):
        """'Archived' radio must count time for projects in archived spheres."""
        self.frame.sphere_var.set("All Spheres")
        self.frame.project_var.set("All Projects")
        self.frame.status_filter.set("archived")

        active_time, _ = self.frame.calculate_totals("All Time")

        self.assertEqual(
            active_time,
            self.DURATION,
            "'Archived' filter must count time for projects in archived spheres",
        )


# ---------------------------------------------------------------------------
# Active project in active sphere always passes "active" filter (regression)
# ---------------------------------------------------------------------------
class TestCardStatusFilterActiveCombination(unittest.TestCase):
    """Active project + active sphere must always be counted with 'active' filter."""

    SPHERE = "Sphere 1"
    PROJECT = "Project A"
    DURATION = 600

    def setUp(self):
        self.root = tk.Tk()
        self.file_manager = TestFileManager()

        spheres = {self.SPHERE: {"is_default": True, "active": True}}
        projects = {
            self.PROJECT: {
                "sphere": self.SPHERE,
                "is_default": True,
                "active": True,
            }
        }
        session_data = {
            "2026-02-19_session1": {
                "sphere": self.SPHERE,
                "date": "2026-02-19",
                "total_duration": self.DURATION,
                "active_duration": self.DURATION,
                "break_duration": 0,
                "active": [
                    {
                        "start": "12:00:00",
                        "start_timestamp": 1740002400,
                        "duration": self.DURATION,
                        "project": self.PROJECT,
                        "comment": "",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
            }
        }
        self.tracker = _make_tracker(self.file_manager, spheres, projects, session_data)
        self.frame = _make_frame(self.root, self.tracker)

    def tearDown(self):
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_active_project_in_active_sphere_is_counted(self):
        """Active project + active sphere must be counted under 'active' filter."""
        self.frame.sphere_var.set("All Spheres")
        self.frame.project_var.set("All Projects")
        self.frame.status_filter.set("active")

        active_time, _ = self.frame.calculate_totals("All Time")

        self.assertEqual(
            active_time,
            self.DURATION,
            "Active project in active sphere must be counted with 'active' filter",
        )

    def test_active_combination_excluded_by_archived_filter(self):
        """Active project + active sphere must be EXCLUDED by 'archived' filter."""
        self.frame.sphere_var.set("All Spheres")
        self.frame.project_var.set("All Projects")
        self.frame.status_filter.set("archived")

        active_time, _ = self.frame.calculate_totals("All Time")

        self.assertEqual(
            active_time,
            0,
            "Active project in active sphere must NOT appear in 'archived' filter",
        )


if __name__ == "__main__":
    unittest.main()
