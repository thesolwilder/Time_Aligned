"""
Debug test to reproduce the exact freeze scenario:
1. Export data
2. Navigate to completion frame
3. Back to analysis frame
4. Click show timeline for all spheres > all time
"""

import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime, timedelta
from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from time_tracker import TimeTracker


def create_test_data():
    """Create test data with ~150 sessions"""
    today = datetime.now()
    test_data = {}

    for i in range(150):
        session_date = (today - timedelta(days=i % 365)).strftime("%Y-%m-%d")
        session_key = f"{session_date}_session{i}"

        test_data[session_key] = {
            "sphere": "Work",
            "date": session_date,
            "start_timestamp": 1234567890 + (i * 1000),
            "end_timestamp": 1234567890 + (i * 1000) + 7200,
            "total_duration": 7200,
            "active_duration": 5400,
            "break_duration": 1800,
            "active": [
                {
                    "duration": 2700,
                    "project": "Active Project",
                    "start": "09:00:00",
                    "start_timestamp": 1234567890 + (i * 1000),
                    "end": "09:45:00",
                    "end_timestamp": 1234567890 + (i * 1000) + 2700,
                    "comment": f"Active period {i}-1",
                },
                {
                    "duration": 2700,
                    "project": "Active Project",
                    "start": "10:00:00",
                    "start_timestamp": 1234567890 + (i * 1000) + 3600,
                    "end": "10:45:00",
                    "end_timestamp": 1234567890 + (i * 1000) + 6300,
                    "comment": f"Active period {i}-2",
                },
            ],
            "breaks": [
                {
                    "duration": 900,
                    "action": "Resting",
                    "start": "11:00:00",
                    "start_timestamp": 1234567890 + (i * 1000) + 7200,
                    "comment": f"Break period {i}",
                }
            ],
            "idle_periods": [],
        }

    return test_data


def main():
    print("=" * 80)
    print("DEBUG TEST: Reproducing freeze scenario")
    print("=" * 80)

    # Create root window
    root = tk.Tk()
    root.title("Debug Test")

    # Create test files
    test_data_file = "test_debug_data.json"
    test_settings_file = "test_debug_settings.json"

    settings = {
        "idle_settings": {"idle_tracking_enabled": True, "idle_threshold": 60},
        "spheres": {"Work": {"is_default": True, "active": True}},
        "projects": {
            "Active Project": {
                "sphere": "Work",
                "is_default": True,
                "active": True,
            }
        },
        "break_actions": {"Resting": {"is_default": True, "active": True}},
    }

    # Create test data
    test_data = create_test_data()

    with open(test_data_file, "w") as f:
        json.dump(test_data, f)

    with open(test_settings_file, "w") as f:
        json.dump(settings, f)

    # Create TimeTracker instance
    tracker = TimeTracker(root)
    tracker.data_file = test_data_file
    tracker.settings_file = test_settings_file
    tracker.settings = tracker.get_settings()
    tracker.session_active = False

    print("\n[STEP 1] Opening analysis frame...")
    tracker.open_analysis()
    root.update()

    print("\n[STEP 2] Setting filters to 'All Spheres' and 'all' status...")
    tracker.analysis_frame.sphere_var.set("All Spheres")
    tracker.analysis_frame.status_filter.set("all")
    tracker.analysis_frame.refresh_all()
    root.update()

    print("\n[STEP 3] Exporting CSV...")
    csv_file = "test_debug_export.csv"
    with patch("tkinter.filedialog.asksaveasfilename", return_value=csv_file):
        with patch("tkinter.messagebox.showinfo"):
            tracker.analysis_frame.export_to_csv()
    root.update()

    print("\n[STEP 4] Navigating to completion frame (simulated)...")
    # Note: We can't easily navigate to completion without a session,
    # so we'll just close and reopen analysis
    tracker.close_analysis()
    root.update()

    print("\n[STEP 5] Reopening analysis frame...")
    tracker.open_analysis()
    root.update()

    print("\n[STEP 6] Setting to 'All Spheres' and 'All Time'...")
    tracker.analysis_frame.sphere_var.set("All Spheres")
    tracker.analysis_frame.status_filter.set("all")
    tracker.analysis_frame.card_ranges[0] = "All Time"
    root.update()

    print("\n[STEP 7] Clicking 'Show Timeline' for card 0 (All Time)...")
    print("-" * 80)

    import time

    start_time = time.time()

    try:
        tracker.analysis_frame.select_card(0)
        root.update()

        elapsed = time.time() - start_time
        print("-" * 80)
        print(f"\n✅ SUCCESS! Timeline updated in {elapsed:.3f}s")

        # Check if widgets were created
        widget_count = len(tracker.analysis_frame.timeline_frame.winfo_children())
        print(f"Timeline widgets created: {widget_count}")

    except Exception as e:
        elapsed = time.time() - start_time
        print("-" * 80)
        print(f"\n❌ FAILED after {elapsed:.3f}s")
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 80)
    print("Test completed. Close the window to exit.")
    print("=" * 80)

    # Clean up test files
    try:
        os.remove(test_data_file)
        os.remove(test_settings_file)
        if os.path.exists(csv_file):
            os.remove(csv_file)
    except:
        pass

    root.mainloop()


if __name__ == "__main__":
    main()
