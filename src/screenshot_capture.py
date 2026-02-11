"""
Screenshot Capture Module for Time Tracker
Captures screenshots when window focus changes and organizes them by date/session/period.
"""

import os
import time
import threading
from datetime import datetime
from PIL import ImageGrab, ImageDraw, ImageFont
import win32gui
import win32process
import psutil

from src.constants import DEFAULT_SCREENSHOT_FOLDER


class ScreenshotCapture:
    """Handles screenshot capture on window focus changes"""

    def __init__(self, settings, data_file_path):
        self.settings = settings
        self.data_file_path = data_file_path

        # Screenshot settings
        self.enabled = self.settings.get("screenshot_settings", {}).get(
            "enabled", False
        )
        self.capture_on_focus_change = self.settings.get("screenshot_settings", {}).get(
            "capture_on_focus_change", True
        )
        self.min_seconds_between_captures = self.settings.get(
            "screenshot_settings", {}
        ).get("min_seconds_between_captures", 10)
        self.screenshot_base_path = self.settings.get("screenshot_settings", {}).get(
            "screenshot_path", DEFAULT_SCREENSHOT_FOLDER
        )

        # State tracking
        self.monitoring = False
        self.monitor_thread = None
        self.last_window_title = None
        self.last_window_process = None
        self.last_capture_time = 0

        # Current session/period info
        self.current_session_key = None
        self.current_period_type = None  # "active", "break", or "idle"
        self.current_period_index = None
        self.current_screenshot_folder = None
        self.current_period_screenshots = (
            []
        )  # List of screenshot info for current period

    def start_monitoring(self):
        """Start monitoring window focus changes"""
        if not self.enabled:
            return

        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop monitoring window focus changes"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)

    def set_current_session(self, session_key, period_type="active", period_index=0):
        """Set the current session and period for organizing screenshots"""
        self.current_session_key = session_key
        self.current_period_type = period_type
        self.current_period_index = period_index
        self.current_period_screenshots = []  # Reset screenshot list for new period

        # Create folder structure: screenshots/YYYY-MM-DD/session_<timestamp>/period_<type>_<index>/
        if session_key:
            date_str = session_key.split("_")[0]  # Extract date from session key
            session_timestamp = session_key.split("_")[1]

            self.current_screenshot_folder = os.path.join(
                self.screenshot_base_path,
                date_str,
                f"session_{session_timestamp}",
                f"period_{period_type}_{period_index}",
            )

            # Create folder if it doesn't exist
            os.makedirs(self.current_screenshot_folder, exist_ok=True)
        else:
            self.current_screenshot_folder = None

    def _get_active_window_info(self):
        """Get information about the currently active window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)

            # Get process info
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                process = psutil.Process(pid)
                process_name = process.name()
            except:
                process_name = "Unknown"

            return window_title, process_name
        except Exception as error:
            return None, None

    def _should_capture(self, window_title, process_name):
        """Determine if a screenshot should be captured"""
        if not self.enabled or not self.current_screenshot_folder:
            return False

        # Check minimum time between captures
        current_time = time.time()
        if current_time - self.last_capture_time < self.min_seconds_between_captures:
            return False

        # Check if window has changed
        if self.capture_on_focus_change:
            if (
                window_title != self.last_window_title
                or process_name != self.last_window_process
            ):
                return True
        else:
            # Capture on timer (handled by min_seconds_between_captures)
            return True

        return False

    def capture_screenshot(self):
        """Capture a screenshot and save it to the current period folder"""
        if not self.current_screenshot_folder:
            return None

        try:
            # Get window info
            window_title, process_name = self._get_active_window_info()

            if not window_title:
                return None

            # Capture screenshot
            screenshot = ImageGrab.grab()

            # Add timestamp overlay to bottom left
            draw = ImageDraw.Draw(screenshot)
            timestamp_display = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")

            # Try to use a nice font, fallback to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()

            # Calculate text size for background rectangle
            bbox = draw.textbbox((0, 0), timestamp_display, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Get image dimensions for bottom left positioning
            img_width, img_height = screenshot.size

            # Draw semi-transparent background rectangle at bottom left
            padding = 8
            y_position = img_height - text_height - padding * 2
            draw.rectangle(
                [(0, y_position), (text_width + padding * 2, img_height)],
                fill=(0, 0, 0, 100),
            )

            # Draw timestamp text in white at bottom left
            draw.text(
                (padding, y_position + padding),
                timestamp_display,
                fill=(255, 255, 255),
                font=font,
            )

            # Generate filename with timestamp and window info
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Sanitize window title for filename
            safe_title = "".join(
                c if c.isalnum() or c in (" ", "-", "_") else "_" for c in window_title
            )
            safe_title = safe_title[:50]  # Limit length

            filename = f"{timestamp_str}_{process_name}_{safe_title}.png"
            filepath = os.path.join(self.current_screenshot_folder, filename)

            # Save screenshot
            screenshot.save(filepath, "PNG", optimize=True)

            # Update state
            self.last_capture_time = time.time()
            self.last_window_title = window_title
            self.last_window_process = process_name

            screenshot_info = {
                "filepath": filepath,
                "relative_path": os.path.relpath(
                    filepath, os.path.dirname(self.data_file_path)
                ),
                "timestamp": timestamp_str,
                "window_title": window_title,
                "process_name": process_name,
            }

            # Add to current period's screenshot list
            self.current_period_screenshots.append(screenshot_info)

            return screenshot_info

        except Exception as error:
            return None

    def _monitor_loop(self):
        """Main monitoring loop that checks for window focus changes"""
        while self.monitoring:
            try:
                window_title, process_name = self._get_active_window_info()

                if window_title and self._should_capture(window_title, process_name):
                    screenshot_info = self.capture_screenshot()
                    # Note: The main application will query get_screenshot_folder_path()
                    # to get the folder path for the data model

                # Check every 0.5 seconds
                time.sleep(0.5)

            except Exception as error:
                time.sleep(1)

    def get_screenshot_folder_path(self):
        """Get the current screenshot folder path for this session.

        Returns the full path to the folder where screenshots are being saved
        for the current active period. Path format: screenshots/YYYY-MM-DD/

        Called from:
        - Screenshot display operations
        - File browser integrations
        - Screenshot management utilities

        Returns:
            String path to current screenshot folder

        Note:
            Folder is created when new period starts via new_period().
            Returns None if no period has started yet.
        """
        return self.current_screenshot_folder

    def get_current_period_screenshots(self):
        """Get defensive copy of screenshots captured for current period.

        Returns list of screenshot file paths captured since the current period
        started. Returns a copy to prevent external code from modifying the
        internal list.

        Called from:
        - Screenshot display in completion frame
        - Session view screenshot gallery
        - Period screenshot review

        Returns:
            List of string file paths to screenshots (e.g., ["screenshots/2026-02-11/1625_screenshot.png"])
            Empty list if no screenshots captured yet

        Note:
            Returns defensive copy via .copy() to prevent external mutation.
            List is reset to empty when new_period() is called.
        """
        return (
            self.current_period_screenshots.copy()
        )  # Return a copy to avoid external modification

    def update_settings(self, new_settings):
        """Update screenshot capture settings from new settings dictionary.

        Reloads all screenshot-related settings from the provided settings dict.
        Updates internal state and restarts monitoring if capture settings changed.

        Called from:
        - Settings dialog save operation
        - Settings file reload

        Settings read (with defaults):
        - enabled: False - Master toggle for screenshot capture
        - capture_on_focus_change: True - Capture when switching windows
        - min_seconds_between_captures: 10 - Rate limiting
        - screenshot_path: "screenshots" - Base folder path

        Args:
            new_settings: Full settings dictionary from settings.json

        Side effects:
            - Updates all screenshot configuration attributes
            - Restarts window monitoring thread if needed
            - Does NOT affect screenshots already captured

        Note:
            Safe to call while session active. Monitoring thread auto-restarts.
        """
        self.settings = new_settings
        self.enabled = self.settings.get("screenshot_settings", {}).get(
            "enabled", False
        )
        self.capture_on_focus_change = self.settings.get("screenshot_settings", {}).get(
            "capture_on_focus_change", True
        )
        self.min_seconds_between_captures = self.settings.get(
            "screenshot_settings", {}
        ).get("min_seconds_between_captures", 10)
        self.screenshot_base_path = self.settings.get("screenshot_settings", {}).get(
            "screenshot_path", "screenshots"
        )

        # Restart monitoring if needed
        if self.enabled and not self.monitoring:
            self.start_monitoring()
        elif not self.enabled and self.monitoring:
            self.stop_monitoring()
