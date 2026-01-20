"""
Quick script to check screenshot directory and show what's being captured
"""

import os
import json

print("=" * 60)
print("SCREENSHOT DIRECTORY CHECK")
print("=" * 60)

# Check if screenshots directory exists
screenshot_dir = "screenshots"
if os.path.exists(screenshot_dir):
    print(f"\n✓ Screenshot directory exists: {os.path.abspath(screenshot_dir)}")

    # List contents
    for root, dirs, files in os.walk(screenshot_dir):
        level = root.replace(screenshot_dir, "").count(os.sep)
        indent = " " * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = " " * 2 * (level + 1)
        for file in files:
            print(f"{sub_indent}{file}")
else:
    print(f"\n✗ Screenshot directory does NOT exist yet")
    print(f"   Will be created at: {os.path.abspath(screenshot_dir)}")

# Check data.json for screenshot info
print("\n" + "=" * 60)
print("SCREENSHOT DATA IN data.json")
print("=" * 60)

if os.path.exists("data.json"):
    with open("data.json", "r") as f:
        data = json.load(f)

    sessions_with_screenshots = 0
    total_screenshots = 0

    for session_name, session_data in data.items():
        has_screenshots = False
        session_screenshot_count = 0

        # Check active periods
        for period in session_data.get("active", []):
            if "screenshot_folder" in period:
                has_screenshots = True
                session_screenshot_count += len(period.get("screenshots", []))

        # Check break periods
        for period in session_data.get("breaks", []):
            if "screenshot_folder" in period:
                has_screenshots = True
                session_screenshot_count += len(period.get("screenshots", []))

        if has_screenshots:
            sessions_with_screenshots += 1
            total_screenshots += session_screenshot_count
            print(f"\n{session_name}: {session_screenshot_count} screenshots")

            # Show folder paths
            for period in session_data.get("active", []):
                if "screenshot_folder" in period:
                    print(f"  Active: {period['screenshot_folder']}")
            for period in session_data.get("breaks", []):
                if "screenshot_folder" in period:
                    print(f"  Break: {period['screenshot_folder']}")

    if sessions_with_screenshots == 0:
        print("\nNo sessions with screenshot data found in data.json")
    else:
        print(
            f"\nTotal: {sessions_with_screenshots} sessions, {total_screenshots} screenshots"
        )
else:
    print("\ndata.json not found")

print("\n" + "=" * 60)
print("SETTINGS")
print("=" * 60)

if os.path.exists("settings.json"):
    with open("settings.json", "r") as f:
        settings = json.load(f)

    ss_settings = settings.get("screenshot_settings", {})
    print(f"\nEnabled: {ss_settings.get('enabled', False)}")
    print(
        f"Capture on focus change: {ss_settings.get('capture_on_focus_change', True)}"
    )
    print(
        f"Min seconds between captures: {ss_settings.get('min_seconds_between_captures', 10)}"
    )
    print(f"Screenshot path: {ss_settings.get('screenshot_path', 'screenshots')}")
else:
    print("\nsettings.json not found")

print("\n" + "=" * 60)
