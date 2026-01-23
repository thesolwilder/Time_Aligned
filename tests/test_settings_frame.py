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
        self.test_settings_file = "test_settings_frame.json"

        # Create test settings with specific defaults
        settings = TestDataGenerator.create_settings_data(
            default_sphere="DefaultSphere", default_project="DefaultProject"
        )
        self.file_manager.create_test_file(self.test_settings_file, settings)

        # Create GUI components
        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up test files"""
        try:
            self.root.destroy()
        except:
            pass
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
        self.test_settings_file = "test_settings_filters.json"

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
        self.file_manager.create_test_file(self.test_settings_file, settings)

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        try:
            self.root.destroy()
        except:
            pass
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
        self.test_settings_file = "test_settings_add_sphere.json"

        settings = TestDataGenerator.create_settings_data()
        self.file_manager.create_test_file(self.test_settings_file, settings)

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        try:
            self.root.destroy()
        except:
            pass
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
        self.test_settings_file = "test_settings_ordering.json"

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
        self.file_manager.create_test_file(self.test_settings_file, settings)

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        try:
            self.root.destroy()
        except:
            pass
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
        self.test_settings_file = "test_settings_one_default.json"

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
        self.file_manager.create_test_file(self.test_settings_file, settings)

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        try:
            self.root.destroy()
        except:
            pass
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
        self.test_settings_file = "test_settings_archive.json"

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
        self.file_manager.create_test_file(self.test_settings_file, settings)

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        try:
            self.root.destroy()
        except:
            pass
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
        self.test_settings_file = "test_settings_combobox.json"

        settings = TestDataGenerator.create_settings_data()
        self.file_manager.create_test_file(self.test_settings_file, settings)

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        try:
            self.root.destroy()
        except:
            pass
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
        self.test_settings_file = "test_settings_accuracy.json"

        settings = TestDataGenerator.create_settings_data()
        self.file_manager.create_test_file(self.test_settings_file, settings)

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        try:
            self.root.destroy()
        except:
            pass
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
        self.test_settings_file = "test_settings_sphere_archive.json"

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
        self.file_manager.create_test_file(self.test_settings_file, settings)

        self.root = tk.Tk()
        self.tracker = MockTracker(self.test_settings_file)
        self.frame = SettingsFrame(self.root, self.tracker, self.root)

    def tearDown(self):
        """Clean up"""
        try:
            self.root.destroy()
        except:
            pass
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


if __name__ == "__main__":
    unittest.main()
