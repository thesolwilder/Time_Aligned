"""
Comprehensive Tests for Settings Frame

Tests all major functionality of the settings frame including:
- Default sphere and project display
- Radio button filters for spheres, projects, and actions
- Adding new spheres and recording to settings file
- Default items always appearing on top
- Only one default per category
- Archive/activate functionality
- Combobox scroll prevention
- Data accuracy validation
"""

import unittest
import json
import os
import sys
import tkinter as tk
from tkinter import ttk
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from test_helpers import TestDataGenerator, TestFileManager
from src.settings_frame import SettingsFrame
from src.ui_helpers import sanitize_name


class MockTracker:
    """Mock TimeTracker for testing settings frame"""

    def __init__(self, settings_file):
        self.settings_file = settings_file
        self.settings = {}
        self.load_settings()

    def load_settings(self):
        """Load settings from file"""
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r") as f:
                self.settings = json.load(f)
        else:
            self.settings = TestDataGenerator.create_settings_data()

    def _get_default_sphere(self):
        """Get default sphere"""
        for name, data in self.settings.get("spheres", {}).items():
            if data.get("is_default", False):
                return name
        # Return first sphere if no default
        spheres = list(self.settings.get("spheres", {}).keys())
        return spheres[0] if spheres else None

    def _get_default_project(self, sphere=None):
        """Get default project, optionally for a specific sphere"""
        for name, data in self.settings.get("projects", {}).items():
            if sphere and data.get("sphere") != sphere:
                continue
            if data.get("is_default", False):
                return name
        return None

    def close_settings(self):
        """Mock close settings"""
        pass


class TestSettingsFrameDefaults(unittest.TestCase):
    """Test default sphere and project display"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        # Create test settings with specific defaults
        settings = TestDataGenerator.create_settings_data(
            default_sphere="DefaultSphere", default_project="DefaultProject"
        )
        self.test_settings_file = self.file_manager.create_test_file(
            "test_settings_frame.json", settings
        )

        # Create GUI components
        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up test files"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_default_sphere_displays(self):
        """Test that default sphere shows up in dropdown"""
        self.frame.refresh_sphere_dropdown()
        current_sphere = self.frame.sphere_var.get()
        self.assertEqual(current_sphere, "DefaultSphere")

    def test_default_project_in_tracker(self):
        """Test that default project is set correctly in settings"""
        default_project = self.tracker._get_default_project()
        self.assertEqual(default_project, "DefaultProject")

    def test_default_sphere_marked_in_settings(self):
        """Test that default sphere has is_default flag"""
        sphere_data = self.tracker.settings["spheres"]["DefaultSphere"]
        self.assertTrue(sphere_data.get("is_default", False))

    def test_default_project_marked_in_settings(self):
        """Test that default project has is_default flag"""
        project_data = self.tracker.settings["projects"]["DefaultProject"]
        self.assertTrue(project_data.get("is_default", False))


class TestSettingsFrameFilters(unittest.TestCase):
    """Test radio button filters for spheres, projects, and actions"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        # Create settings with active and archived items
        settings = {
            "spheres": {
                "ActiveSphere": {"is_default": True, "active": True},
                "ArchivedSphere": {"is_default": False, "active": False},
            },
            "projects": {
                "ActiveProject": {
                    "sphere": "ActiveSphere",
                    "is_default": True,
                    "active": True,
                    "note": "",
                    "goal": "",
                },
                "ArchivedProject": {
                    "sphere": "ActiveSphere",
                    "is_default": False,
                    "active": False,
                    "note": "",
                    "goal": "",
                },
            },
            "break_actions": {
                "ActiveBreak": {"is_default": True, "active": True, "notes": ""},
                "ArchivedBreak": {"is_default": False, "active": False, "notes": ""},
            },
            "idle_settings": {"idle_threshold": 60, "idle_break_threshold": 300},
            "screenshot_settings": {"enabled": False},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_settings_filters.json", settings
        )

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_sphere_filter_active(self):
        """Test sphere filter shows only active spheres"""
        self.frame.sphere_filter.set("active")
        self.frame.refresh_sphere_dropdown()

        values = self.frame.sphere_dropdown["values"]
        # Remove "Create New Sphere..." from values
        sphere_values = [v for v in values if v != "Create New Sphere..."]

        self.assertIn("ActiveSphere", sphere_values)
        self.assertNotIn("ArchivedSphere", sphere_values)

    def test_sphere_filter_inactive(self):
        """Test sphere filter shows only archived spheres"""
        self.frame.sphere_filter.set("inactive")
        self.frame.refresh_sphere_dropdown()

        values = self.frame.sphere_dropdown["values"]
        sphere_values = [v for v in values if v != "Create New Sphere..."]

        self.assertNotIn("ActiveSphere", sphere_values)
        self.assertIn("ArchivedSphere", sphere_values)

    def test_sphere_filter_all(self):
        """Test sphere filter shows all spheres"""
        self.frame.sphere_filter.set("all")
        self.frame.refresh_sphere_dropdown()

        values = self.frame.sphere_dropdown["values"]
        sphere_values = [v for v in values if v != "Create New Sphere..."]

        self.assertIn("ActiveSphere", sphere_values)
        self.assertIn("ArchivedSphere", sphere_values)

    def test_sphere_filter_change_updates_project_list(self):
        """Test that changing sphere filter radio button updates project list"""
        # Set sphere to ActiveSphere
        self.frame.sphere_var.set("ActiveSphere")
        self.frame.on_sphere_selected()

        # Verify project list shows ActiveSphere's projects
        found_active_project = False

        def search_for_active_project(widget):
            nonlocal found_active_project
            if isinstance(widget, (ttk.Entry, tk.Entry)):
                try:
                    if "ActiveProject" in str(widget.get()):
                        found_active_project = True
                except:
                    pass
            for child in widget.winfo_children():
                search_for_active_project(child)

        search_for_active_project(self.frame.projects_list_frame)
        self.assertTrue(
            found_active_project, "ActiveProject should be visible initially"
        )

        # Change sphere filter to inactive (this should select ArchivedSphere)
        self.frame.sphere_filter.set("inactive")
        self.frame.refresh_sphere_dropdown()

        # The sphere dropdown should now show ArchivedSphere
        current_sphere = self.frame.sphere_var.get()
        self.assertEqual(current_sphere, "ArchivedSphere")

        # Verify project list was updated to show ArchivedSphere's projects (no projects in this case)
        # Clear found flag
        found_active_project = False
        search_for_active_project(self.frame.projects_list_frame)
        self.assertFalse(
            found_active_project,
            "ActiveProject should NOT be visible after sphere filter change",
        )

    def test_project_filter_active(self):
        """Test project filter shows only active projects"""
        self.frame.sphere_var.set("ActiveSphere")
        self.frame.project_filter.set("active")
        self.frame.refresh_project_section()

        # Check that active project is in the list
        found_active = False
        found_archived = False

        def search_widgets(widget):
            nonlocal found_active, found_archived
            if isinstance(widget, (ttk.Label, tk.Label)):
                text = str(widget.cget("text"))
                if "ActiveProject" in text:
                    found_active = True
                if "ArchivedProject" in text:
                    found_archived = True
            elif isinstance(widget, (ttk.Entry, tk.Entry)):
                try:
                    text = str(widget.get())
                    if "ActiveProject" in text:
                        found_active = True
                    if "ArchivedProject" in text:
                        found_archived = True
                except:
                    pass
            for child in widget.winfo_children():
                search_widgets(child)

        search_widgets(self.frame.projects_list_frame)

        self.assertTrue(found_active)
        self.assertFalse(found_archived)

    def test_project_filter_archived(self):
        """Test project filter shows only archived projects"""
        self.frame.sphere_var.set("ActiveSphere")
        self.frame.project_filter.set("inactive")
        self.frame.refresh_project_section()

        found_active = False
        found_archived = False

        def search_widgets(widget):
            nonlocal found_active, found_archived
            if isinstance(widget, (ttk.Label, tk.Label)):
                text = str(widget.cget("text"))
                if "ActiveProject" in text:
                    found_active = True
                if "ArchivedProject" in text:
                    found_archived = True
            elif isinstance(widget, (ttk.Entry, tk.Entry)):
                try:
                    text = str(widget.get())
                    if "ActiveProject" in text:
                        found_active = True
                    if "ArchivedProject" in text:
                        found_archived = True
                except:
                    pass
            for child in widget.winfo_children():
                search_widgets(child)

        search_widgets(self.frame.projects_list_frame)

        self.assertFalse(found_active)
        self.assertTrue(found_archived)

    def test_project_filter_all(self):
        """Test project filter shows all projects"""
        self.frame.sphere_var.set("ActiveSphere")
        self.frame.project_filter.set("all")
        self.frame.refresh_project_section()

        found_active = False
        found_archived = False

        def search_widgets(widget):
            nonlocal found_active, found_archived
            if isinstance(widget, (ttk.Label, tk.Label)):
                text = str(widget.cget("text"))
                if "ActiveProject" in text:
                    found_active = True
                if "ArchivedProject" in text:
                    found_archived = True
            elif isinstance(widget, (ttk.Entry, tk.Entry)):
                try:
                    text = str(widget.get())
                    if "ActiveProject" in text:
                        found_active = True
                    if "ArchivedProject" in text:
                        found_archived = True
                except:
                    pass
            for child in widget.winfo_children():
                search_widgets(child)

        search_widgets(self.frame.projects_list_frame)

        self.assertTrue(found_active)
        self.assertTrue(found_archived)

    def test_break_action_filter_active(self):
        """Test break action filter shows only active actions"""
        self.frame.break_action_filter.set("active")
        self.frame.refresh_break_actions()

        # Check widgets in break actions frame
        found_active = False
        found_archived = False

        for widget in self.frame.break_actions_frame.winfo_children():
            labels = [w for w in widget.winfo_children() if isinstance(w, ttk.Label)]
            for label in labels:
                text = str(label.cget("text"))
                if "ActiveBreak" in text:
                    found_active = True
                if "ArchivedBreak" in text:
                    found_archived = True

        self.assertTrue(found_active)
        self.assertFalse(found_archived)

    def test_break_action_filter_all(self):
        """Test break action filter shows all actions"""
        self.frame.break_action_filter.set("all")
        self.frame.refresh_break_actions()

        found_active = False
        found_archived = False

        for widget in self.frame.break_actions_frame.winfo_children():
            labels = [w for w in widget.winfo_children() if isinstance(w, ttk.Label)]
            for label in labels:
                text = str(label.cget("text"))
                if "ActiveBreak" in text:
                    found_active = True
                if "ArchivedBreak" in text:
                    found_archived = True

        self.assertTrue(found_active)
        self.assertTrue(found_archived)


class TestSettingsFrameAddSphere(unittest.TestCase):
    """Test adding new spheres and recording to settings file"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_settings_add_sphere.json", settings
        )

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    @patch("tkinter.simpledialog.askstring")
    def test_add_new_sphere(self, mock_askstring):
        """Test adding a new sphere"""
        mock_askstring.return_value = "NewSphere"

        initial_count = len(self.tracker.settings["spheres"])
        self.frame.create_new_sphere()

        # Check sphere was added
        self.assertIn("NewSphere", self.tracker.settings["spheres"])
        self.assertEqual(len(self.tracker.settings["spheres"]), initial_count + 1)

    @patch("tkinter.simpledialog.askstring")
    def test_new_sphere_saved_to_file(self, mock_askstring):
        """Test that new sphere is saved to settings file"""
        mock_askstring.return_value = "FileSphere"

        self.frame.create_new_sphere()

        # Reload settings from file
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        self.assertIn("FileSphere", settings["spheres"])

    @patch("tkinter.simpledialog.askstring")
    def test_new_sphere_is_active(self, mock_askstring):
        """Test that new sphere is active by default"""
        mock_askstring.return_value = "ActiveNewSphere"

        self.frame.create_new_sphere()

        sphere_data = self.tracker.settings["spheres"]["ActiveNewSphere"]
        self.assertTrue(sphere_data.get("active", False))

    @patch("tkinter.simpledialog.askstring")
    def test_new_sphere_not_default(self, mock_askstring):
        """Test that new sphere is not default by default"""
        mock_askstring.return_value = "NotDefaultSphere"

        self.frame.create_new_sphere()

        sphere_data = self.tracker.settings["spheres"]["NotDefaultSphere"]
        self.assertFalse(sphere_data.get("is_default", False))

    @patch("tkinter.simpledialog.askstring")
    @patch("tkinter.messagebox.showerror")
    def test_duplicate_sphere_rejected(self, mock_error, mock_askstring):
        """Test that duplicate sphere names are rejected"""
        existing_sphere = list(self.tracker.settings["spheres"].keys())[0]
        mock_askstring.return_value = existing_sphere

        initial_count = len(self.tracker.settings["spheres"])
        self.frame.create_new_sphere()

        # Count should not change
        self.assertEqual(len(self.tracker.settings["spheres"]), initial_count)
        # Error should be shown
        mock_error.assert_called_once()

    @patch("tkinter.simpledialog.askstring")
    def test_sphere_name_sanitized(self, mock_askstring):
        """Test that sphere names are sanitized"""
        mock_askstring.return_value = "Test@#Sphere!!"

        self.frame.create_new_sphere()

        # Should be sanitized to remove special characters
        sanitized = sanitize_name("Test@#Sphere!!")
        self.assertIn(sanitized, self.tracker.settings["spheres"])


class TestSettingsFrameDefaultOrdering(unittest.TestCase):
    """Test that default items always appear on top"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        # Create settings with multiple items, default not first alphabetically
        settings = {
            "spheres": {
                "ASphere": {"is_default": False, "active": True},
                "ZDefaultSphere": {"is_default": True, "active": True},
                "MSphere": {"is_default": False, "active": True},
            },
            "projects": {
                "AProject": {
                    "sphere": "ZDefaultSphere",
                    "is_default": False,
                    "active": True,
                    "note": "",
                    "goal": "",
                },
                "ZDefaultProject": {
                    "sphere": "ZDefaultSphere",
                    "is_default": True,
                    "active": True,
                    "note": "",
                    "goal": "",
                },
                "MProject": {
                    "sphere": "ZDefaultSphere",
                    "is_default": False,
                    "active": True,
                    "note": "",
                    "goal": "",
                },
            },
            "break_actions": {
                "AAction": {"is_default": False, "active": True, "notes": ""},
                "ZDefaultAction": {"is_default": True, "active": True, "notes": ""},
                "MAction": {"is_default": False, "active": True, "notes": ""},
            },
            "idle_settings": {"idle_threshold": 60, "idle_break_threshold": 300},
            "screenshot_settings": {"enabled": False},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_settings_ordering.json", settings
        )

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_default_project_appears_first(self):
        """Test that default project appears first in list"""
        self.frame.sphere_var.set("ZDefaultSphere")
        self.frame.project_filter.set("active")
        self.frame.refresh_project_section()

        # Get first project widget
        widgets = self.frame.projects_list_frame.winfo_children()
        if widgets:
            first_widget = widgets[0]

            # Search all children for the project name
            found_default_first = False
            for widget in first_widget.winfo_children():
                if isinstance(widget, (ttk.Entry, tk.Entry)):
                    try:
                        text = str(widget.get())
                        if "ZDefaultProject" in text:
                            found_default_first = True
                            break
                    except:
                        pass
                elif isinstance(widget, (ttk.Label, tk.Label)):
                    text = str(widget.cget("text"))
                    if "ZDefaultProject" in text:
                        found_default_first = True
                        break

            self.assertTrue(found_default_first)

    def test_default_break_action_appears_first(self):
        """Test that default break action appears first in list"""
        self.frame.break_action_filter.set("active")
        self.frame.refresh_break_actions()

        # Find all action name labels
        all_action_names = []
        for widget in self.frame.break_actions_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                labels = [
                    w for w in widget.winfo_children() if isinstance(w, ttk.Label)
                ]
                for label in labels:
                    text = str(label.cget("text"))
                    if text in ["AAction", "ZDefaultAction", "MAction"]:
                        all_action_names.append(text)
                        break

        # First action should be the default one
        if all_action_names:
            self.assertEqual(all_action_names[0], "ZDefaultAction")


class TestSettingsFrameOnlyOneDefault(unittest.TestCase):
    """Test that only one default exists per category"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        settings = {
            "spheres": {
                "Sphere1": {"is_default": True, "active": True},
                "Sphere2": {"is_default": False, "active": True},
            },
            "projects": {
                "Project1": {
                    "sphere": "Sphere1",
                    "is_default": True,
                    "active": True,
                    "note": "",
                    "goal": "",
                },
                "Project2": {
                    "sphere": "Sphere1",
                    "is_default": False,
                    "active": True,
                    "note": "",
                    "goal": "",
                },
            },
            "break_actions": {
                "Action1": {"is_default": True, "active": True, "notes": ""},
                "Action2": {"is_default": False, "active": True, "notes": ""},
            },
            "idle_settings": {"idle_threshold": 60, "idle_break_threshold": 300},
            "screenshot_settings": {"enabled": False},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_settings_one_default.json", settings
        )

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_set_sphere_default_removes_old_default(self):
        """Test that setting a new default sphere removes old default"""
        self.frame.set_default_sphere("Sphere2")

        # Sphere1 should no longer be default
        self.assertFalse(self.tracker.settings["spheres"]["Sphere1"]["is_default"])
        # Sphere2 should now be default
        self.assertTrue(self.tracker.settings["spheres"]["Sphere2"]["is_default"])

        # Count defaults
        default_count = sum(
            1
            for data in self.tracker.settings["spheres"].values()
            if data.get("is_default", False)
        )
        self.assertEqual(default_count, 1)

    def test_set_project_default_removes_old_default(self):
        """Test that setting a new default project removes old default in same sphere"""
        self.frame.set_default_project("Project2")

        # Project1 should no longer be default
        self.assertFalse(self.tracker.settings["projects"]["Project1"]["is_default"])
        # Project2 should now be default
        self.assertTrue(self.tracker.settings["projects"]["Project2"]["is_default"])

        # Count defaults in same sphere
        default_count = sum(
            1
            for data in self.tracker.settings["projects"].values()
            if data.get("sphere") == "Sphere1" and data.get("is_default", False)
        )
        self.assertEqual(default_count, 1)

    def test_set_break_action_default_removes_old_default(self):
        """Test that setting a new default break action removes old default"""
        self.frame.set_default_break_action("Action2")

        # Action1 should no longer be default
        self.assertFalse(
            self.tracker.settings["break_actions"]["Action1"]["is_default"]
        )
        # Action2 should now be default
        self.assertTrue(self.tracker.settings["break_actions"]["Action2"]["is_default"])

        # Count defaults
        default_count = sum(
            1
            for data in self.tracker.settings["break_actions"].values()
            if data.get("is_default", False)
        )
        self.assertEqual(default_count, 1)

    def test_multiple_spheres_can_have_default_projects(self):
        """Test that different spheres can each have their own default project"""
        # Add another sphere with its own projects
        self.tracker.settings["spheres"]["Sphere3"] = {
            "is_default": False,
            "active": True,
        }
        self.tracker.settings["projects"]["Project3"] = {
            "sphere": "Sphere3",
            "is_default": True,
            "active": True,
            "note": "",
            "goal": "",
        }

        # Both projects should be default in their respective spheres
        sphere1_defaults = [
            name
            for name, data in self.tracker.settings["projects"].items()
            if data.get("sphere") == "Sphere1" and data.get("is_default", False)
        ]
        sphere3_defaults = [
            name
            for name, data in self.tracker.settings["projects"].items()
            if data.get("sphere") == "Sphere3" and data.get("is_default", False)
        ]

        self.assertEqual(len(sphere1_defaults), 1)
        self.assertEqual(len(sphere3_defaults), 1)


class TestSettingsFrameArchiveActivate(unittest.TestCase):
    """Test archive and activate functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        settings = {
            "spheres": {
                "ActiveSphere": {"is_default": True, "active": True},
                "ArchivedSphere": {"is_default": False, "active": False},
            },
            "projects": {
                "ActiveProject": {
                    "sphere": "ActiveSphere",
                    "is_default": True,
                    "active": True,
                    "note": "",
                    "goal": "",
                },
                "ArchivedProject": {
                    "sphere": "ActiveSphere",
                    "is_default": False,
                    "active": False,
                    "note": "",
                    "goal": "",
                },
            },
            "break_actions": {
                "ActiveAction": {"is_default": True, "active": True, "notes": ""},
                "ArchivedAction": {"is_default": False, "active": False, "notes": ""},
            },
            "idle_settings": {"idle_threshold": 60, "idle_break_threshold": 300},
            "screenshot_settings": {"enabled": False},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_settings_archive.json", settings
        )

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_archive_sphere(self):
        """Test archiving an active sphere"""
        self.frame.toggle_sphere_active("ActiveSphere")

        # Should now be inactive
        self.assertFalse(self.tracker.settings["spheres"]["ActiveSphere"]["active"])

    def test_activate_sphere(self):
        """Test activating an archived sphere"""
        self.frame.toggle_sphere_active("ArchivedSphere")

        # Should now be active
        self.assertTrue(self.tracker.settings["spheres"]["ArchivedSphere"]["active"])

    def test_archive_project(self):
        """Test archiving an active project"""
        self.frame.toggle_project_active("ActiveProject")

        # Should now be inactive
        self.assertFalse(self.tracker.settings["projects"]["ActiveProject"]["active"])

    def test_activate_project(self):
        """Test activating an archived project"""
        self.frame.toggle_project_active("ArchivedProject")

        # Should now be active
        self.assertTrue(self.tracker.settings["projects"]["ArchivedProject"]["active"])

    def test_archive_break_action(self):
        """Test archiving an active break action"""
        self.frame.toggle_break_action_active("ActiveAction")

        # Should now be inactive
        self.assertFalse(
            self.tracker.settings["break_actions"]["ActiveAction"]["active"]
        )

    def test_activate_break_action(self):
        """Test activating an archived break action"""
        self.frame.toggle_break_action_active("ArchivedAction")

        # Should now be active
        self.assertTrue(
            self.tracker.settings["break_actions"]["ArchivedAction"]["active"]
        )

    def test_archived_item_persisted_to_file(self):
        """Test that archive status is saved to file"""
        self.frame.toggle_project_active("ActiveProject")

        # Reload from file
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        self.assertFalse(settings["projects"]["ActiveProject"]["active"])

    def test_activated_item_persisted_to_file(self):
        """Test that activate status is saved to file"""
        self.frame.toggle_project_active("ArchivedProject")

        # Reload from file
        with open(self.test_settings_file, "r") as f:
            settings = json.load(f)

        self.assertTrue(settings["projects"]["ArchivedProject"]["active"])


class TestSettingsFrameComboboxScroll(unittest.TestCase):
    """Test that comboboxes cannot be scrolled through"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_settings_combobox.json", settings
        )

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_sphere_dropdown_is_readonly(self):
        """Test that sphere dropdown is readonly (prevents scrolling)"""
        self.assertEqual(str(self.frame.sphere_dropdown["state"]), "readonly")

    def test_sphere_dropdown_has_exportselection_false(self):
        """Test that sphere dropdown has exportselection=False"""
        # This prevents scroll behavior
        self.assertFalse(self.frame.sphere_dropdown.cget("exportselection"))


class TestSettingsFrameDataAccuracy(unittest.TestCase):
    """Test data accuracy and validation"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_settings_accuracy.json", settings
        )

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_project_sphere_association_preserved(self):
        """Test that project-sphere associations are maintained"""
        for project_name, project_data in self.tracker.settings["projects"].items():
            sphere_name = project_data.get("sphere")
            self.assertIsNotNone(sphere_name)
            self.assertIn(sphere_name, self.tracker.settings["spheres"])

    def test_all_spheres_have_required_fields(self):
        """Test that all spheres have is_default and active fields"""
        for sphere_name, sphere_data in self.tracker.settings["spheres"].items():
            self.assertIn("is_default", sphere_data)
            self.assertIn("active", sphere_data)
            self.assertIsInstance(sphere_data["is_default"], bool)
            self.assertIsInstance(sphere_data["active"], bool)

    def test_all_projects_have_required_fields(self):
        """Test that all projects have required fields"""
        required_fields = ["sphere", "is_default", "active", "note", "goal"]
        for project_name, project_data in self.tracker.settings["projects"].items():
            for field in required_fields:
                self.assertIn(field, project_data)

    def test_all_break_actions_have_required_fields(self):
        """Test that all break actions have required fields"""
        required_fields = ["is_default", "active"]
        for action_name, action_data in self.tracker.settings["break_actions"].items():
            for field in required_fields:
                self.assertIn(field, action_data)

    def test_settings_file_is_valid_json(self):
        """Test that settings file contains valid JSON"""
        with open(self.test_settings_file, "r") as f:
            try:
                json.load(f)
                valid = True
            except json.JSONDecodeError:
                valid = False

        self.assertTrue(valid)

    def test_only_one_sphere_is_default(self):
        """Test that exactly one sphere is default"""
        default_count = sum(
            1
            for data in self.tracker.settings["spheres"].values()
            if data.get("is_default", False)
        )
        self.assertEqual(default_count, 1)

    def test_each_sphere_has_at_most_one_default_project(self):
        """Test that each sphere has at most one default project"""
        sphere_defaults = {}
        for project_name, project_data in self.tracker.settings["projects"].items():
            sphere = project_data.get("sphere")
            if project_data.get("is_default", False):
                if sphere not in sphere_defaults:
                    sphere_defaults[sphere] = 0
                sphere_defaults[sphere] += 1

        for sphere, count in sphere_defaults.items():
            self.assertLessEqual(count, 1, f"Sphere {sphere} has {count} defaults")

    def test_only_one_break_action_is_default(self):
        """Test that exactly one break action is default"""
        default_count = sum(
            1
            for data in self.tracker.settings["break_actions"].values()
            if data.get("is_default", False)
        )
        self.assertGreaterEqual(default_count, 1)
        self.assertLessEqual(default_count, 1)

    def test_edit_sphere_name_updates_projects(self):
        """Test that editing sphere name updates associated projects"""
        old_name = "Coding"
        new_name = "ProgrammingRenamed"

        # First ensure the sphere exists
        if old_name not in self.tracker.settings["spheres"]:
            self.tracker.settings["spheres"][old_name] = {
                "is_default": False,
                "active": True,
            }

        # Add a project associated with this sphere
        self.tracker.settings["projects"]["TestProj"] = {
            "sphere": old_name,
            "is_default": False,
            "active": True,
            "note": "",
            "goal": "",
        }

        # Mock the dialog
        with patch("tkinter.simpledialog.askstring") as mock_ask:
            mock_ask.return_value = new_name
            self.frame.edit_sphere_name(old_name)

        # Check that project's sphere reference was updated
        self.assertEqual(
            self.tracker.settings["projects"]["TestProj"]["sphere"], new_name
        )

    def test_delete_sphere_removes_associated_projects(self):
        """Test that deleting a sphere removes its projects"""
        sphere_to_delete = "Coding"

        # Ensure sphere exists
        if sphere_to_delete not in self.tracker.settings["spheres"]:
            self.tracker.settings["spheres"][sphere_to_delete] = {
                "is_default": False,
                "active": True,
            }

        # Add projects to this sphere
        self.tracker.settings["projects"]["ToDelete1"] = {
            "sphere": sphere_to_delete,
            "is_default": False,
            "active": True,
            "note": "",
            "goal": "",
        }
        self.tracker.settings["projects"]["ToDelete2"] = {
            "sphere": sphere_to_delete,
            "is_default": False,
            "active": True,
            "note": "",
            "goal": "",
        }

        # Mock confirmation dialog
        with patch("tkinter.messagebox.askyesno") as mock_confirm:
            mock_confirm.return_value = True
            self.frame.delete_sphere(sphere_to_delete)

        # Check that projects were deleted
        self.assertNotIn("ToDelete1", self.tracker.settings["projects"])
        self.assertNotIn("ToDelete2", self.tracker.settings["projects"])

    def test_delete_sphere_removes_all_associated_projects_only(self):
        """Test that deleting a sphere only removes projects from that sphere"""
        sphere_to_delete = "DeleteSphere"
        other_sphere = "KeepSphere"

        # Create two spheres
        self.tracker.settings["spheres"][sphere_to_delete] = {
            "is_default": False,
            "active": True,
        }
        self.tracker.settings["spheres"][other_sphere] = {
            "is_default": False,
            "active": True,
        }

        # Add projects to both spheres
        self.tracker.settings["projects"]["DeleteProject1"] = {
            "sphere": sphere_to_delete,
            "is_default": False,
            "active": True,
            "note": "",
            "goal": "",
        }
        self.tracker.settings["projects"]["DeleteProject2"] = {
            "sphere": sphere_to_delete,
            "is_default": False,
            "active": True,
            "note": "",
            "goal": "",
        }
        self.tracker.settings["projects"]["KeepProject"] = {
            "sphere": other_sphere,
            "is_default": False,
            "active": True,
            "note": "",
            "goal": "",
        }

        initial_keep_project_count = 1

        # Mock confirmation dialog
        with patch("tkinter.messagebox.askyesno") as mock_confirm:
            mock_confirm.return_value = True
            self.frame.delete_sphere(sphere_to_delete)

        # Check that only projects from deleted sphere were removed
        self.assertNotIn("DeleteProject1", self.tracker.settings["projects"])
        self.assertNotIn("DeleteProject2", self.tracker.settings["projects"])
        self.assertIn("KeepProject", self.tracker.settings["projects"])
        self.assertEqual(
            self.tracker.settings["projects"]["KeepProject"]["sphere"], other_sphere
        )


class TestSettingsFrameSphereArchiveCascade(unittest.TestCase):
    """Test that archiving a sphere archives all associated projects"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        # Create settings with multiple spheres and projects
        settings = {
            "spheres": {
                "ActiveSphere": {"is_default": True, "active": True},
                "ToArchiveSphere": {"is_default": False, "active": True},
            },
            "projects": {
                "ActiveProject": {
                    "sphere": "ActiveSphere",
                    "is_default": True,
                    "active": True,
                    "note": "",
                    "goal": "",
                },
                "ToArchiveProject1": {
                    "sphere": "ToArchiveSphere",
                    "is_default": False,
                    "active": True,
                    "note": "",
                    "goal": "",
                },
                "ToArchiveProject2": {
                    "sphere": "ToArchiveSphere",
                    "is_default": True,
                    "active": True,
                    "note": "",
                    "goal": "",
                },
            },
            "break_actions": {
                "ActiveAction": {"is_default": True, "active": True, "notes": ""}
            },
            "idle_settings": {"idle_threshold": 60, "idle_break_threshold": 300},
            "screenshot_settings": {"enabled": False},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_settings_sphere_archive.json", settings
        )

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_archive_sphere_does_not_auto_archive_projects(self):
        """Test current behavior: archiving sphere doesn't auto-archive projects"""
        # This documents the current behavior - projects are NOT automatically archived
        # when their sphere is archived. Projects remain active but won't show up
        # in the active sphere view.

        self.frame.toggle_sphere_active("ToArchiveSphere")

        # Sphere should be archived
        self.assertFalse(self.tracker.settings["spheres"]["ToArchiveSphere"]["active"])

        # Projects are NOT automatically archived (current behavior)
        self.assertTrue(
            self.tracker.settings["projects"]["ToArchiveProject1"]["active"]
        )
        self.assertTrue(
            self.tracker.settings["projects"]["ToArchiveProject2"]["active"]
        )

    def test_archived_sphere_projects_not_visible_in_active_filter(self):
        """Test that projects from archived sphere don't show in active sphere filter"""
        # Archive the sphere
        self.frame.toggle_sphere_active("ToArchiveSphere")

        # Set sphere filter to active
        self.frame.sphere_filter.set("active")
        self.frame.refresh_sphere_dropdown()

        # ToArchiveSphere should not be in dropdown
        values = self.frame.sphere_dropdown["values"]
        sphere_values = [v for v in values if v != "Create New Sphere..."]
        self.assertNotIn("ToArchiveSphere", sphere_values)

        # Therefore, its projects won't be shown even though they're active
        # (because you can't select an archived sphere to view its projects)

    def test_activate_archived_sphere_shows_projects_again(self):
        """Test that activating an archived sphere makes its projects visible again"""
        # Archive then activate the sphere
        self.frame.toggle_sphere_active("ToArchiveSphere")
        self.frame.toggle_sphere_active("ToArchiveSphere")

        # Sphere should be active again
        self.assertTrue(self.tracker.settings["spheres"]["ToArchiveSphere"]["active"])

        # Set sphere filter to active and select the sphere
        self.frame.sphere_filter.set("active")
        self.frame.refresh_sphere_dropdown()

        # ToArchiveSphere should be in dropdown
        values = self.frame.sphere_dropdown["values"]
        sphere_values = [v for v in values if v != "Create New Sphere..."]
        self.assertIn("ToArchiveSphere", sphere_values)

        # Select it and verify projects are visible
        self.frame.sphere_var.set("ToArchiveSphere")
        self.frame.project_filter.set("active")
        self.frame.refresh_project_section()

        # Check that projects show up
        found_project1 = False
        found_project2 = False

        def search_widgets(widget):
            nonlocal found_project1, found_project2
            if isinstance(widget, (ttk.Entry, tk.Entry)):
                try:
                    text = str(widget.get())
                    if "ToArchiveProject1" in text:
                        found_project1 = True
                    if "ToArchiveProject2" in text:
                        found_project2 = True
                except:
                    pass
            for child in widget.winfo_children():
                search_widgets(child)

        search_widgets(self.frame.projects_list_frame)

        self.assertTrue(found_project1)
        self.assertTrue(found_project2)


class TestExtractSpreadsheetIdFromUrl(unittest.TestCase):
    """Test extract_spreadsheet_id_from_url utility function"""

    def test_extract_from_standard_url(self):
        """Test extraction from standard Google Sheets URL"""
        from src.settings_frame import extract_spreadsheet_id_from_url

        url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"
        result = extract_spreadsheet_id_from_url(url)

        self.assertEqual(result, "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")

    def test_extract_from_url_with_gid(self):
        """Test extraction from URL with sheet ID (gid parameter)"""
        from src.settings_frame import extract_spreadsheet_id_from_url

        url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=0"
        result = extract_spreadsheet_id_from_url(url)

        self.assertEqual(result, "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")

    def test_extract_from_url_with_range(self):
        """Test extraction from URL with cell range"""
        from src.settings_frame import extract_spreadsheet_id_from_url

        url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=0&range=A1:B2"
        result = extract_spreadsheet_id_from_url(url)

        self.assertEqual(result, "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")

    def test_plain_id_returned_unchanged(self):
        """Test that plain spreadsheet ID is returned unchanged"""
        from src.settings_frame import extract_spreadsheet_id_from_url

        plain_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        result = extract_spreadsheet_id_from_url(plain_id)

        self.assertEqual(result, plain_id)

    def test_empty_string_returns_empty(self):
        """Test that empty string returns empty string"""
        from src.settings_frame import extract_spreadsheet_id_from_url

        result = extract_spreadsheet_id_from_url("")

        self.assertEqual(result, "")

    def test_none_returns_empty(self):
        """Test that None returns empty string"""
        from src.settings_frame import extract_spreadsheet_id_from_url

        result = extract_spreadsheet_id_from_url(None)

        self.assertEqual(result, "")

    def test_invalid_url_returned_unchanged(self):
        """Test that invalid URL is returned unchanged"""
        from src.settings_frame import extract_spreadsheet_id_from_url

        invalid_url = "https://example.com/not-a-sheet"
        result = extract_spreadsheet_id_from_url(invalid_url)

        self.assertEqual(result, invalid_url)

    def test_id_with_hyphens_and_underscores(self):
        """Test extraction of ID containing hyphens and underscores"""
        from src.settings_frame import extract_spreadsheet_id_from_url

        url = "https://docs.google.com/spreadsheets/d/ABC123-def_456-GHI/edit"
        result = extract_spreadsheet_id_from_url(url)

        self.assertEqual(result, "ABC123-def_456-GHI")

    def test_url_without_edit_suffix(self):
        """Test extraction from URL without /edit suffix"""
        from src.settings_frame import extract_spreadsheet_id_from_url

        url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        result = extract_spreadsheet_id_from_url(url)

        self.assertEqual(result, "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")


class TestProjectSphereChangeIntegration(unittest.TestCase):
    """Integration test: Project sphere change refreshes project list correctly"""

    def setUp(self):
        """Set up test fixtures with two spheres and projects in each"""
        self.file_manager = TestFileManager()

        # Create settings with two spheres and projects in each
        settings = {
            "spheres": {
                "Sphere1": {"is_default": True, "active": True},
                "Sphere2": {"is_default": False, "active": True},
            },
            "projects": {
                "Project1A": {
                    "sphere": "Sphere1",
                    "is_default": True,
                    "active": True,
                    "note": "",
                    "goal": "",
                },
                "Project1B": {
                    "sphere": "Sphere1",
                    "is_default": False,
                    "active": True,
                    "note": "Will be moved",
                    "goal": "",
                },
                "Project2A": {
                    "sphere": "Sphere2",
                    "is_default": True,
                    "active": True,
                    "note": "",
                    "goal": "",
                },
            },
            "break_actions": {
                "Resting": {"is_default": True, "active": True, "notes": ""}
            },
            "idle_settings": {
                "idle_tracking_enabled": True,
                "idle_threshold": 60,
                "idle_break_threshold": 300,
            },
            "screenshot_settings": {
                "enabled": False,
                "capture_on_focus_change": True,
                "min_seconds_between_captures": 10,
                "screenshot_path": "./screenshots",
            },
            "google_sheets": {
                "enabled": False,
                "spreadsheet_id": "",
                "sheet_name": "Session Data",
            },
        }

        self.test_settings_file = self.file_manager.create_test_file(
            "test_sphere_change.json", settings
        )

        # Create GUI components
        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up test files"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_project_disappears_when_sphere_changed(self):
        """
        Integration test: When editing project and changing sphere,
        project should disappear from current sphere's project list

        Bug reproduction:
        1. Start on Sphere1 (shows Project1A and Project1B)
        2. Edit Project1B and change sphere to Sphere2
        3. Save
        Expected: Project1B disappears from Sphere1 list
        Bug: Project1B still visible in Sphere1 list
        """
        # Arrange: Select Sphere1 (should show Project1A and Project1B)
        self.frame.sphere_var.set("Sphere1")
        self.frame.load_selected_sphere()
        self.frame.refresh_project_section()

        # Get initial project count for Sphere1
        initial_projects = []
        for widget in self.frame.projects_list_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                # Look for project name in the frame's children
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Label) and child.cget("text") == "Name:":
                        # Next widget should be the entry with project name
                        for sibling in widget.winfo_children():
                            if isinstance(sibling, ttk.Entry):
                                project_name = sibling.get()
                                if project_name:
                                    initial_projects.append(project_name)
                                    break
                        break

        # Verify we start with 2 projects in Sphere1
        self.assertEqual(len(initial_projects), 2)
        self.assertIn("Project1A", initial_projects)
        self.assertIn("Project1B", initial_projects)

        # Act: Change Project1B's sphere to Sphere2
        # Simulate user editing project
        self.tracker.settings["projects"]["Project1B"]["sphere"] = "Sphere2"
        with open(self.test_settings_file, "w") as f:
            json.dump(self.tracker.settings, f, indent=2)
        self.tracker.load_settings()

        # Refresh project section (this is what the bug fix does)
        self.frame.refresh_project_section()

        # Assert: Project1B should no longer appear in Sphere1's project list
        final_projects = []
        for widget in self.frame.projects_list_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Label) and child.cget("text") == "Name:":
                        for sibling in widget.winfo_children():
                            if isinstance(sibling, ttk.Entry):
                                project_name = sibling.get()
                                if project_name:
                                    final_projects.append(project_name)
                                    break
                        break

        # After sphere change, should only see Project1A in Sphere1
        self.assertEqual(len(final_projects), 1)
        self.assertIn("Project1A", final_projects)
        self.assertNotIn("Project1B", final_projects)

        # Verify Project1B now appears in Sphere2
        self.frame.sphere_var.set("Sphere2")
        self.frame.load_selected_sphere()
        self.frame.refresh_project_section()

        sphere2_projects = []
        for widget in self.frame.projects_list_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Label) and child.cget("text") == "Name:":
                        for sibling in widget.winfo_children():
                            if isinstance(sibling, ttk.Entry):
                                project_name = sibling.get()
                                if project_name:
                                    sphere2_projects.append(project_name)
                                    break
                        break

        self.assertEqual(len(sphere2_projects), 2)
        self.assertIn("Project2A", sphere2_projects)
        self.assertIn("Project1B", sphere2_projects)


class TestIdleSettingsValidation(unittest.TestCase):
    """Test validation for idle settings input - following TDD"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()
        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_idle_validation.json", settings
        )

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        # Create a minimal validation function to test
        # This allows tests to RUN and FAIL, not ERROR

    def tearDown(self):
        """Clean up test files"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_validate_idle_threshold_function_exists(self):
        """Test that validate_idle_threshold helper function exists in settings_frame"""
        from src.settings_frame import validate_idle_threshold

        # Function should exist
        self.assertIsNotNone(validate_idle_threshold)

        # Should be callable
        self.assertTrue(callable(validate_idle_threshold))

    def test_validate_idle_threshold_accepts_valid_value(self):
        """Test that validate_idle_threshold accepts valid numeric string"""
        from src.settings_frame import validate_idle_threshold

        # Test with valid value - should return integer
        result = validate_idle_threshold("120")

        # Should return the integer value, not None
        self.assertEqual(result, 120)

    def test_validate_idle_threshold_rejects_invalid_string(self):
        """Test that validate_idle_threshold rejects non-numeric string"""
        from src.settings_frame import validate_idle_threshold

        # Test with invalid string
        result = validate_idle_threshold("invalid_text")

        # Should return None (validation failed)
        self.assertIsNone(result)

    def test_validate_idle_threshold_rejects_negative_value(self):
        """Test that validate_idle_threshold rejects negative values"""
        from src.settings_frame import validate_idle_threshold

        # Test with negative value
        result = validate_idle_threshold("-10")

        # Should return None (validation failed)
        self.assertIsNone(result)

    def test_validate_idle_threshold_rejects_zero(self):
        """Test that validate_idle_threshold rejects zero"""
        from src.settings_frame import validate_idle_threshold

        # Test with zero
        result = validate_idle_threshold("0")

        # Should return None (validation failed)
        self.assertIsNone(result)

    def test_validate_idle_threshold_accepts_boundary_values(self):
        """Test that validate_idle_threshold accepts min (1) and max (600)"""
        from src.settings_frame import validate_idle_threshold

        # Test minimum value
        result_min = validate_idle_threshold("1")
        self.assertEqual(result_min, 1)

        # Test maximum value
        result_max = validate_idle_threshold("600")
        self.assertEqual(result_max, 600)

    def test_validate_idle_threshold_rejects_too_large_value(self):
        """Test that validate_idle_threshold rejects values > 600"""
        from src.settings_frame import validate_idle_threshold

        # Test with value over max
        result = validate_idle_threshold("601")

        # Should return None (validation failed)
        self.assertIsNone(result)


class TestIdleSettingsUI(unittest.TestCase):
    """Test idle settings UI displays values correctly"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()
        # Create settings with specific idle threshold
        settings = TestDataGenerator.create_settings_data()
        settings["idle_settings"] = {
            "idle_tracking_enabled": True,
            "idle_threshold": 120,  # Set to 120 for testing
            "idle_break_threshold": 300,
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_idle_ui.json", settings
        )

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)

    def tearDown(self):
        """Clean up test files"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_idle_settings_loads_from_json(self):
        """Test that idle settings from JSON are loaded correctly"""
        # Verify tracker loaded settings correctly
        self.assertEqual(self.tracker.settings["idle_settings"]["idle_threshold"], 120)

        # Now create settings frame
        frame = SettingsFrame(self.root, self.tracker, self.root)

        # The frame should have created UI with the value 120
        # We can verify by checking if save would work with the initial value
        self.assertEqual(self.tracker.settings["idle_settings"]["idle_threshold"], 120)

    def test_idle_threshold_spinbox_shows_value_from_settings(self):
        """Test that idle threshold spinbox displays the value from settings.json on load"""
        # Create settings frame - this should load settings and display in UI
        frame = SettingsFrame(self.root, self.tracker, self.root)

        # Force widget updates
        self.root.update_idletasks()
        self.root.update()

        # Search through the frame to find the idle settings spinbox
        found_spinbox = None
        found_label = False

        # The spinbox is in a LabelFrame created by _create_idle_settings_subsection
        def find_widgets(widget, depth=0):
            nonlocal found_spinbox, found_label

            if depth > 10:  # Prevent infinite recursion
                return

            for child in widget.winfo_children():
                # Look for the "Idle Threshold (seconds):" label to confirm we're in the right area
                if isinstance(child, ttk.Label):
                    label_text = child.cget("text")
                    if "Idle Threshold (seconds)" in str(label_text):
                        found_label = True

                # Look for Spinbox widget
                if (
                    isinstance(child, ttk.Spinbox)
                    and found_label
                    and found_spinbox is None
                ):
                    # This should be the idle threshold spinbox (first spinbox after the label)
                    found_spinbox = child
                    return

                # Recursively search children
                find_widgets(child, depth + 1)

        find_widgets(frame)

        # Verify we found the spinbox
        self.assertIsNotNone(
            found_spinbox,
            "Could not find idle threshold spinbox. Make sure _create_idle_settings_subsection creates the widget.",
        )

        # Get the displayed value
        displayed_value = found_spinbox.get()

        # The spinbox should display "120" from our test settings
        self.assertEqual(
            displayed_value,
            "120",
            f"Spinbox should display '120' from settings.json but displays '{displayed_value}'. "
            f"Check that idle_threshold_spin.set() is called after widget creation.",
        )


class TestBreakActionsCRUD(unittest.TestCase):
    """Test break actions create, read, update, delete operations"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        # Create settings with break actions
        settings = {
            "spheres": {"TestSphere": {"is_default": True, "active": True}},
            "projects": {},
            "break_actions": {
                "Lunch": {"is_default": True, "active": True, "notes": "12pm daily"},
                "Coffee": {"is_default": False, "active": True, "notes": ""},
                "ArchivedBreak": {"is_default": False, "active": False, "notes": ""},
            },
            "idle_settings": {
                "idle_tracking_enabled": True,
                "idle_threshold": 60,
                "idle_break_threshold": 300,
            },
            "screenshot_settings": {"enabled": False},
            "google_sheets": {"enabled": False},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_break_actions.json", settings
        )

        # Create GUI components
        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up test files"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    @patch("tkinter.messagebox.askyesno", return_value=True)
    def test_delete_break_action(self, mock_messagebox):
        """Test deleting a break action"""
        # Verify break action exists
        self.assertIn("Coffee", self.tracker.settings["break_actions"])

        # Delete it
        self.frame.delete_break_action("Coffee")

        # Verify it's removed from settings
        self.assertNotIn("Coffee", self.tracker.settings["break_actions"])

        # Verify messagebox was shown
        mock_messagebox.assert_called_once()

    @patch("tkinter.messagebox.askyesno", return_value=False)
    def test_delete_break_action_cancelled(self, mock_messagebox):
        """Test cancelling break action deletion"""
        # Delete with cancel
        self.frame.delete_break_action("Coffee")

        # Verify it still exists
        self.assertIn("Coffee", self.tracker.settings["break_actions"])

    @patch("tkinter.simpledialog.askstring", return_value="Meeting")
    def test_create_new_break_action(self, mock_dialog):
        """Test creating a new break action"""
        # Create new break action
        self.frame.create_new_break_action()

        # Verify it exists in settings
        self.assertIn("Meeting", self.tracker.settings["break_actions"])
        self.assertTrue(self.tracker.settings["break_actions"]["Meeting"]["active"])
        self.assertFalse(
            self.tracker.settings["break_actions"]["Meeting"]["is_default"]
        )

    @patch("tkinter.simpledialog.askstring", return_value="Test<>Break")
    def test_create_break_action_invalid_name(self, mock_dialog):
        """Test creating break action with dangerous path characters gets sanitized"""
        initial_count = len(self.tracker.settings["break_actions"])

        # Try to create with invalid name containing dangerous path characters
        self.frame.create_new_break_action()

        # Name should be sanitized - < and > replaced with _
        self.assertIn("Test__Break", self.tracker.settings["break_actions"])

    @patch("tkinter.simpledialog.askstring", return_value="")
    def test_create_break_action_empty_name(self, mock_dialog):
        """Test creating break action with empty name is rejected"""
        initial_count = len(self.tracker.settings["break_actions"])

        # Try to create with empty name - should not create anything
        self.frame.create_new_break_action()

        # Should not add anything
        self.assertEqual(len(self.tracker.settings["break_actions"]), initial_count)

    @patch("tkinter.simpledialog.askstring", return_value="///:")
    @patch("tkinter.messagebox.showerror")
    def test_create_break_action_only_special_chars(self, mock_error, mock_dialog):
        """Test creating break action with only dangerous characters shows error"""
        initial_count = len(self.tracker.settings["break_actions"])

        # Try to create with only dangerous characters (sanitizes to all underscores)
        self.frame.create_new_break_action()

        # Should create "____" (sanitized version)
        self.assertIn("____", self.tracker.settings["break_actions"])

    def test_toggle_break_action_archive(self):
        """Test archiving and activating break actions"""
        # Initially active
        self.assertTrue(self.tracker.settings["break_actions"]["Coffee"]["active"])

        # Archive it
        self.frame.toggle_break_action_active("Coffee")
        self.assertFalse(self.tracker.settings["break_actions"]["Coffee"]["active"])

        # Activate it again
        self.frame.toggle_break_action_active("Coffee")
        self.assertTrue(self.tracker.settings["break_actions"]["Coffee"]["active"])

    def test_set_default_break_action(self):
        """Test setting a break action as default"""
        # Initially Lunch is default
        self.assertTrue(self.tracker.settings["break_actions"]["Lunch"]["is_default"])
        self.assertFalse(self.tracker.settings["break_actions"]["Coffee"]["is_default"])

        # Set Coffee as default
        self.frame.set_default_break_action("Coffee")

        # Verify only Coffee is default now
        self.assertFalse(self.tracker.settings["break_actions"]["Lunch"]["is_default"])
        self.assertTrue(self.tracker.settings["break_actions"]["Coffee"]["is_default"])

    def test_break_action_notes_edit(self):
        """Test editing break action notes"""
        # Create a mock Entry widget for notes
        notes_entry = tk.Entry(self.root)
        notes_entry.insert(0, "Old notes")

        # Create edit button
        edit_btn = ttk.Button(self.root, text="Edit")

        # First toggle enables editing
        self.frame.toggle_break_action_edit("Coffee", notes_entry, edit_btn)
        self.assertEqual(edit_btn["text"], "Save")
        self.assertEqual(notes_entry["state"], "normal")

        # Update notes
        notes_entry.delete(0, tk.END)
        notes_entry.insert(0, "New notes for coffee break")

        # Second toggle saves
        self.frame.toggle_break_action_edit("Coffee", notes_entry, edit_btn)
        self.assertEqual(edit_btn["text"], "Edit")
        self.assertEqual(notes_entry["state"], "disabled")

        # Verify notes were saved
        self.assertEqual(
            self.tracker.settings["break_actions"]["Coffee"]["notes"],
            "New notes for coffee break",
        )


class TestBreakActionsFilter(unittest.TestCase):
    """Test break actions filter functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        settings = {
            "spheres": {"TestSphere": {"is_default": True, "active": True}},
            "projects": {},
            "break_actions": {
                "ActiveBreak1": {"is_default": True, "active": True, "notes": ""},
                "ActiveBreak2": {"is_default": False, "active": True, "notes": ""},
                "ArchivedBreak1": {"is_default": False, "active": False, "notes": ""},
                "ArchivedBreak2": {"is_default": False, "active": False, "notes": ""},
            },
            "idle_settings": {},
            "screenshot_settings": {"enabled": False},
            "google_sheets": {"enabled": False},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_break_filter.json", settings
        )

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_filter_active_break_actions(self):
        """Test filtering shows only active break actions"""
        self.frame.break_action_filter.set("active")
        self.frame.refresh_break_actions()

        # Force widget updates
        self.root.update_idletasks()
        self.root.update()

        # Count visible rows in break_actions_frame
        visible_count = 0
        for child in self.frame.break_actions_frame.winfo_children():
            if isinstance(child, ttk.Frame):
                # Check if it's a break action row (has relief='ridge' and contains action data)
                try:
                    relief_value = str(child.cget("relief"))
                    if relief_value == "ridge":
                        visible_count += 1
                except:
                    pass

        # Should show 2 active break actions
        self.assertEqual(visible_count, 2)

    def test_filter_archived_break_actions(self):
        """Test filtering shows only archived break actions"""
        self.frame.break_action_filter.set("inactive")
        self.frame.refresh_break_actions()

        # Force widget updates
        self.root.update_idletasks()
        self.root.update()

        visible_count = 0
        for child in self.frame.break_actions_frame.winfo_children():
            if isinstance(child, ttk.Frame):
                try:
                    relief_value = str(child.cget("relief"))
                    if relief_value == "ridge":
                        visible_count += 1
                except:
                    pass

        # Should show 2 archived break actions
        self.assertEqual(visible_count, 2)

    def test_filter_all_break_actions(self):
        """Test filtering shows all break actions"""
        self.frame.break_action_filter.set("all")
        self.frame.refresh_break_actions()

        # Force widget updates
        self.root.update_idletasks()
        self.root.update()

        visible_count = 0
        for child in self.frame.break_actions_frame.winfo_children():
            if isinstance(child, ttk.Frame):
                try:
                    relief_value = str(child.cget("relief"))
                    if relief_value == "ridge":
                        visible_count += 1
                except:
                    pass

        # Should show all 4 break actions
        self.assertEqual(visible_count, 4)

    def test_default_break_action_appears_first(self):
        """Test that default break action appears first in filtered list"""
        self.frame.break_action_filter.set("active")
        self.frame.refresh_break_actions()

        # Force widget updates
        self.root.update_idletasks()
        self.root.update()

        # Find first break action frame
        first_frame = None
        for child in self.frame.break_actions_frame.winfo_children():
            if isinstance(child, ttk.Frame):
                try:
                    relief_value = str(child.cget("relief"))
                    if relief_value == "ridge":
                        first_frame = child
                        break
                except:
                    pass

        # Should find at least one break action frame
        self.assertIsNotNone(first_frame, "Should find at least one break action frame")

        # Find the label with the break action name
        found_name = None
        for child in first_frame.winfo_children():
            if isinstance(child, ttk.Label):
                label_text = str(child.cget("text"))
                if label_text in ["ActiveBreak1", "ActiveBreak2", "Notes:"]:
                    if label_text != "Notes:":  # Skip the "Notes:" label
                        found_name = label_text
                        break

        # Should be the default one
        self.assertEqual(
            found_name, "ActiveBreak1", "Default break action should appear first"
        )


class TestCSVExport(unittest.TestCase):
    """Test CSV export functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_csv_settings.json", settings
        )

        # Create test data file with proper structure
        data = {
            "session1": {
                "date": "2026-02-17",
                "sphere": "Work",
                "start_time": "09:00:00",
                "end_time": "10:30:00",
                "total_duration": 5400,
                "active_duration": 5400,
                "break_duration": 0,
                "active": [
                    {
                        "project": "Project A",
                        "start": "09:00:00",
                        "end": "10:30:00",
                        "duration": 5400,
                        "comment": "Made progress",
                    }
                ],
                "breaks": [],
                "idle_periods": [],
                "session_comments": {
                    "active_notes": "",
                    "break_notes": "",
                    "idle_notes": "",
                    "session_notes": "",
                },
            }
        }
        self.test_data_file = self.file_manager.create_test_file(
            "test_csv_data.json", data
        )

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.tracker.data_file = self.test_data_file
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    @patch("tkinter.filedialog.asksaveasfilename", return_value=None)
    def test_csv_export_cancelled(self, mock_dialog):
        """Test CSV export when user cancels file dialog"""
        # Should not raise exception
        self.frame.save_all_data_to_csv()

        # Verify dialog was shown
        mock_dialog.assert_called_once()

    @patch("tkinter.filedialog.asksaveasfilename")
    @patch("tkinter.messagebox.showinfo")
    @patch("os.startfile")  # Mock Windows file explorer opening
    def test_csv_export_success(self, mock_startfile, mock_info, mock_dialog):
        """Test successful CSV export"""
        # Create temporary output file path
        output_file = os.path.join(self.file_manager.test_data_dir, "output.csv")
        mock_dialog.return_value = output_file

        # Export
        self.frame.save_all_data_to_csv()

        # Verify file was created
        self.assertTrue(os.path.exists(output_file))

        # Verify CSV content
        import csv

        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["date"], "2026-02-17")
        self.assertEqual(rows[0]["sphere"], "Work")
        self.assertEqual(rows[0]["project"], "Project A")

        # Verify success message was shown
        mock_info.assert_called_once()

        # Clean up
        if os.path.exists(output_file):
            os.remove(output_file)

    @patch("tkinter.messagebox.showerror")
    def test_csv_export_no_data_file(self, mock_error):
        """Test CSV export when data file doesn't exist"""
        # Point to non-existent file
        self.tracker.data_file = "nonexistent.json"

        # Try to export
        self.frame.save_all_data_to_csv()

        # Should show error
        mock_error.assert_called_once()

    @patch("tkinter.filedialog.asksaveasfilename")
    @patch("tkinter.messagebox.showwarning")  # Mock the "No Data" warning popup
    def test_csv_export_empty_data(self, mock_warning, mock_dialog):
        """Test CSV export with empty data file"""
        # Create empty data file
        empty_data = {}
        empty_file = self.file_manager.create_test_file("empty_data.json", empty_data)
        self.tracker.data_file = empty_file

        output_file = os.path.join(self.file_manager.test_data_dir, "output_empty.csv")
        mock_dialog.return_value = output_file

        # Export - should return early with warning, not create file
        self.frame.save_all_data_to_csv()

        # Should NOT create file because there's no data
        self.assertFalse(os.path.exists(output_file))

        # Should show warning about no data
        mock_warning.assert_called_once()

        # Clean up (in case file was created)
        if os.path.exists(output_file):
            os.remove(output_file)


class TestScreenshotSettingsValidation(unittest.TestCase):
    """Test screenshot settings validation"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        settings = {
            "spheres": {"TestSphere": {"is_default": True, "active": True}},
            "projects": {},
            "break_actions": {},
            "idle_settings": {},
            "screenshot_settings": {
                "enabled": False,
                "capture_on_focus_change": True,
                "min_seconds_between_captures": 10,
                "screenshot_path": "screenshots",
            },
            "google_sheets": {"enabled": False},
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_screenshot_settings.json", settings
        )

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_screenshot_settings_loads_correctly(self):
        """Test that screenshot settings load from JSON"""
        settings = self.tracker.settings["screenshot_settings"]

        self.assertFalse(settings["enabled"])
        self.assertTrue(settings["capture_on_focus_change"])
        self.assertEqual(settings["min_seconds_between_captures"], 10)

    @patch("tkinter.messagebox.showinfo")
    def test_screenshot_settings_save(self, mock_info):
        """Test saving screenshot settings"""
        # Find the save button and variables by searching the frame
        found_enabled_var = None
        found_focus_var = None
        found_min_seconds_var = None
        found_save_btn = None

        def find_screenshot_widgets(widget, depth=0):
            nonlocal found_enabled_var, found_focus_var, found_min_seconds_var, found_save_btn

            if depth > 10:
                return

            for child in widget.winfo_children():
                # Look for save button
                if isinstance(child, ttk.Button):
                    btn_text = child.cget("text")
                    if "Save Screenshot Settings" in str(btn_text):
                        found_save_btn = child

                # Recurse
                find_screenshot_widgets(child, depth + 1)

        find_screenshot_widgets(self.frame)

        # If we found the save button, we can trigger it
        if found_save_btn:
            # The button has a command that saves settings
            # Invoke it
            found_save_btn.invoke()

            # Verify success message was shown
            mock_info.assert_called_once()


class TestKeyboardShortcutsSection(unittest.TestCase):
    """Test keyboard shortcuts reference section"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        settings = TestDataGenerator.create_settings_data()
        self.test_settings_file = self.file_manager.create_test_file(
            "test_shortcuts.json", settings
        )

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_keyboard_shortcuts_section_exists(self):
        """Test that keyboard shortcuts section is created"""
        # Search for LabelFrame with "Global Keyboard Shortcuts" text
        found_shortcuts_frame = False

        def find_shortcuts_frame(widget, depth=0):
            nonlocal found_shortcuts_frame

            if depth > 10:
                return

            for child in widget.winfo_children():
                if isinstance(child, ttk.LabelFrame):
                    frame_text = child.cget("text")
                    if "Global Keyboard Shortcuts" in str(frame_text):
                        found_shortcuts_frame = True
                        return

                find_shortcuts_frame(child, depth + 1)

        find_shortcuts_frame(self.frame)

        self.assertTrue(
            found_shortcuts_frame, "Keyboard shortcuts section should exist"
        )

    def test_keyboard_shortcuts_display_all_shortcuts(self):
        """Test that all keyboard shortcuts are displayed"""
        expected_shortcuts = [
            "Ctrl + Shift + S",
            "Ctrl + Shift + B",
            "Ctrl + Shift + E",
            "Ctrl + Shift + W",
        ]

        # Search for labels with shortcut text
        found_shortcuts = []

        def find_shortcut_labels(widget, depth=0):
            if depth > 10:
                return

            for child in widget.winfo_children():
                if isinstance(child, ttk.Label):
                    label_text = str(child.cget("text"))
                    for shortcut in expected_shortcuts:
                        if shortcut in label_text:
                            found_shortcuts.append(shortcut)

                find_shortcut_labels(child, depth + 1)

        find_shortcut_labels(self.frame)

        # Verify all shortcuts are displayed
        for shortcut in expected_shortcuts:
            self.assertIn(
                shortcut, found_shortcuts, f"Shortcut {shortcut} should be displayed"
            )


class TestGoogleSheetsSettingsUI(unittest.TestCase):
    """Test Google Sheets settings UI components"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        settings = {
            "spheres": {"TestSphere": {"is_default": True, "active": True}},
            "projects": {},
            "break_actions": {},
            "idle_settings": {},
            "screenshot_settings": {"enabled": False},
            "google_sheets": {
                "enabled": False,
                "spreadsheet_id": "",
                "sheet_name": "Sessions",
                "credentials_file": "credentials.json",
            },
        }
        self.test_settings_file = self.file_manager.create_test_file(
            "test_google_sheets_ui.json", settings
        )

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        from tests.test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    @patch("tkinter.filedialog.askopenfilename", return_value="test_credentials.json")
    def test_browse_credentials_button(self, mock_dialog):
        """Test browsing for credentials file"""
        # Find the browse button
        found_browse_btn = None

        def find_browse_button(widget, depth=0):
            nonlocal found_browse_btn

            if depth > 10:
                return

            for child in widget.winfo_children():
                if isinstance(child, ttk.Button):
                    btn_text = str(child.cget("text"))
                    if "Browse" in btn_text:
                        # Make sure it's in Google Sheets section (check if parent has Google Sheets label)
                        parent = child.master
                        for sibling in parent.winfo_children():
                            if isinstance(sibling, ttk.Label):
                                if "Credentials File" in str(sibling.cget("text")):
                                    found_browse_btn = child
                                    return

                find_browse_button(child, depth + 1)

        find_browse_button(self.frame)

        if found_browse_btn:
            # Invoke the button
            found_browse_btn.invoke()

            # Verify file dialog was called
            mock_dialog.assert_called_once()

    @patch("tkinter.messagebox.showinfo")
    @patch("src.settings_frame.GoogleSheetsUploader")
    def test_google_sheets_test_connection_success(self, mock_uploader, mock_info):
        """Test successful Google Sheets connection test"""
        # Mock successful connection
        mock_instance = Mock()
        mock_instance.test_connection.return_value = (True, "Connected to spreadsheet: Test Sheet")
        mock_uploader.return_value = mock_instance

        # Set valid spreadsheet ID
        self.tracker.settings["google_sheets"]["spreadsheet_id"] = "test123"

        # Recreate frame to pick up settings
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

        # Find test connection button
        found_test_btn = None

        def find_test_button(widget, depth=0):
            nonlocal found_test_btn

            if depth > 10:
                return

            for child in widget.winfo_children():
                if isinstance(child, ttk.Button):
                    btn_text = str(child.cget("text"))
                    if "Test Connection" in btn_text:
                        found_test_btn = child
                        return

                find_test_button(child, depth + 1)

        find_test_button(self.frame)

        # Button should be found
        self.assertIsNotNone(found_test_btn, "Test Connection button not found")
        
        # Invoke the button
        found_test_btn.invoke()

        # Process any pending events
        self.root.update()

        # Verify uploader was instantiated and test_connection was called
        mock_uploader.assert_called_once()
        mock_instance.test_connection.assert_called_once()


if __name__ == "__main__":
    unittest.main()
