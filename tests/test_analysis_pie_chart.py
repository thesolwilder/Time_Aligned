"""
Tests for Analysis Frame Pie Chart Feature

TDD - tests written BEFORE implementation.

Verifies:
- draw_pie_chart() creates correct arc and text items on a tk.Canvas
- Arc colors match tray icon constants (green active, amber break)
- Percentage labels rendered inside each slice
- Edge cases: zero active, zero break, both zero
- Integration: each card has a pie_canvas attribute
- Integration: Active/Break labels use tray-matching foreground colors
"""

import math
import sys
import os
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ---------------------------------------------------------------------------
# 1. Import smoke tests
# ---------------------------------------------------------------------------


class TestPieChartImport(unittest.TestCase):
    """Verify new symbols are importable before any other tests run."""

    def test_draw_pie_chart_importable(self):
        """draw_pie_chart must be importable from src.analysis_frame."""
        from src.analysis_frame import draw_pie_chart

        self.assertIsNotNone(draw_pie_chart)

    def test_pie_chart_size_constant_importable(self):
        """PIE_CHART_SIZE constant must be importable from src.constants."""
        from src.constants import PIE_CHART_SIZE

        self.assertIsInstance(PIE_CHART_SIZE, int)
        self.assertGreater(PIE_CHART_SIZE, 0)

    def test_pie_chart_margin_constant_importable(self):
        """PIE_CHART_MARGIN constant must be importable from src.constants."""
        from src.constants import PIE_CHART_MARGIN

        self.assertIsInstance(PIE_CHART_MARGIN, int)
        self.assertGreater(PIE_CHART_MARGIN, 0)

    def test_pie_text_min_percent_importable(self):
        """PIE_TEXT_MIN_PERCENT constant must be importable from src.constants."""
        from src.constants import PIE_TEXT_MIN_PERCENT

        self.assertIsInstance(PIE_TEXT_MIN_PERCENT, int)
        self.assertGreater(PIE_TEXT_MIN_PERCENT, 0)


# ---------------------------------------------------------------------------
# 2. Unit tests for draw_pie_chart()
# ---------------------------------------------------------------------------


class TestDrawPieChartUnit(unittest.TestCase):
    """Unit tests for the standalone draw_pie_chart() function."""

    def setUp(self):
        self.root = tk.Tk()
        self.addCleanup(self.root.destroy)
        from src.constants import PIE_CHART_SIZE

        self.size = PIE_CHART_SIZE
        self.canvas = tk.Canvas(self.root, width=self.size, height=self.size)

    def _arcs(self):
        return [
            item for item in self.canvas.find_all() if self.canvas.type(item) == "arc"
        ]

    def _texts(self):
        return [
            item for item in self.canvas.find_all() if self.canvas.type(item) == "text"
        ]

    # -- Two-section chart ---------------------------------------------------

    def test_creates_two_arcs_for_mixed_values(self):
        """Two arc items created when both active and break are > 0."""
        from src.analysis_frame import draw_pie_chart

        draw_pie_chart(self.canvas, active_secs=3600, break_secs=1200)
        self.assertEqual(len(self._arcs()), 2)

    def test_arc_colors_match_tray_active_and_break(self):
        """Arc fill colors must match COLOR_TRAY_ACTIVE and COLOR_TRAY_BREAK."""
        from src.analysis_frame import draw_pie_chart
        from src.constants import COLOR_TRAY_ACTIVE, COLOR_TRAY_BREAK

        draw_pie_chart(self.canvas, active_secs=3600, break_secs=1200)
        fill_colors = {
            self.canvas.itemcget(item, "fill").lower() for item in self._arcs()
        }
        self.assertIn(COLOR_TRAY_ACTIVE.lower(), fill_colors)
        self.assertIn(COLOR_TRAY_BREAK.lower(), fill_colors)

    def test_percentage_texts_created_for_large_slices(self):
        """At least two text items created when both slices are >= min percent."""
        from src.analysis_frame import draw_pie_chart

        # 75% / 25% — both above PIE_TEXT_MIN_PERCENT (10%)
        draw_pie_chart(self.canvas, active_secs=3600, break_secs=1200)
        self.assertGreaterEqual(len(self._texts()), 2)

    def test_percentage_text_values_are_correct(self):
        """Percentage text values match the actual proportions."""
        from src.analysis_frame import draw_pie_chart

        # 3600 / (3600+1200) = 75%,  1200/4800 = 25%
        draw_pie_chart(self.canvas, active_secs=3600, break_secs=1200)
        combined_text = " ".join(
            self.canvas.itemcget(item, "text") for item in self._texts()
        )
        self.assertIn("75%", combined_text)
        self.assertIn("25%", combined_text)

    def test_percentage_text_sum_to_100(self):
        """Percentages inside the chart always sum to 100."""
        from src.analysis_frame import draw_pie_chart

        draw_pie_chart(self.canvas, active_secs=1800, break_secs=600)
        percents = []
        for item in self._texts():
            raw = self.canvas.itemcget(item, "text")
            if raw.endswith("%"):
                percents.append(int(raw[:-1]))
        self.assertEqual(sum(percents), 100)

    # -- Zero-break edge case ------------------------------------------------

    def test_zero_break_draws_one_arc(self):
        """When break_secs == 0, a single active arc fills the circle."""
        from src.analysis_frame import draw_pie_chart

        draw_pie_chart(self.canvas, active_secs=3600, break_secs=0)
        self.assertEqual(len(self._arcs()), 1)

    def test_zero_break_arc_color_is_active_green(self):
        """Full-circle arc color matches COLOR_TRAY_ACTIVE when break == 0."""
        from src.analysis_frame import draw_pie_chart
        from src.constants import COLOR_TRAY_ACTIVE

        draw_pie_chart(self.canvas, active_secs=3600, break_secs=0)
        fill = self.canvas.itemcget(self._arcs()[0], "fill").lower()
        self.assertEqual(fill, COLOR_TRAY_ACTIVE.lower())

    # -- Zero-active edge case -----------------------------------------------

    def test_zero_active_draws_one_arc(self):
        """When active_secs == 0, a single break arc fills the circle."""
        from src.analysis_frame import draw_pie_chart

        draw_pie_chart(self.canvas, active_secs=0, break_secs=3600)
        self.assertEqual(len(self._arcs()), 1)

    def test_zero_active_arc_color_is_break_amber(self):
        """Full-circle arc color matches COLOR_TRAY_BREAK when active == 0."""
        from src.analysis_frame import draw_pie_chart
        from src.constants import COLOR_TRAY_BREAK

        draw_pie_chart(self.canvas, active_secs=0, break_secs=3600)
        fill = self.canvas.itemcget(self._arcs()[0], "fill").lower()
        self.assertEqual(fill, COLOR_TRAY_BREAK.lower())

    # -- Both-zero edge case -------------------------------------------------

    def test_both_zero_draws_one_gray_arc(self):
        """When both are zero, exactly one arc is drawn (gray 'No data')."""
        from src.analysis_frame import draw_pie_chart

        draw_pie_chart(self.canvas, active_secs=0, break_secs=0)
        self.assertEqual(len(self._arcs()), 1)

    def test_both_zero_shows_no_data_text(self):
        """When both are zero, 'No data' text is displayed."""
        from src.analysis_frame import draw_pie_chart

        draw_pie_chart(self.canvas, active_secs=0, break_secs=0)
        combined = " ".join(
            self.canvas.itemcget(item, "text") for item in self._texts()
        )
        self.assertIn("No data", combined)

    def test_both_zero_no_percentage_text(self):
        """No percentage text (like '75%') is shown when both are zero."""
        from src.analysis_frame import draw_pie_chart

        draw_pie_chart(self.canvas, active_secs=0, break_secs=0)
        combined = " ".join(
            self.canvas.itemcget(item, "text") for item in self._texts()
        )
        self.assertNotIn("%", combined)

    # -- Redraw idempotency --------------------------------------------------

    def test_redraw_replaces_previous_items(self):
        """Calling draw_pie_chart twice produces the same item count."""
        from src.analysis_frame import draw_pie_chart

        draw_pie_chart(self.canvas, active_secs=3600, break_secs=1200)
        count_first = len(self.canvas.find_all())

        draw_pie_chart(self.canvas, active_secs=1200, break_secs=3600)
        count_second = len(self.canvas.find_all())

        self.assertEqual(count_first, count_second)

    # -- Small-slice text suppression ----------------------------------------

    def test_tiny_slice_suppresses_percentage_text(self):
        """A slice below PIE_TEXT_MIN_PERCENT does not receive a text label."""
        from src.analysis_frame import draw_pie_chart
        from src.constants import PIE_TEXT_MIN_PERCENT

        # 2% active, 98% break — active pct below threshold
        draw_pie_chart(self.canvas, active_secs=20, break_secs=980)
        combined = " ".join(
            self.canvas.itemcget(item, "text") for item in self._texts()
        )
        # 2% should be suppressed; 98% should still appear
        self.assertNotIn("2%", combined)
        self.assertIn("98%", combined)


# ---------------------------------------------------------------------------
# 3. Integration tests — AnalysisFrame card structure
# ---------------------------------------------------------------------------


class TestPieChartIntegration(unittest.TestCase):
    """Integration tests: pie canvas present in cards and labels use tray colors."""

    def _make_mock_tracker(self):
        tracker = Mock()
        tracker.settings = {
            "analysis_settings": {
                "card_ranges": ["Last 7 Days", "Last 30 Days", "All Time"]
            },
            "spheres": {},
            "projects": {},
            "break_actions": {},
        }
        tracker.settings_file = "test_settings.json"
        tracker.load_data = Mock(return_value={})
        tracker._get_default_sphere.return_value = "All Spheres"
        tracker._get_default_project.return_value = "All Projects"
        return tracker

    def setUp(self):
        self.root = tk.Tk()
        self.addCleanup(self.root.destroy)

    def _make_frame(self):
        from src.analysis_frame import AnalysisFrame

        parent = ttk.Frame(self.root)
        return AnalysisFrame(parent, self._make_mock_tracker(), self.root)

    def test_each_card_has_pie_canvas_attribute(self):
        """All three cards must expose a pie_canvas attribute."""
        frame = self._make_frame()
        for index, card in enumerate(frame.cards):
            with self.subTest(card=index):
                self.assertTrue(
                    hasattr(card, "pie_canvas"),
                    f"Card {index} missing pie_canvas attribute",
                )

    def test_pie_canvas_is_tk_canvas(self):
        """pie_canvas attribute must be a tk.Canvas instance."""
        frame = self._make_frame()
        for index, card in enumerate(frame.cards):
            with self.subTest(card=index):
                self.assertIsInstance(
                    card.pie_canvas,
                    tk.Canvas,
                    f"Card {index} pie_canvas is not a tk.Canvas",
                )

    def test_pie_canvas_has_correct_size(self):
        """pie_canvas width and height must equal PIE_CHART_SIZE."""
        from src.constants import PIE_CHART_SIZE

        frame = self._make_frame()
        for index, card in enumerate(frame.cards):
            with self.subTest(card=index):
                self.assertEqual(
                    int(card.pie_canvas["width"]),
                    PIE_CHART_SIZE,
                    f"Card {index} pie_canvas width != PIE_CHART_SIZE",
                )
                self.assertEqual(
                    int(card.pie_canvas["height"]),
                    PIE_CHART_SIZE,
                    f"Card {index} pie_canvas height != PIE_CHART_SIZE",
                )

    def test_active_label_foreground_matches_tray_active(self):
        """Active time label foreground must match COLOR_TRAY_ACTIVE."""
        from src.constants import COLOR_TRAY_ACTIVE

        frame = self._make_frame()
        for index, card in enumerate(frame.cards):
            with self.subTest(card=index):
                fg = str(card.active_label.cget("foreground")).lower()
                self.assertEqual(
                    fg,
                    COLOR_TRAY_ACTIVE.lower(),
                    f"Card {index} active_label foreground {fg!r} != {COLOR_TRAY_ACTIVE!r}",
                )

    def test_break_label_foreground_matches_tray_break(self):
        """Break time label foreground must match COLOR_TRAY_BREAK."""
        from src.constants import COLOR_TRAY_BREAK

        frame = self._make_frame()
        for index, card in enumerate(frame.cards):
            with self.subTest(card=index):
                fg = str(card.break_label.cget("foreground")).lower()
                self.assertEqual(
                    fg,
                    COLOR_TRAY_BREAK.lower(),
                    f"Card {index} break_label foreground {fg!r} != {COLOR_TRAY_BREAK!r}",
                )

    def test_pie_canvas_has_chart_items_after_init(self):
        """After frame creation, each pie_canvas has at least one drawn item."""
        frame = self._make_frame()
        for index, card in enumerate(frame.cards):
            with self.subTest(card=index):
                item_count = len(card.pie_canvas.find_all())
                self.assertGreater(
                    item_count,
                    0,
                    f"Card {index} pie_canvas has no drawn items after init",
                )


if __name__ == "__main__":
    unittest.main()
