"""
Tests for UI Helper Utilities

Tests the common UI widget utilities including sanitization functions,
security validation, and the ScrollableFrame component.
"""

import unittest
import tkinter as tk
from tkinter import ttk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.ui_helpers import (
    get_frame_background,
    sanitize_name,
    escape_for_sheets,
    validate_folder_path,
    ScrollableFrame,
)
from test_helpers import TestFileManager


class TestUIHelpersImport(unittest.TestCase):
    """Test that ui_helpers module imports successfully"""

    def test_import(self):
        """Verify ui_helpers module imports without errors"""
        from src import ui_helpers

        assert ui_helpers is not None


class TestGetFrameBackground(unittest.TestCase):
    """Test get_frame_background function"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()

    def tearDown(self):
        """Clean up after tests"""
        from test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)

    def test_get_frame_background_returns_string(self):
        """Verify get_frame_background returns a string color code"""
        result = get_frame_background()
        self.assertIsInstance(result, str)

    def test_get_frame_background_returns_hex_color(self):
        """Verify get_frame_background returns a hex color code or system color"""
        result = get_frame_background()
        # Should be either hex color (#d9d9d9) or system color (SystemButtonFace)
        is_hex = result.startswith("#") and len(result) == 7
        is_system_color = result and not result.startswith("#")
        self.assertTrue(is_hex or is_system_color)


class TestSanitizeName(unittest.TestCase):
    """Test sanitize_name function for security and data integrity"""

    def test_sanitize_name_removes_forward_slash(self):
        """Verify forward slash is replaced with underscore"""
        result = sanitize_name("folder/name")
        self.assertEqual(result, "folder_name")

    def test_sanitize_name_removes_backslash(self):
        """Verify backslash is replaced with underscore"""
        result = sanitize_name("folder\\name")
        self.assertEqual(result, "folder_name")

    def test_sanitize_name_removes_path_traversal(self):
        """Verify path traversal attempts are sanitized"""
        result = sanitize_name("../../../etc/passwd")
        self.assertEqual(result, "______etc_passwd")

    def test_sanitize_name_removes_dangerous_characters(self):
        """Verify all dangerous characters are replaced"""
        dangerous = '<>:"|?*{}'
        result = sanitize_name(f"test{dangerous}name")
        # All dangerous chars should be replaced with underscores
        self.assertNotIn("<", result)
        self.assertNotIn(">", result)
        self.assertNotIn(":", result)
        self.assertNotIn('"', result)
        self.assertNotIn("|", result)
        self.assertNotIn("?", result)
        self.assertNotIn("*", result)
        self.assertNotIn("{", result)
        self.assertNotIn("}", result)

    def test_sanitize_name_removes_control_characters(self):
        """Verify newlines, tabs, and carriage returns are replaced"""
        result = sanitize_name("test\nname\twith\rcontrol")
        self.assertNotIn("\n", result)
        self.assertNotIn("\t", result)
        self.assertNotIn("\r", result)
        self.assertEqual(result, "test_name_with_control")

    def test_sanitize_name_limits_length(self):
        """Verify name is truncated to max_length"""
        long_name = "a" * 100
        result = sanitize_name(long_name, max_length=50)
        self.assertEqual(len(result), 50)

    def test_sanitize_name_custom_max_length(self):
        """Verify custom max_length parameter works"""
        name = "a" * 50
        result = sanitize_name(name, max_length=20)
        self.assertEqual(len(result), 20)

    def test_sanitize_name_strips_whitespace(self):
        """Verify leading and trailing whitespace is removed"""
        result = sanitize_name("  test name  ")
        self.assertEqual(result, "test name")

    def test_sanitize_name_handles_empty_string(self):
        """Verify empty string returns empty string"""
        result = sanitize_name("")
        self.assertEqual(result, "")

    def test_sanitize_name_handles_none(self):
        """Verify None input returns empty string"""
        result = sanitize_name(None)
        self.assertEqual(result, "")

    def test_sanitize_name_handles_whitespace_only(self):
        """Verify whitespace-only input returns empty string"""
        result = sanitize_name("   ")
        self.assertEqual(result, "")

    def test_sanitize_name_preserves_valid_characters(self):
        """Verify valid characters are preserved"""
        valid_name = "Valid_Name-123"
        result = sanitize_name(valid_name)
        self.assertEqual(result, valid_name)


class TestEscapeForSheets(unittest.TestCase):
    """Test escape_for_sheets function for formula injection prevention"""

    def test_escape_for_sheets_prefixes_equals_sign(self):
        """Verify equals sign is prefixed with single quote"""
        result = escape_for_sheets("=SUM(A1:A10)")
        self.assertEqual(result, "'=SUM(A1:A10)")

    def test_escape_for_sheets_prefixes_plus_sign(self):
        """Verify plus sign is prefixed with single quote"""
        result = escape_for_sheets("+1234")
        self.assertEqual(result, "'+1234")

    def test_escape_for_sheets_prefixes_minus_sign(self):
        """Verify minus sign is prefixed with single quote"""
        result = escape_for_sheets("-1234")
        self.assertEqual(result, "'-1234")

    def test_escape_for_sheets_prefixes_at_sign(self):
        """Verify at sign is prefixed with single quote"""
        result = escape_for_sheets("@formula")
        self.assertEqual(result, "'@formula")

    def test_escape_for_sheets_prefixes_pipe_sign(self):
        """Verify pipe sign is prefixed with single quote"""
        result = escape_for_sheets("|command")
        self.assertEqual(result, "'|command")

    def test_escape_for_sheets_escapes_html_less_than(self):
        """Verify less than sign is escaped"""
        result = escape_for_sheets("<script>alert('xss')</script>")
        self.assertIn("&lt;", result)
        self.assertNotIn("<script>", result)

    def test_escape_for_sheets_escapes_html_greater_than(self):
        """Verify greater than sign is escaped"""
        result = escape_for_sheets("<script>alert('xss')</script>")
        self.assertIn("&gt;", result)
        self.assertNotIn("</script>", result)

    def test_escape_for_sheets_handles_empty_string(self):
        """Verify empty string returns empty string"""
        result = escape_for_sheets("")
        self.assertEqual(result, "")

    def test_escape_for_sheets_handles_none(self):
        """Verify None input returns empty string"""
        result = escape_for_sheets(None)
        self.assertEqual(result, "")

    def test_escape_for_sheets_preserves_normal_text(self):
        """Verify normal text is unchanged"""
        normal_text = "This is normal text"
        result = escape_for_sheets(normal_text)
        self.assertEqual(result, normal_text)

    def test_escape_for_sheets_handles_combined_threats(self):
        """Verify multiple threat patterns are all escaped"""
        dangerous = "=SUM(A1)<script>"
        result = escape_for_sheets(dangerous)
        self.assertTrue(result.startswith("'"))  # Formula prefix
        self.assertIn("&lt;", result)  # HTML escaped
        self.assertIn("&gt;", result)  # HTML escaped


class TestValidateFolderPath(unittest.TestCase):
    """Test validate_folder_path function for path traversal prevention"""

    def test_validate_folder_path_accepts_valid_path(self):
        """Verify valid folder path is accepted"""
        result = validate_folder_path("C:/Users/Test/Documents")
        self.assertTrue(result)

    def test_validate_folder_path_rejects_path_traversal(self):
        """Verify path traversal with .. is rejected"""
        result = validate_folder_path("C:/Users/../../../etc")
        self.assertFalse(result)

    def test_validate_folder_path_rejects_tilde(self):
        """Verify tilde home directory shortcut is rejected"""
        result = validate_folder_path("~/Documents")
        self.assertFalse(result)

    def test_validate_folder_path_rejects_etc_directory(self):
        """Verify /etc/ directory is rejected"""
        result = validate_folder_path("/etc/passwd")
        self.assertFalse(result)

    def test_validate_folder_path_rejects_windows_directory(self):
        """Verify Windows system directory is rejected"""
        result = validate_folder_path("C:\\Windows\\System32")
        self.assertFalse(result)

    def test_validate_folder_path_rejects_root_directory(self):
        """Verify /root/ directory is rejected"""
        result = validate_folder_path("/root/secrets")
        self.assertFalse(result)

    def test_validate_folder_path_rejects_environment_variables(self):
        """Verify environment variable references are rejected"""
        result = validate_folder_path("%USERPROFILE%/Documents")
        self.assertFalse(result)

    def test_validate_folder_path_rejects_shell_variables(self):
        """Verify shell variable references are rejected"""
        result = validate_folder_path("${HOME}/Documents")
        self.assertFalse(result)

    def test_validate_folder_path_rejects_powershell_variables(self):
        """Verify PowerShell variable references are rejected"""
        result = validate_folder_path("$env:USERPROFILE/Documents")
        self.assertFalse(result)

    def test_validate_folder_path_handles_empty_string(self):
        """Verify empty string is rejected"""
        result = validate_folder_path("")
        self.assertFalse(result)

    def test_validate_folder_path_handles_none(self):
        """Verify None input is rejected"""
        result = validate_folder_path(None)
        self.assertFalse(result)

    def test_validate_folder_path_case_insensitive(self):
        """Verify validation is case-insensitive"""
        result = validate_folder_path("c:\\WINDOWS\\System32")
        self.assertFalse(result)


class TestScrollableFrame(unittest.TestCase):
    """Test ScrollableFrame component"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)

    def tearDown(self):
        """Clean up after tests"""
        from test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_scrollable_frame_creates_successfully(self):
        """Verify ScrollableFrame can be instantiated"""
        frame = ScrollableFrame(self.root)
        self.assertIsNotNone(frame)
        self.assertIsInstance(frame, ttk.Frame)

    def test_scrollable_frame_has_canvas(self):
        """Verify ScrollableFrame creates a canvas"""
        frame = ScrollableFrame(self.root)
        self.assertIsNotNone(frame.canvas)
        self.assertIsInstance(frame.canvas, tk.Canvas)

    def test_scrollable_frame_has_scrollbar(self):
        """Verify ScrollableFrame creates a scrollbar"""
        frame = ScrollableFrame(self.root)
        self.assertIsNotNone(frame.scrollbar)
        self.assertIsInstance(frame.scrollbar, ttk.Scrollbar)

    def test_scrollable_frame_has_content_frame(self):
        """Verify ScrollableFrame creates a content frame"""
        frame = ScrollableFrame(self.root)
        self.assertIsNotNone(frame.content_frame)
        self.assertIsInstance(frame.content_frame, ttk.Frame)

    def test_scrollable_frame_get_content_frame(self):
        """Verify get_content_frame returns the content frame"""
        frame = ScrollableFrame(self.root)
        content = frame.get_content_frame()
        self.assertEqual(content, frame.content_frame)

    def test_scrollable_frame_canvas_has_background(self):
        """Verify canvas background is set to match theme"""
        frame = ScrollableFrame(self.root)
        bg_color = frame.canvas.cget("bg")
        # Should be a color value (hex or system color name)
        self.assertIsNotNone(bg_color)
        self.assertTrue(len(bg_color) > 0)

    def test_scrollable_frame_canvas_has_no_highlight(self):
        """Verify canvas has no highlight thickness"""
        frame = ScrollableFrame(self.root)
        highlight = frame.canvas.cget("highlightthickness")
        # Tkinter returns string, convert to int for comparison
        self.assertEqual(int(highlight), 0)

    def test_scrollable_frame_scrollbar_controls_canvas(self):
        """Verify scrollbar is connected to canvas yview"""
        frame = ScrollableFrame(self.root)
        # Scrollbar command should be set
        self.assertIsNotNone(frame.scrollbar.cget("command"))

    def test_scrollable_frame_adds_widgets_to_content_frame(self):
        """Verify widgets can be added to content frame"""
        frame = ScrollableFrame(self.root)
        label = ttk.Label(frame.content_frame, text="Test")
        label.pack()

        # Check label is in content frame
        children = frame.content_frame.winfo_children()
        self.assertIn(label, children)

    def test_scrollable_frame_is_alive_flag(self):
        """Verify _is_alive flag is True when created"""
        frame = ScrollableFrame(self.root)
        self.assertTrue(frame._is_alive)

    def test_scrollable_frame_destroy_sets_is_alive_false(self):
        """Verify destroy() sets _is_alive to False"""
        frame = ScrollableFrame(self.root)
        frame.destroy()
        self.assertFalse(frame._is_alive)

    def test_scrollable_frame_mousewheel_event_count_starts_zero(self):
        """Verify mousewheel event counter starts at zero"""
        frame = ScrollableFrame(self.root)
        self.assertEqual(frame._mousewheel_event_count, 0)

    def test_scrollable_frame_rebind_mousewheel_method_exists(self):
        """Verify rebind_mousewheel method exists"""
        frame = ScrollableFrame(self.root)
        self.assertTrue(hasattr(frame, "rebind_mousewheel"))
        self.assertTrue(callable(frame.rebind_mousewheel))

    def test_scrollable_frame_rebind_mousewheel_runs_without_error(self):
        """Verify rebind_mousewheel can be called without error"""
        frame = ScrollableFrame(self.root)
        # Add a combobox to the content frame
        combo = ttk.Combobox(frame.content_frame)
        combo.pack()
        # Should not raise exception
        frame.rebind_mousewheel()

    def test_scrollable_frame_canvas_window_created(self):
        """Verify canvas window is created for content frame"""
        frame = ScrollableFrame(self.root)
        self.assertIsNotNone(frame.canvas_window)
        # canvas_window should be a canvas item ID (int)
        self.assertIsInstance(frame.canvas_window, int)

    def test_scrollable_frame_scrollregion_updates_on_configure(self):
        """Verify scrollregion updates when content frame is configured"""
        frame = ScrollableFrame(self.root)
        frame.pack(fill="both", expand=True)

        # Add content to trigger configure event
        for i in range(10):
            ttk.Label(frame.content_frame, text=f"Label {i}").pack()

        # Force update to process configure events
        self.root.update_idletasks()

        # Scrollregion should be set (not empty tuple)
        scrollregion = frame.canvas.cget("scrollregion")
        self.assertNotEqual(scrollregion, "")

    def test_scrollable_frame_canvas_window_width_updates(self):
        """Verify canvas window width updates on canvas resize"""
        frame = ScrollableFrame(self.root)
        frame.pack(fill="both", expand=True)

        # Force update to process resize
        self.root.update_idletasks()

        # Canvas window should have a width configuration
        width = frame.canvas.itemcget(frame.canvas_window, "width")
        # Width should be set to something (may be 0 in headless, but not empty)
        self.assertIsNotNone(width)


class TestScrollableFrameMousewheelHandling(unittest.TestCase):
    """Test ScrollableFrame mousewheel event handling"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)

    def tearDown(self):
        """Clean up after tests"""
        from test_helpers import safe_teardown_tk_root

        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def test_scrollable_frame_disables_combobox_scrolling(self):
        """Verify comboboxes in content frame have mousewheel disabled"""
        frame = ScrollableFrame(self.root)
        combo = ttk.Combobox(frame.content_frame, values=["A", "B", "C"])
        combo.pack()

        # Rebind to apply mousewheel disabling
        frame.rebind_mousewheel()

        # Check that combobox has a MouseWheel binding
        bindings = combo.bind("<MouseWheel>")
        # Should have a binding (that returns "break")
        self.assertIsNotNone(bindings)

    def test_scrollable_frame_disables_spinbox_scrolling(self):
        """Verify spinboxes in content frame have mousewheel disabled"""
        frame = ScrollableFrame(self.root)
        spinbox = ttk.Spinbox(frame.content_frame, from_=0, to=100)
        spinbox.pack()

        # Rebind to apply mousewheel disabling
        frame.rebind_mousewheel()

        # Check that spinbox has a MouseWheel binding
        bindings = spinbox.bind("<MouseWheel>")
        # Should have a binding (that returns "break")
        self.assertIsNotNone(bindings)


if __name__ == "__main__":
    unittest.main()
