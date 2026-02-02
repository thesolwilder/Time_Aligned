"""Visual test for two-row header implementation

Run this script to see the new two-row headers in action.

The timeline should now show:
- Column 5: "Sphere" (top) / "Active" (bottom)
- Column 6: "Project" (top) / "Active" (bottom)

All other headers are single-row but vertically centered to align.
"""

import tkinter as tk
from tkinter import ttk
from time_tracker import TimeTracker
from src.analysis_frame import AnalysisFrame
import json
from datetime import datetime

# Create test data with multiple sessions
test_data = {}
for i in range(5):
    date = f"2026-02-{str(i+1).zfill(2)}"
    test_data[f"{date}_session{i+1}"] = {
        "sphere": ["Work", "Personal", "Learning", "Health", "Creative"][i],
        "date": date,
        "start_timestamp": 1234567890 + (i * 10000),
        "end_timestamp": 1234570890 + (i * 10000),
        "total_duration": 3000,
        "active_duration": 3000,
        "active": [
            {
                "duration": 3000,
                "project": ["Project A", "Project B", "Study", "Exercise", "Art"][i],
                "comment": f"Working on task {i+1}",
                "start": f"{10+i}:30:00",
                "start_timestamp": 1234567890 + (i * 10000),
            }
        ],
        "breaks": [],
        "idle_periods": [],
        "session_comments": {
            "active_notes": f"Active note {i+1}",
            "break_notes": "",
            "idle_notes": "",
            "session_notes": f"Session note {i+1}",
        },
    }

# Write test data
with open("test_two_row_data.json", "w") as f:
    json.dump(test_data, f)

# Create minimal settings
settings = {
    "idle_settings": {"idle_tracking_enabled": False},
    "spheres": {
        "Work": {"is_default": True, "active": True},
        "Personal": {"is_default": False, "active": True},
        "Learning": {"is_default": False, "active": True},
        "Health": {"is_default": False, "active": True},
        "Creative": {"is_default": False, "active": True},
    },
    "projects": {
        "Project A": {"sphere": "Work", "is_default": True, "active": True},
        "Project B": {"sphere": "Personal", "is_default": False, "active": True},
        "Study": {"sphere": "Learning", "is_default": False, "active": True},
        "Exercise": {"sphere": "Health", "is_default": False, "active": True},
        "Art": {"sphere": "Creative", "is_default": False, "active": True},
    },
    "break_actions": {"Resting": {"is_default": True, "active": True}},
}

with open("test_two_row_settings.json", "w") as f:
    json.dump(settings, f)

# Create UI
root = tk.Tk()
root.title("Two-Row Headers Test")
root.geometry("1400x600")

tracker = TimeTracker(root)
tracker.data_file = "test_two_row_data.json"
tracker.settings_file = "test_two_row_settings.json"
tracker.settings = tracker.get_settings()

# Create analysis frame
parent_frame = ttk.Frame(root)
parent_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

frame = AnalysisFrame(parent_frame, tracker, root)
frame.pack(fill=tk.BOTH, expand=True)

# Update display
frame.update_timeline()

# Add instructions
instructions = tk.Label(
    root,
    text="✨ NEW TWO-ROW HEADERS ✨\n"
    "Look at columns 5 & 6: 'Sphere/Active' and 'Project/Active'\n"
    "These now clearly show what the checkmarks mean!\n"
    "Try clicking column headers to sort.",
    bg="#e8f5e9",
    font=("Arial", 10, "bold"),
    pady=10,
)
instructions.pack(side=tk.BOTTOM, fill=tk.X)

print("\n" + "=" * 80)
print("TWO-ROW HEADERS VISUAL TEST")
print("=" * 80)
print("\nInspect the timeline header:")
print("- Column 5 should show: 'Sphere' (top row) / 'Active' (bottom row)")
print("- Column 6 should show: 'Project' (top row) / 'Active' (bottom row)")
print("- All other columns should be single-row but vertically centered")
print("\nClick column headers to test sorting functionality.")
print("Close the window when done.\n")

root.mainloop()

# Cleanup
import os

os.remove("test_two_row_data.json")
os.remove("test_two_row_settings.json")
