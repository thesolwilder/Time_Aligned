"""
Tests for Analysis Frame "Load More" functionality.

The "Load More" button allows incremental loading of timeline data
instead of loading all periods at once (which freezes UI for 60s with 682 periods).

Design:
- Load first 50 periods immediately (fast)
- Show "Load More" button at bottom
- Each click loads next 50 periods
- Button shows progress: "Showing 50 of 682 total"
- When all loaded: "All 682 periods loaded"
"""

import unittest
import tkinter as tk
from tkinter import ttk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time_tracker import TimeTracker
from src.analysis_frame import AnalysisFrame
from tests.test_helpers import TestFileManager, TestDataGenerator, safe_teardown_tk_root


class TestImport(unittest.TestCase):
    """Smoke test - verify module imports"""

    def test_import(self):
        """Verify analysis_frame imports without errors"""
        from src.analysis_frame import AnalysisFrame

        assert AnalysisFrame is not None


class TestLoadMoreButton(unittest.TestCase):
    """Test Load More button functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()

        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)

    def tearDown(self):
        """Clean up after tests"""
        safe_teardown_tk_root(self.root)
        self.file_manager.cleanup()

    def _create_analysis_frame_with_data(self, num_periods):
        """Helper to create analysis frame with test data and proper filters

        Args:
            num_periods: Number of periods to generate in test data

        Returns:
            tuple: (tracker, frame) ready for testing
        """
        test_data = TestDataGenerator.create_test_data_with_n_periods(num_periods)
        settings = TestDataGenerator.create_settings_data()

        test_data_file = self.file_manager.create_test_file("test_data.json", test_data)
        test_settings_file = self.file_manager.create_test_file(
            "test_settings.json", settings
        )

        tracker = TimeTracker(self.root)
        tracker.data_file = test_data_file
        tracker.settings_file = test_settings_file
        tracker.settings = tracker.get_settings()
        tracker.data = test_data

        content_frame = ttk.Frame(self.root)
        content_frame.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        frame = AnalysisFrame(content_frame, tracker, self.root)
        self.root.update()

        # Set filters to include all test data
        frame.sphere_var.set("All Spheres")
        frame.project_var.set("All Projects")
        frame.selected_card = 2  # "All Time"

        return tracker, frame

    def test_load_more_button_exists_on_initial_load(self):
        """
        Test that "Load More" button appears at bottom of timeline
        when there are more than 50 periods to display.
        """
        tracker, frame = self._create_analysis_frame_with_data(100)

        # Trigger timeline update
        frame.update_timeline()
        self.root.update()

        # Check for Load More button in timeline_frame
        widgets = frame.timeline_frame.winfo_children()
        load_more_found = False
        for widget in widgets:
            # Check if widget is a button
            if isinstance(widget, (tk.Button, ttk.Button)):
                button_text = widget.cget("text")
                if "Load" in button_text and "More" in button_text:
                    load_more_found = True
                    break
            # Check if widget is a frame (button might be inside)
            elif isinstance(widget, (tk.Frame, ttk.Frame)):
                for child in widget.winfo_children():
                    if isinstance(child, (tk.Button, ttk.Button)):
                        button_text = child.cget("text")
                        if "Load" in button_text and "More" in button_text:
                            load_more_found = True
                            break
                if load_more_found:
                    break

        self.assertTrue(
            load_more_found,
            "Load More button should exist when there are more than 50 periods",
        )

    def test_shows_only_50_periods_initially(self):
        """
        Test that only first 50 periods are rendered initially,
        even when 200 total periods exist.
        """
        tracker, frame = self._create_analysis_frame_with_data(200)

        # Trigger timeline update
        frame.update_timeline()
        self.root.update()

        # Count number of period rows rendered
        # (Each period creates a frame with multiple labels)
        # Look for frames in timeline_frame (each period = 1 frame)
        timeline_widgets = frame.timeline_frame.winfo_children()
        period_frames = [
            w for w in timeline_widgets if isinstance(w, (tk.Frame, ttk.Frame))
        ]

        # Should have ~50 period frames (plus maybe header and Load More button frame)
        self.assertLess(
            len(period_frames),
            70,  # Allow for header, button container
            "Should render approximately 50 periods, not all 200",
        )
        self.assertGreater(
            len(period_frames),
            45,  # At least 45 period frames
            "Should render at least 45-50 periods initially",
        )

    def test_load_more_button_shows_progress(self):
        """
        Test that Load More button shows progress like:
        "Load 50 More (50 of 200 shown)"
        """
        tracker, frame = self._create_analysis_frame_with_data(200)

        frame.update_timeline()
        self.root.update()

        # Find Load More button (it's inside a frame container)
        widgets = frame.timeline_frame.winfo_children()

        load_more_button = None
        for widget in widgets:
            # Check if widget is a button
            if isinstance(widget, (tk.Button, ttk.Button)):
                button_text = widget.cget("text")
                if "Load" in button_text and "More" in button_text:
                    load_more_button = widget
                    break
            # Check if widget is a frame (button might be inside)
            elif isinstance(widget, (tk.Frame, ttk.Frame)):
                for child in widget.winfo_children():
                    if isinstance(child, (tk.Button, ttk.Button)):
                        button_text = child.cget("text")
                        if "Load" in button_text and "More" in button_text:
                            load_more_button = child
                            break
                if load_more_button:
                    break

        self.assertIsNotNone(load_more_button, "Load More button should exist")

        # Check button text shows progress
        button_text = load_more_button.cget("text")
        self.assertIn("50", button_text, "Button should show 50 periods loaded/to load")
        self.assertIn("200", button_text, "Button should show total 200 periods")


if __name__ == "__main__":
    unittest.main()
