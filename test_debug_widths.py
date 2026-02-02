"""Debug script to check actual header vs data widths"""

import tkinter as tk
from tkinter import ttk
from time_tracker import TimeTracker
from src.analysis_frame import AnalysisFrame
import json

# Create test data
date = "2026-01-29"
test_data = {
    f"{date}_session1": {
        "sphere": "Work",
        "date": date,
        "start_timestamp": 1234567890,
        "end_timestamp": 1234570890,
        "total_duration": 3000,
        "active_duration": 3000,
        "active": [
            {
                "duration": 3000,
                "project": "Project A",
                "comment": "Working",
                "start": "10:30:00",
                "start_timestamp": 1234567890,
            }
        ],
        "breaks": [],
        "idle_periods": [],
        "session_comments": {
            "active_notes": "active comment",
            "break_notes": "",
            "idle_notes": "",
            "session_notes": "session note",
        },
    }
}

# Write test data
with open("test_debug_data.json", "w") as f:
    json.dump(test_data, f)

# Create minimal settings
settings = {
    "idle_settings": {"idle_tracking_enabled": False},
    "spheres": {"Work": {"is_default": True, "active": True}},
    "projects": {"Project A": {"sphere": "Work", "is_default": True, "active": True}},
    "break_actions": {"Resting": {"is_default": True, "active": True}},
}

with open("test_debug_settings.json", "w") as f:
    json.dump(settings, f)

# Create UI
root = tk.Tk()
tracker = TimeTracker(root)
tracker.data_file = "test_debug_data.json"
tracker.settings_file = "test_debug_settings.json"
tracker.settings = tracker.get_settings()

parent_frame = ttk.Frame(root)
frame = AnalysisFrame(parent_frame, tracker, root)

# Update display
frame.update_timeline()
root.update_idletasks()

# Get headers
header_labels = [
    w for w in frame.timeline_header_frame.winfo_children() if isinstance(w, tk.Label)
]

# Get first data row
data_rows = [
    w for w in frame.timeline_frame.winfo_children() if isinstance(w, tk.Frame)
]
first_row = data_rows[0]
data_labels = [w for w in first_row.winfo_children() if isinstance(w, tk.Label)]

print(f"\n{'='*80}")
print("HEADER vs DATA WIDTH COMPARISON")
print(f"{'='*80}\n")
print(
    f"{'Col':<4} {'Header Text':<25} {'H-Cfg':>6} {'H-Px':>6} {'D-Cfg':>6} {'D-Px':>6} {'Match?':<8}"
)
print(f"{'-'*80}")

for idx, (header, data) in enumerate(zip(header_labels, data_labels)):
    h_text = header.cget("text")
    h_cfg_width = header.cget("width")
    h_px_width = header.winfo_reqwidth()
    d_cfg_width = data.cget("width")
    d_px_width = data.winfo_reqwidth()
    match = "✓" if h_px_width == d_px_width else "✗ FAIL"

    print(
        f"{idx:<4} {h_text:<25} {h_cfg_width:>6} {h_px_width:>6} {d_cfg_width:>6} {d_px_width:>6} {match:<8}"
    )

print(f"\n{'='*80}\n")

root.destroy()

# Cleanup
import os

os.remove("test_debug_data.json")
os.remove("test_debug_settings.json")
