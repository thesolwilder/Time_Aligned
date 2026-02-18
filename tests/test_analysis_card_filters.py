"""
Tests for Analysis Frame Card Date Filters

Tests the date filtering functionality for analysis cards:
- Today filter
- Yesterday filter
- Custom date filter

Following TDD workflow: Import → Unit → Integration → E2E
"""

import unittest
import sys
import os
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestAnalysisCardFiltersImport(unittest.TestCase):
    """Import tests for card filter functionality"""

    def test_import_analysis_frame(self):
        """Verify AnalysisFrame can be imported"""
        from src.analysis_frame import AnalysisFrame

        assert AnalysisFrame is not None

    def test_import_test_helpers(self):
        """Verify test helpers can be imported"""
        from tests.test_helpers import TestDataGenerator, MockTime

        assert TestDataGenerator is not None
        assert MockTime is not None


class TestCardDateFilterFunctions(unittest.TestCase):
    """Unit tests for date filter helper functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.addCleanup(self.root.destroy)

        from tests.test_helpers import MockTime, TestFileManager

        self.mock_time = MockTime()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)

    def test_get_today_date_range(self):
        """Test that get_today_date_range returns correct date range"""
        from src.analysis_frame import AnalysisFrame

        # Mock current date as 2026-01-28
        with patch("src.analysis_frame.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 1, 28, 14, 30, 0)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(
                *args, **kwargs
            )

            # Create mock tracker with proper settings
            mock_tracker = Mock()
            mock_tracker.settings = {
                "analysis_settings": {
                    "card_ranges": ["Last 7 Days", "Last 30 Days", "All Time"]
                }
            }
            mock_tracker.settings_file = "test_settings.json"
            mock_tracker.data = {}
            mock_tracker.load_data = Mock(return_value={})

            # Create frame with real Tk parent
            parent_frame = ttk.Frame(self.root)
            frame = AnalysisFrame(parent_frame, mock_tracker, self.root)

            # Test method exists and returns today's date
            start_date, end_date = frame.get_date_range_for_filter("Today")

            self.assertEqual(start_date.date(), datetime(2026, 1, 28).date())
            # End date is exclusive, so it's the next day
            self.assertEqual(end_date.date(), datetime(2026, 1, 29).date())

    def test_get_yesterday_date_range(self):
        """Test that get_yesterday_date_range returns correct date range"""
        from src.analysis_frame import AnalysisFrame

        # Mock current date as 2026-01-28
        with patch("src.analysis_frame.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 1, 28, 14, 30, 0)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(
                *args, **kwargs
            )

            # Create mock tracker with proper settings
            mock_tracker = Mock()
            mock_tracker.settings = {
                "analysis_settings": {
                    "card_ranges": ["Last 7 Days", "Last 30 Days", "All Time"]
                }
            }
            mock_tracker.settings_file = "test_settings.json"
            mock_tracker.data = {}
            mock_tracker.load_data = Mock(return_value={})

            # Create frame with real Tk parent
            parent_frame = ttk.Frame(self.root)
            frame = AnalysisFrame(parent_frame, mock_tracker, self.root)

            # Test method returns yesterday's date
            start_date, end_date = frame.get_date_range_for_filter("Yesterday")

            self.assertEqual(start_date.date(), datetime(2026, 1, 27).date())
            # End date is exclusive, so it's the next day (today)
            self.assertEqual(end_date.date(), datetime(2026, 1, 28).date())

    def test_get_custom_date_range(self):
        """Test that get_custom_date_range returns correct date range"""
        from src.analysis_frame import AnalysisFrame

        # Create mock tracker with proper settings
        mock_tracker = Mock()
        mock_tracker.settings = {
            "analysis_settings": {
                "card_ranges": ["Last 7 Days", "Last 30 Days", "All Time"]
            }
        }
        mock_tracker.settings_file = "test_settings.json"
        mock_tracker.data = {}
        mock_tracker.load_data = Mock(return_value={})

        # Create frame with real Tk parent
        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, mock_tracker, self.root)

        # Test custom date parsing
        start_date, end_date = frame.get_date_range_for_filter("Custom: 2026-01-25")

        self.assertEqual(start_date.date(), datetime(2026, 1, 25).date())
        # End date is exclusive, so it's the next day
        self.assertEqual(end_date.date(), datetime(2026, 1, 26).date())


class TestCardFilterUI(unittest.TestCase):
    """Integration tests for card filter UI components"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.addCleanup(self.root.destroy)

        from tests.test_helpers import MockTime, TestFileManager

        self.mock_time = MockTime()
        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)

    def test_card_has_today_filter_option(self):
        """Test that card dropdown includes Today option"""
        from src.analysis_frame import AnalysisFrame

        # Create mock tracker with proper settings
        mock_tracker = Mock()
        mock_tracker.settings = {
            "analysis_settings": {
                "card_ranges": ["Last 7 Days", "Last 30 Days", "All Time"]
            }
        }
        mock_tracker.settings_file = "test_settings.json"
        mock_tracker.data = {}
        mock_tracker.load_data = Mock(return_value={})

        # Create frame with real Tk parent
        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, mock_tracker, self.root)

        # Verify Today is in date_ranges
        self.assertIn("Today", frame.date_ranges)

    def test_card_has_yesterday_filter_option(self):
        """Test that card dropdown includes Yesterday option"""
        from src.analysis_frame import AnalysisFrame

        # Create mock tracker with proper settings
        mock_tracker = Mock()
        mock_tracker.settings = {
            "analysis_settings": {
                "card_ranges": ["Last 7 Days", "Last 30 Days", "All Time"]
            }
        }
        mock_tracker.settings_file = "test_settings.json"
        mock_tracker.data = {}
        mock_tracker.load_data = Mock(return_value={})

        # Create frame with real Tk parent
        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, mock_tracker, self.root)

        # Verify Yesterday is in date_ranges
        self.assertIn("Yesterday", frame.date_ranges)

    def test_card_has_custom_date_filter_option(self):
        """Test that card supports custom date selection"""
        from src.analysis_frame import AnalysisFrame

        # Create mock tracker with proper settings
        mock_tracker = Mock()
        mock_tracker.settings = {
            "analysis_settings": {
                "card_ranges": ["Last 7 Days", "Last 30 Days", "All Time"]
            }
        }
        mock_tracker.settings_file = "test_settings.json"
        mock_tracker.data = {}
        mock_tracker.load_data = Mock(return_value={})

        # Create frame with real Tk parent
        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, mock_tracker, self.root)

        # Verify Custom Date is in date_ranges or frame has custom date selector
        has_custom = "Custom Date" in frame.date_ranges or hasattr(
            frame, "open_custom_date_dialog"
        )
        self.assertTrue(has_custom, "Frame should support custom date selection")


class TestCardFilterIntegration(unittest.TestCase):
    """Integration tests for complete filter workflow"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.addCleanup(self.root.destroy)

        from tests.test_helpers import TestFileManager

        self.file_manager = TestFileManager()
        self.addCleanup(self.file_manager.cleanup)

    def test_selecting_today_updates_card_data(self):
        """Test that selecting Today filter updates card with today's data"""
        from src.analysis_frame import AnalysisFrame
        from tests.test_helpers import TestDataGenerator

        # Create mock tracker with test data
        mock_tracker = Mock()
        today = datetime.now().strftime("%Y-%m-%d")
        test_data = TestDataGenerator.create_session_data(date=today)
        mock_tracker.data = test_data
        mock_tracker.settings = {
            "analysis_settings": {
                "card_ranges": ["Last 7 Days", "Last 30 Days", "All Time"]
            }
        }
        mock_tracker.settings_file = "test_settings.json"
        mock_tracker.load_data = Mock(return_value=test_data)

        # Create frame with real Tk parent
        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, mock_tracker, self.root)

        # Mock the card update method
        frame.update_card = Mock()

        # Simulate selecting "Today" filter
        frame.on_range_changed(0, "Today")

        # Verify update_card was called with correct index
        frame.update_card.assert_called_once_with(0)

    def test_selecting_yesterday_updates_card_data(self):
        """Test that selecting Yesterday filter updates card with yesterday's data"""
        from src.analysis_frame import AnalysisFrame
        from tests.test_helpers import TestDataGenerator

        # Create mock tracker with test data
        mock_tracker = Mock()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        test_data = TestDataGenerator.create_session_data(date=yesterday)
        mock_tracker.data = test_data
        mock_tracker.settings = {
            "analysis_settings": {
                "card_ranges": ["Last 7 Days", "Last 30 Days", "All Time"]
            }
        }
        mock_tracker.settings_file = "test_settings.json"
        mock_tracker.load_data = Mock(return_value=test_data)

        # Create frame with real Tk parent
        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, mock_tracker, self.root)

        # Mock the card update method
        frame.update_card = Mock()

        # Simulate selecting "Yesterday" filter
        frame.on_range_changed(0, "Yesterday")

        # Verify update_card was called
        frame.update_card.assert_called_once_with(0)

    def test_today_filter_shows_timeline_data(self):
        """Test that Today filter displays sessions in timeline"""
        from src.analysis_frame import AnalysisFrame
        from tests.test_helpers import TestDataGenerator

        # Create mock tracker with today's session data
        mock_tracker = Mock()
        today = datetime.now().strftime("%Y-%m-%d")

        # Create realistic session data for today
        test_data = {
            f"{today}_session1": {
                "sphere": "Work",
                "date": today,
                "start_time": "09:00:00",
                "active": [
                    {
                        "start": "09:00:00",
                        "duration": 3600,  # 1 hour
                        "project": "Project A",
                        "comment": "Morning work",
                    }
                ],
                "breaks": [
                    {
                        "start": "10:00:00",
                        "duration": 600,  # 10 minutes
                        "action": "coffee",
                    }
                ],
                "idle_periods": [],
            }
        }

        mock_tracker.data = test_data
        mock_tracker.settings = {
            "analysis_settings": {"card_ranges": ["Today", "Last 7 Days", "All Time"]}
        }
        mock_tracker.settings_file = "test_settings.json"
        mock_tracker.load_data = Mock(return_value=test_data)

        # Create frame with real Tk parent
        parent_frame = ttk.Frame(self.root)
        frame = AnalysisFrame(parent_frame, mock_tracker, self.root)

        # Set card 0 to "Today" filter
        frame.card_ranges[0] = "Today"
        frame.selected_card = 0

        # Initialize sphere and project filters to "All"
        frame.sphere_var.set("All Spheres")
        frame.project_var.set("All Projects")

        # Update the timeline (this should populate timeline_frame with data)
        frame.update_timeline()

        # Verify timeline has content (should have at least 2 rows: 1 active + 1 break)
        timeline_children = frame.timeline_frame.winfo_children()
        self.assertGreater(
            len(timeline_children),
            0,
            "Timeline should display sessions when Today filter is active",
        )

        # Verify we have at least 2 entries (1 active + 1 break)
        self.assertGreaterEqual(
            len(timeline_children),
            2,
            "Timeline should show at least 2 periods (active + break) for today's session",
        )


if __name__ == "__main__":
    unittest.main()
