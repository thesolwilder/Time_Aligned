"""
Debug script to reproduce and log the freeze bug.

Reproduces the exact sequence:
1. Open Analysis
2. Export CSV (large dataset)
3. Navigate to Completion Frame
4. Back to Analysis Frame
5. Click "Show Timeline" for All Spheres / All Time
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

print("=" * 80)
print("DEBUG FREEZE BUG - STARTING")
print("=" * 80)
print(
    "\nThis script will help you reproduce and debug the SCROLL & WIDGET BREAKING bug."
)
print("Please follow these steps EXACTLY:")
print()
print("1. The application will launch")
print("2. Click 'Analysis' button to open analysis frame")
print("3. Select 'All Spheres' and 'All Time' card")
print("4. Click 'Export CSV' button")
print("5. Save the CSV file anywhere")
print("6. Click 'Latest Session' button (to open completion frame)")
print("7. Click 'Back' button (to return to analysis frame)")
print("8. Click on the 'All Time' card (or any card)")
print("9. Try to SCROLL the timeline (mouse wheel or scrollbar)")
print("10. Click on DIFFERENT cards (Yesterday, Last 30 Days, etc.)")
print()
print("WATCH THE CONSOLE OUTPUT - it will show you:")
print("  - Instance IDs for each AnalysisFrame created")
print("  - Instance IDs for timeline_frame and scrollable canvas")
print("  - ScrollableFrame state (exists, bindings, scrollregion)")
print("  - Canvas bindings (should include MouseWheel)")
print("  - Canvas scrollregion and bbox (content area)")
print("  - Data sizes during CSV export")
print("  - Data sizes during timeline update")
print("  - Any errors or missing widgets")
print()
print("REPORT BACK:")
print("  - Can you scroll after step 8? (Yes/No)")
print("  - Do widgets break when clicking different cards? (Yes/No)")
print("  - What error messages appear in the console?")
print()
print("If the app freezes, press Ctrl+C in this console to see where it got stuck.")
print()
input("Press ENTER to start the application...")
print()

# Import after the instructions so user sees them first
from time_tracker import TimeTracker
import tkinter as tk

# Create and run the app
root = tk.Tk()
app = TimeTracker(root)

print("\n" + "=" * 80)
print("APPLICATION STARTED - Follow the steps above")
print("=" * 80 + "\n")

try:
    root.mainloop()
except KeyboardInterrupt:
    print("\n" + "=" * 80)
    print("INTERRUPTED BY USER (Ctrl+C)")
    print("=" * 80)
    import traceback

    traceback.print_stack()
except Exception as e:
    print("\n" + "=" * 80)
    print(f"ERROR: {e}")
    print("=" * 80)
    import traceback

    traceback.print_exc()
finally:
    print("\n" + "=" * 80)
    print("DEBUG FREEZE BUG - ENDED")
    print("=" * 80)
