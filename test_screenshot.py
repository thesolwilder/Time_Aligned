"""
Quick test script to verify screenshot capture functionality
"""

import time
from screenshot_capture import ScreenshotCapture
import json

# Load settings
with open("settings.json", "r") as f:
    settings = json.load(f)

# Create screenshot capture instance
capture = ScreenshotCapture(settings, "data.json")

# Test session info
test_session_key = "2026-01-20_1234567890"

print("Testing screenshot capture functionality...")
print(f"Screenshot enabled: {capture.enabled}")
print(f"Capture on focus change: {capture.capture_on_focus_change}")
print(f"Min seconds between captures: {capture.min_seconds_between_captures}")
print()

# Set up a test session
print(f"Setting up test session: {test_session_key}")
capture.set_current_session(test_session_key, "active", 0)
print(f"Screenshot folder: {capture.get_screenshot_folder_path()}")
print()

# Start monitoring
print("Starting screenshot monitoring...")
print("Monitoring will run for 30 seconds. Switch between windows to test!")
capture.start_monitoring()

# Monitor for 30 seconds
for i in range(30):
    time.sleep(1)
    screenshots = capture.get_current_period_screenshots()
    if len(screenshots) > 0:
        print(f"  Captured {len(screenshots)} screenshot(s)")
        for ss in screenshots:
            print(f"    - {ss['process_name']}: {ss['window_title'][:50]}")

print()
print("Stopping monitoring...")
capture.stop_monitoring()

# Show final results
final_screenshots = capture.get_current_period_screenshots()
print(f"\nTotal screenshots captured: {len(final_screenshots)}")
if len(final_screenshots) > 0:
    print("\nScreenshot details:")
    for i, ss in enumerate(final_screenshots, 1):
        print(f"{i}. {ss['timestamp']} - {ss['process_name']}")
        print(f"   Window: {ss['window_title']}")
        print(f"   Path: {ss['relative_path']}")
        print()

print("Test complete!")
