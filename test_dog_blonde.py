"""Test to reproduce the '7 dog is blonde' truncation bug"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from time_tracker import TimeTracker
from analysis_frame import AnalysisFrame
from tests.test_helpers import TestFileManager


# Create test data matching screenshot
def test_seven_blonde_statements():
    """Test that all 7 'the dog is blonde' statements show without truncation"""
    root = tk.Tk()
    file_manager = TestFileManager()

    date = "2026-02-02"

    # This is the actual text from the screenshot/data.json
    seven_blonde_text = "1. the dog is blonde. 2. the dog is blonde. 3. the dog is blonde. 4. the dog is blonde. 5. the dog is blonde. 6. the dog is blonde. 7. the dog is blonde."

    test_data = {
        f"{date}_session1": {
            "sphere": "General",
            "date": date,
            "start_timestamp": 1738540140,
            "end_timestamp": 1738540145,
            "total_duration": 5,
            "active_duration": 5,
            "active": [
                {
                    "duration": 5,
                    "project": "General",
                    "comment": seven_blonde_text,
                    "start": "03:49 PM",
                    "start_timestamp": 1738540140,
                }
            ],
            "breaks": [],
            "idle_periods": [],
            "session_comments": {
                "active_notes": seven_blonde_text,
                "break_notes": "",
                "idle_notes": "",
                "session_notes": seven_blonde_text,
            },
        }
    }

    settings = {
        "idle_settings": {"idle_tracking_enabled": False},
        "spheres": {
            "General": {"is_default": True, "active": True},
        },
        "projects": {
            "General": {"sphere": "General", "is_default": True, "active": True},
        },
        "break_actions": {"Resting": {"is_default": True, "active": True}},
    }

    test_settings_file = file_manager.create_test_file(
        "test_dog_settings.json", settings
    )
    test_data_file = file_manager.create_test_file("test_dog_data.json", test_data)

    tracker = TimeTracker(root)
    tracker.data_file = test_data_file
    tracker.settings_file = test_settings_file
    tracker.settings = tracker.get_settings()

    parent_frame = ttk.Frame(root)
    frame = AnalysisFrame(parent_frame, tracker, root)
    frame.update_timeline()
    root.update_idletasks()

    # Get first row
    timeline_children = frame.timeline_frame.winfo_children()
    assert len(timeline_children) > 0, "Should have at least one row"

    row_frame = timeline_children[0]
    all_widgets = [child for child in row_frame.winfo_children()]

    # Check comment columns that should show all 7 statements
    # Primary Comment (8), Active Comments (11), Session Notes (13)
    comment_indices = {
        8: "Primary Comment",
        11: "Active Comments",
        13: "Session Notes",
    }

    print(f"\nFull text length: {len(seven_blonde_text)} chars")
    print(f"Expected all 7 occurrences: 7")

    for idx, col_name in comment_indices.items():
        if idx < len(all_widgets):
            widget = all_widgets[idx]

            # Should be Text widget
            assert isinstance(widget, tk.Text), f"{col_name} should be Text widget"

            # Get displayed text
            displayed_text = widget.get("1.0", "end-1c")

            # Count occurrences
            occurrences = displayed_text.count("the dog is blonde")

            # Get widget height
            height = widget.cget("height")
            width = widget.cget("width")

            print(f"\n{col_name} (index {idx}):")
            print(f"  Widget config: width={width} chars, height={height} lines")
            print(f"  Displayed text length: {len(displayed_text)} chars")
            print(f"  Full text matches: {displayed_text == seven_blonde_text}")
            print(f"  Number of 'the dog is blonde' occurrences: {occurrences}")

            # THE ACTUAL TEST: All 7 occurrences should be visible
            assert (
                occurrences == 7
            ), f"{col_name} only shows {occurrences}/7 'the dog is blonde' statements! Text is truncated."

            assert (
                displayed_text == seven_blonde_text
            ), f"{col_name} text doesn't match. Expected full text with all 7 statements."

            # Calculate minimum height needed for this text
            # The actual widget now uses tkinter's count("displaylines") which measures
            # the ACTUAL wrapped line count, not an estimation
            # For this specific text (153 chars, width=21), actual display is ~7 lines
            # The widget should have height >= 7 to show all content
            min_reasonable_height = (
                7  # Based on actual displaylines count for this text
            )

            print(
                f"  Minimum height needed: {min_reasonable_height} lines (actual wrapped line count)"
            )

            # VISUAL HEIGHT TEST: Widget must be tall enough to display all text
            assert height >= min_reasonable_height, (
                f"{col_name} widget height={height} lines is too small! "
                f"Text has 7 'the dog is blonde' statements which wrap to ~{min_reasonable_height} display lines "
                f"with width={width} chars. Need at least {min_reasonable_height} lines to display all content. "
                f"Text is stored but visually TRUNCATED (bottom lines cut off)!"
            )

    print(
        "\n✓ SUCCESS: All 7 'the dog is blonde' statements are visible in all columns!"
    )

    file_manager.cleanup()
    root.destroy()


if __name__ == "__main__":
    test_seven_blonde_statements()
