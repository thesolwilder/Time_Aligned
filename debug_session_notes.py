"""
Debug script to check session notes column placement.
"""

import tkinter as tk
from tkinter import ttk
from time_tracker import TimeTracker
from src.analysis_frame import AnalysisFrame

# Create root window
root = tk.Tk()
root.title("Session Notes Debug")

# Create tracker and analysis frame
tracker = TimeTracker(root)
tracker.settings = tracker.get_settings()

parent_frame = ttk.Frame(root)
parent_frame.grid(row=0, column=0, sticky="nsew")
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

frame = AnalysisFrame(parent_frame, tracker, root)

# Update timeline to show data
frame.update_timeline()
root.update_idletasks()

# Get first data row
timeline_rows = [
    w for w in frame.timeline_frame.winfo_children() if isinstance(w, tk.Frame)
]

if len(timeline_rows) > 0:
    print(f"\nFound {len(timeline_rows)} timeline rows")

    first_row = timeline_rows[0]
    row_labels = [w for w in first_row.winfo_children() if isinstance(w, tk.Label)]

    print(f"\nTotal columns: {len(row_labels)}")
    print("\nColumn contents:")
    for i, label in enumerate(row_labels):
        text = label.cget("text")
        if text:  # Only print non-empty columns
            print(f"  Column {i}: '{text}'")

    # Check specific columns
    if len(row_labels) > 13:
        print(f"\n=== Key Columns ===")
        print(f"Column 9 (Secondary Action): '{row_labels[9].cget('text')}'")
        print(f"Column 13 (Session Notes): '{row_labels[13].cget('text')}'")
else:
    print("No timeline rows found!")

# Keep window open for inspection
print("\nWindow opened - close to exit")
root.mainloop()
