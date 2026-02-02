"""Visual inspection script to see actual column alignment"""

import tkinter as tk
from tkinter import ttk
from time_tracker import TimeTracker
from src.analysis_frame import AnalysisFrame
import json

# Create test data with multiple sessions
date = "2026-01-29"
test_data = {}
for i in range(5):
    test_data[f"{date}_session{i}"] = {
        "sphere": f"Sphere{i % 2}",
        "date": date,
        "start_timestamp": 1234567890 + (i * 1000),
        "end_timestamp": 1234570890 + (i * 1000),
        "total_duration": 3000,
        "active_duration": 3000,
        "active": [
            {
                "duration": 3000,
                "project": f"Project {chr(65 + i)}",
                "comment": f"Work comment {i}",
                "start": f"10:{30 + i}:00",
                "start_timestamp": 1234567890 + (i * 1000),
            }
        ],
        "breaks": [],
        "idle_periods": [],
        "session_comments": {
            "active_notes": f"active comment {i}",
            "break_notes": "",
            "idle_notes": "",
            "session_notes": f"session note {i}",
        },
    }

# Write test data
with open("visual_test_data.json", "w") as f:
    json.dump(test_data, f)

# Create minimal settings
settings = {
    "idle_settings": {"idle_tracking_enabled": False},
    "spheres": {
        "Sphere0": {"is_default": True, "active": True},
        "Sphere1": {"is_default": False, "active": True},
    },
    "projects": {
        f"Project {chr(65 + i)}": {
            "sphere": "Sphere0",
            "is_default": i == 0,
            "active": True,
        }
        for i in range(5)
    },
    "break_actions": {"Resting": {"is_default": True, "active": True}},
}

with open("visual_test_settings.json", "w") as f:
    json.dump(settings, f)

# Create UI
root = tk.Tk()
root.title("Column Alignment Visual Test")
root.geometry("1400x600")

tracker = TimeTracker(root)
tracker.data_file = "visual_test_data.json"
tracker.settings_file = "visual_test_settings.json"
tracker.settings = tracker.get_settings()

parent_frame = ttk.Frame(root)
parent_frame.pack(fill=tk.BOTH, expand=True)

frame = AnalysisFrame(parent_frame, tracker, root)
frame.pack(fill=tk.BOTH, expand=True)

# Update display
frame.update_timeline()

print("\n" + "=" * 80)
print("VISUAL INSPECTION TEST")
print("=" * 80)
print("\nLook at the window and verify:")
print("1. Header column edges align with data column edges")
print("2. Text in each column starts at the same horizontal position")
print("3. Column separations are visually consistent")
print("4. Try clicking headers to sort - alignment should remain")
print("\n" + "=" * 80)
print("\nClose the window when done inspecting...")

root.mainloop()

# Cleanup
import os

os.remove("visual_test_data.json")
os.remove("visual_test_settings.json")
