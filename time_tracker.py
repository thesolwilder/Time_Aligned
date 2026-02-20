import tkinter as tk
from tkinter import ttk, messagebox
import time
import os
import json
from datetime import datetime
import sys
import threading
from PIL import Image, ImageDraw
import pystray
from pynput import mouse, keyboard

from src.ui_helpers import ScrollableFrame, get_frame_background
from src.completion_frame import CompletionFrame
from src.settings_frame import SettingsFrame
from src.analysis_frame import AnalysisFrame
from src.screenshot_capture import ScreenshotCapture
from src.constants import (
    UPDATE_TIMER_INTERVAL_MS,
    ONE_MINUTE_MS,
    DEFAULT_IDLE_THRESHOLD_SECONDS,
    DEFAULT_IDLE_BREAK_THRESHOLD_SECONDS,
    SECONDS_PER_HOUR,
    SECONDS_PER_MINUTE,
    DEFAULT_SETTINGS_FILE,
    DEFAULT_DATA_FILE,
    DEFAULT_SCREENSHOT_FOLDER,
    COLOR_LINK_BLUE,
    COLOR_GRAY_TEXT,
    COLOR_ACTIVE_GREEN,
    get_resource_path,
    COLOR_BREAK_ORANGE,
    COLOR_TRAY_IDLE,
    COLOR_TRAY_ACTIVE,
    COLOR_TRAY_BREAK,
    COLOR_TRAY_SESSION_IDLE,
    TRAY_ICON_SIZE,
    TRAY_ICON_MARGIN,
    TRAY_ICON_OUTLINE_WIDTH,
    FONT_LINK,
    FONT_SMALL,
    FONT_NORMAL,
    FONT_HEADING,
    FONT_TIMER_LARGE,
    FONT_TIMER_MEDIUM,
    FONT_TIMER_SMALL,
)


class TimeTracker:
    def __init__(self, root):
        # Initialize main window
        self.root = root
        self.root.title("Time Aligned - Time Tracker")
        self.root.geometry("600x400")

        # Set window and taskbar icon (works in dev and PyInstaller bundle)
        icon_path = get_resource_path("assets/icon.ico")
        if os.path.isfile(icon_path):
            self.root.iconbitmap(icon_path)

        # Set theme
        style = ttk.Style()
        style.theme_use("clam")

        # Session state variables
        self.session_name = None
        self.session_active = False
        self.session_start_time = None
        self.session_elapsed = 0
        self.active_period_start_time = None  # Track start of current active period

        self.break_active = False
        self.break_start_time = None
        self.break_elapsed = 0
        self.total_break_time = 0  # Track cumulative break time
        self.auto_break_start_time_from_idle = None

        self.session_idle = False
        self.idle_start_time = None
        self.last_user_input = time.time()

        self.backup_loop_count = 0  # auto back up save end time if crash
        self.update_timer_interval = UPDATE_TIMER_INTERVAL_MS
        self.one_minute_ms = ONE_MINUTE_MS
        self.backup_frequency = (
            self.one_minute_ms // self.update_timer_interval
        )  # save every minute

        # File paths
        self.settings_file = DEFAULT_SETTINGS_FILE
        self.data_file = DEFAULT_DATA_FILE

        # Load settings
        self.settings = self.get_settings()

        # Input monitoring
        self.input_listener_running = False
        self.mouse_listener = None
        self.keyboard_listener = None
        self.input_monitoring_error_shown = (
            False  # Track if error notification already displayed
        )

        # Screenshot capture
        self.screenshot_capture = ScreenshotCapture(self.settings, self.data_file)

        # Frame references
        self.completion_frame = None
        self.settings_frame = None

        # System tray icon
        self.tray_icon = None
        self.tray_thread = None
        self.window_visible = True

        # Global hotkeys
        self.hotkey_listener = None

        # Create GUI
        self.create_widgets()

        # Setup system tray
        self.setup_tray_icon()

        # Setup global hotkeys
        self.setup_global_hotkeys()

        # Start update loop
        self.update_timers()

    def get_settings(self):
        """Load or create settings file"""
        default_settings = {
            "idle_settings": {
                "idle_tracking_enabled": True,  # enable/disable idle tracking
                "idle_threshold": DEFAULT_IDLE_THRESHOLD_SECONDS,
                "idle_break_threshold": DEFAULT_IDLE_BREAK_THRESHOLD_SECONDS,
            },
            "screenshot_settings": {
                "enabled": False,  # enable/disable screenshot capture
                "capture_on_focus_change": True,  # capture on window focus change
                "min_seconds_between_captures": 10,  # minimum seconds between captures
                "screenshot_path": DEFAULT_SCREENSHOT_FOLDER,  # base path for screenshots
            },
            "spheres": {
                "General": {"is_default": True, "active": True},
            },
            "projects": {
                "General": {"sphere": "General", "is_default": True, "active": True},
                "Work": {"sphere": "General", "is_default": False, "active": True},
                "Personal": {"sphere": "General", "is_default": False, "active": True},
            },
            "break_actions": {"Resting": {"is_default": True, "active": True}},
        }

        if not os.path.exists(self.settings_file):
            with open(self.settings_file, "w") as f:
                json.dump(default_settings, f, indent=2)
            return default_settings

        try:
            with open(self.settings_file, "r") as f:
                return json.load(f)
        except Exception:
            return default_settings

    def _get_default_sphere(self):
        """Get the default sphere from settings"""
        for sphere, data in self.settings["spheres"].items():
            if data.get("is_default", False):
                return sphere
        # Fallback to first active sphere if no default found
        for sphere, data in self.settings["spheres"].items():
            if data.get("active", True):
                return sphere
        return "General"

    def get_active_spheres(self):
        """Get list of active spheres and default sphere"""
        active_spheres = [
            sphere
            for sphere, data in self.settings["spheres"].items()
            if data.get("active", True)
        ]

        default_sphere = next(
            (
                sphere
                for sphere, data in self.settings["spheres"].items()
                if data.get("is_default", False)
            ),
            None,
        )

        return active_spheres, default_sphere

    def get_active_projects(self, sphere=None):
        """Get active projects, optionally filtered by sphere"""
        projects = []
        for project, data in self.settings.get("projects", {}).items():
            if not data.get("active", True):
                continue
            if sphere and data.get("sphere") != sphere:
                continue
            projects.append(project)

        return projects

    def get_default_project(self, sphere):
        """Get default project for a sphere"""
        # First try to find default project in the sphere
        for project, data in self.settings.get("projects", {}).items():
            if (
                data.get("sphere") == sphere
                and data.get("is_default", False)
                and data.get("active", True)
            ):
                return project

        # Fallback to first active project in the sphere
        for project, data in self.settings.get("projects", {}).items():
            if data.get("sphere") == sphere and data.get("active", True):
                return project

        return None

    def get_active_break_actions(self):
        """Get break actions and default break action"""
        break_actions = [
            action
            for action, data in self.settings["break_actions"].items()
            if data.get("active", True)
        ]

        default_action = next(
            (
                action
                for action, data in self.settings["break_actions"].items()
                if data.get("is_default", True)
            ),
            None,
        )

        return break_actions, default_action

    def load_data(self):
        """Load existing session data from the data file.

        Reads the data.json file containing all saved session information.
        Returns an empty dictionary if the file doesn't exist or cannot be read.

        Returns:
            dict: Dictionary mapping session names to session data, or empty dict if:
                - data.json file doesn't exist
                - File cannot be read due to permissions/corruption
                - JSON parsing fails

        Note:
            This method silently handles errors by returning {} rather than raising
            exceptions, allowing the app to continue with empty/new data.
        """
        if not os.path.exists(self.data_file):
            return {}

        try:
            with open(self.data_file, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_data(self, session_data, merge=True):
        """Save session data to file

        Args:
            session_data: Data to save
            merge: If True, merge with existing data. If False, replace entirely.
        """
        try:
            if merge:
                all_data = self.load_data()
                all_data.update(session_data)
            else:
                # Safety check: Don't save if replacement data is empty
                if not session_data:
                    return
                all_data = session_data

            with open(self.data_file, "w") as f:
                json.dump(all_data, f, indent=2)
        except Exception as error:
            messagebox.showerror(
                "Save Error",
                f"Failed to save session data to {self.data_file}\n\n"
                f"Error: {error}\n\n"
                "Your session data may not be saved. Please check file permissions.",
            )

    def create_widgets(self):
        """Create the main GUI elements for the time tracker interface.

        Builds the complete user interface including:
        - Scrollable main frame container
        - Top navigation links (Settings, Analysis, Session View)
        - Session name entry field
        - Session control buttons (Start/End Session, Start/End Break)
        - Timer displays (Session, Break, Total Active, Total Break)
        - Status indicator label

        Side effects:
            - Creates self.main_frame_container (ScrollableFrame)
            - Initializes all UI widgets (buttons, labels, entry fields)
            - Sets initial button states (Start enabled, End/Break disabled)
            - Configures grid layout and padding
            - Binds click handlers to navigation links

        Note:
            This is called once during __init__ to set up the entire main UI.
        """
        # Create scrollable container for main frame
        self.main_frame_container = ScrollableFrame(self.root, padding="10")
        self.main_frame_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        main_frame = self.main_frame_container.get_content_frame()

        # Top-right utility links frame
        top_right_frame = ttk.Frame(main_frame)
        top_right_frame.grid(row=0, column=2, sticky=tk.E, pady=5)

        # Get background color to match frame
        frame_bg = get_frame_background()

        # Settings link (top right)
        settings_link = tk.Label(
            top_right_frame,
            text="Settings",
            fg=COLOR_LINK_BLUE,
            bg=frame_bg,
            cursor="hand2",
            font=FONT_LINK,
        )
        settings_link.grid(row=0, column=0, padx=8)
        settings_link.bind("<Button-1>", lambda e: self.open_settings())

        # Analysis link (top right)
        analysis_link = tk.Label(
            top_right_frame,
            text="Analysis",
            fg=COLOR_LINK_BLUE,
            bg=frame_bg,
            cursor="hand2",
            font=FONT_LINK,
        )
        analysis_link.grid(row=0, column=1, padx=8)
        analysis_link.bind("<Button-1>", lambda e: self.open_analysis())

        # Session View link (top right)
        session_view_link = tk.Label(
            top_right_frame,
            text="Session View",
            fg=COLOR_LINK_BLUE,
            bg=frame_bg,
            cursor="hand2",
            font=FONT_LINK,
        )
        session_view_link.grid(row=0, column=2, padx=8)
        session_view_link.bind("<Button-1>", lambda e: self.open_session_view())

        # Session start info
        self.session_start_label = ttk.Label(
            main_frame, text="", font=FONT_NORMAL, foreground=COLOR_GRAY_TEXT
        )
        self.session_start_label.grid(row=1, column=0, columnspan=3, pady=(5, 0))

        # Session timer
        session_timer_frame = ttk.Frame(main_frame)
        session_timer_frame.grid(row=2, column=0, columnspan=3, pady=(5, 2))
        ttk.Label(session_timer_frame, text="Session Time:", font=FONT_HEADING).pack()
        self.session_timer_label = ttk.Label(
            session_timer_frame, text="00:00:00", font=FONT_TIMER_LARGE
        )
        self.session_timer_label.pack()

        # Break timer
        break_timer_frame = ttk.Frame(main_frame)
        break_timer_frame.grid(row=3, column=0, columnspan=3, pady=2)
        ttk.Label(break_timer_frame, text="Break Time:", font=FONT_NORMAL).pack()
        self.break_timer_label = ttk.Label(
            break_timer_frame, text="00:00:00", font=FONT_TIMER_MEDIUM
        )
        self.break_timer_label.pack()

        # Total times display (Active / Break)
        totals_frame = ttk.Frame(main_frame)
        totals_frame.grid(row=4, column=0, columnspan=3, pady=(2, 2))

        # Total Active Time
        active_frame = ttk.Frame(totals_frame)
        active_frame.pack(side=tk.LEFT, padx=20)
        ttk.Label(active_frame, text="Total Active:", font=FONT_SMALL).pack()
        self.total_active_label = ttk.Label(
            active_frame,
            text="00:00:00",
            font=FONT_TIMER_SMALL,
            foreground=COLOR_ACTIVE_GREEN,
        )
        self.total_active_label.pack()

        # Total Break Time
        break_total_frame = ttk.Frame(totals_frame)
        break_total_frame.pack(side=tk.LEFT, padx=20)
        ttk.Label(break_total_frame, text="Total Break:", font=FONT_SMALL).pack()
        self.total_break_label = ttk.Label(
            break_total_frame,
            text="00:00:00",
            font=FONT_TIMER_SMALL,
            foreground=COLOR_BREAK_ORANGE,
        )
        self.total_break_label.pack()

        # Status label
        self.status_label = ttk.Label(
            main_frame, text="Ready to start", font=FONT_NORMAL
        )
        self.status_label.grid(row=5, column=0, columnspan=3, pady=5)

        # Bottom control buttons (Start, Break, End only)
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=10)

        self.start_button = ttk.Button(
            button_frame, text="Start Session", command=self.start_session
        )
        self.start_button.grid(row=0, column=0, padx=5)

        # Break button disabled until session starts (enabled in start_session())
        self.break_button = ttk.Button(
            button_frame,
            text="Start Break",
            command=self.toggle_break,
            state=tk.DISABLED,
        )
        self.break_button.grid(row=0, column=1, padx=5)

        # End Session button disabled until session starts (enabled in start_session())
        self.end_button = ttk.Button(
            button_frame,
            text="End Session",
            command=self.end_session,
            state=tk.DISABLED,
        )
        self.end_button.grid(row=0, column=2, padx=5)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Store references
        self.main_frame = main_frame

    def format_time(self, seconds):
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // SECONDS_PER_HOUR)
        minutes = int((seconds % SECONDS_PER_HOUR) // SECONDS_PER_MINUTE)
        secs = int(seconds % SECONDS_PER_MINUTE)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def start_input_monitoring(self):
        """Start monitoring keyboard and mouse input for idle detection.

        Sets up pynput listeners to track user activity (mouse movement, clicks,
        scrolling, and keyboard presses). When activity is detected after an idle
        period, this method handles the complex transition back to active state:
        - Saves the completed idle period with duration
        - Saves the pre-idle active period (from last active start to idle start)
        - Starts a new active period from when activity resumed
        - Manages screenshot capture transitions between periods

        The on_activity callback is triggered on ANY input event and updates
        last_user_input timestamp used by check_idle() for threshold detection.

        Side effects:
            - Sets input_listener_running flag to True
            - Creates and starts mouse_listener (pynput.mouse.Listener)
            - Creates and starts keyboard_listener (pynput.keyboard.Listener)
            - When resuming from idle:
                - Updates session_idle flag to False
                - Saves idle period end time to data.json
                - Saves pre-idle active period with screenshot info
                - Starts new active period with fresh screenshot capture
                - Updates active_period_start_time to current time



        CRITICAL: This method implements complex state transitions when resuming
        from idle. It must save the active period that ended when idle started,
        then start a fresh active period from when idle ended. This preserves
        accurate time tracking boundaries.
        """
        if self.input_listener_running:
            return

        self.input_listener_running = True
        self.last_user_input = time.time()

        def on_activity(*args):
            try:
                self.last_user_input = time.time()
                if self.session_idle:
                    self.session_idle = False
                    self.status_label.config(text="Active")
                    # Save idle period end
                    all_data = self.load_data()
                    if self.session_name in all_data:
                        idle_periods = all_data[self.session_name]["idle_periods"]
                        # Check if there are any idle periods and the last one doesn't have an end time
                        if idle_periods and "end" not in idle_periods[-1]:
                            last_idle = idle_periods[-1]
                            last_idle["end"] = datetime.now().strftime("%H:%M:%S")
                            last_idle["end_timestamp"] = self.last_user_input
                            last_idle["duration"] = (
                                last_idle["end_timestamp"]
                                - last_idle["start_timestamp"]
                            )

                            # Save the active period that ended when idle started,
                            # then start a new active period from when idle ended
                            all_data[self.session_name]["active"] = all_data[
                                self.session_name
                            ].get("active", [])

                            # Build active period from last active_period_start_time to idle start
                            idle_start_time = last_idle["start_timestamp"]
                            pre_idle_active_period = {
                                "start": datetime.fromtimestamp(
                                    self.active_period_start_time
                                ).strftime("%H:%M:%S"),
                                "start_timestamp": self.active_period_start_time,
                                "end": datetime.fromtimestamp(idle_start_time).strftime(
                                    "%H:%M:%S"
                                ),
                                "end_timestamp": idle_start_time,
                                "duration": idle_start_time
                                - self.active_period_start_time,
                            }

                            # Add screenshot info if any were captured
                            current_screenshots = (
                                self.screenshot_capture.get_current_period_screenshots()
                            )
                            if self.screenshot_capture.enabled and current_screenshots:
                                screenshot_folder = (
                                    self.screenshot_capture.get_screenshot_folder_path()
                                )
                                if screenshot_folder:
                                    pre_idle_active_period["screenshot_folder"] = (
                                        os.path.relpath(
                                            screenshot_folder,
                                            os.path.dirname(self.data_file),
                                        )
                                    )
                                    pre_idle_active_period["screenshots"] = (
                                        current_screenshots
                                    )

                            all_data[self.session_name]["active"].append(
                                pre_idle_active_period
                            )

                            # Start new active period from when idle ended (NOW)
                            self.active_period_start_time = self.last_user_input

                            # Start fresh screenshot capture for new active period
                            active_period_count = len(
                                all_data[self.session_name]["active"]
                            )
                            self.screenshot_capture.set_current_session(
                                self.session_name, "active", active_period_count
                            )

                            self.save_data(all_data)
            except Exception as error:
                # Show error notification once for user-actionable issues (disk full, permissions)
                # After first notification, fail silently to avoid spamming on every input event
                if not self.input_monitoring_error_shown:
                    self.input_monitoring_error_shown = True
                    messagebox.showerror(
                        "Input Monitoring Error",
                        f"Error saving idle/active period data:\n\n{error}\n\n"
                        "This could be due to disk space or file permissions.\n"
                        "Input monitoring will continue, but some data may not be saved.",
                    )

        # Start mouse listener with error suppression
        self.mouse_listener = mouse.Listener(
            on_move=on_activity,
            on_click=on_activity,
            on_scroll=on_activity,
            suppress=False,
        )
        self.mouse_listener.start()

        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(on_press=on_activity)
        self.keyboard_listener.start()

    def stop_input_monitoring(self):
        """Stop monitoring input"""
        self.input_listener_running = False

        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None

        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None

    def start_session(self):
        """Start a new tracking session.

        Creates a new time tracking session with a unique name based on the current
        date and timestamp. Initializes session state, saves initial session data to
        the data file, updates the UI to reflect the active session, and starts input
        monitoring and screenshot capture (if enabled).

        The session name format is: YYYY-MM-DD_<unix_timestamp>

        Side effects:
            - Creates new session entry in data.json
            - Enables End Session and Start Break buttons
            - Starts input monitoring for idle detection
            - Starts screenshot capture for the first active period
            - Updates status label to "Session active"
        """
        if self.session_active:
            return

        # Initialize session
        self.session_active = True
        self.session_start_time = time.time()
        self.active_period_start_time = self.session_start_time
        self.session_elapsed = 0
        self.total_break_time = 0

        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")
        # Unique session name with date and timestamp
        self.session_name = f"{current_date}_{int(self.session_start_time)}"

        settings = self.get_settings()

        # Create session data
        session_data = {
            self.session_name: {
                "sphere": (self._get_default_sphere() if settings else "General"),
                "date": current_date,
                "start_time": current_time,
                "start_timestamp": self.session_start_time,
                "breaks": [],
                "idle_periods": [],
            }
        }

        # Save initial session
        self.save_data(session_data)

        # Update UI
        self.start_button.config(state=tk.DISABLED)
        self.end_button.config(state=tk.NORMAL)
        self.break_button.config(state=tk.NORMAL)
        self.status_label.config(text="Session active")

        # Update session start label
        start_datetime = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        self.session_start_label.config(text=f"Started: {start_datetime}")

        # Reset total time labels
        self.total_active_label.config(text="00:00:00")
        self.total_break_label.config(text="00:00:00")

        # Start input monitoring
        self.start_input_monitoring()

        # Start screenshot capture for first active period
        self.screenshot_capture.set_current_session(self.session_name, "active", 0)
        self.screenshot_capture.start_monitoring()

    def end_session(self):
        """End the current tracking session.

        Finalizes the current session by saving the final active period, calculating
        total elapsed time, active time, and break time, updating the session data in
        the data file, and displaying the completion frame for labeling session actions.

        If a break is active when ending the session, it will be automatically ended
        first. Input monitoring and screenshot capture are stopped.

        Side effects:
            - Saves final active period to data.json with screenshot info
            - Stops input monitoring (mouse/keyboard listeners)
            - Stops screenshot capture
            - Calculates and saves final time statistics
            - Resets UI to inactive state
            - Shows completion frame for activity labeling

        Note:
            Session name is retained after ending to support completion frame workflow.
        """
        if not self.session_active:
            return

        end_on_break = False

        # End any active break
        if self.break_active:
            self.toggle_break()
            end_on_break = True

        current_time = time.time()
        duration = current_time - self.active_period_start_time

        # Save the final active period (if not on break)
        if not end_on_break:

            all_data = self.load_data()
            if self.session_name in all_data:
                all_data[self.session_name]["active"] = all_data[self.session_name].get(
                    "active", []
                )
                # Build final active period with screenshot data
                final_period = {
                    "start": datetime.fromtimestamp(
                        self.active_period_start_time
                    ).strftime("%H:%M:%S"),
                    "start_timestamp": self.active_period_start_time,
                    "end": datetime.fromtimestamp(current_time).strftime("%H:%M:%S"),
                    "end_timestamp": current_time,
                    "duration": duration,
                }
                # Add screenshot info if any were captured
                current_screenshots = (
                    self.screenshot_capture.get_current_period_screenshots()
                )
                if self.screenshot_capture.enabled and current_screenshots:
                    screenshot_folder = (
                        self.screenshot_capture.get_screenshot_folder_path()
                    )
                    if screenshot_folder:
                        final_period["screenshot_folder"] = os.path.relpath(
                            screenshot_folder, os.path.dirname(self.data_file)
                        )
                        final_period["screenshots"] = current_screenshots
                all_data[self.session_name]["active"].append(final_period)
                self.save_data(all_data)

        # Stop input monitoring
        self.stop_input_monitoring()

        # Stop screenshot capture
        self.screenshot_capture.stop_monitoring()

        # Calculate final time using original session start time
        end_time = time.time()
        # Load original start time from saved data
        all_data = self.load_data()
        original_start = all_data.get(self.session_name, {}).get(
            "start_timestamp", self.session_start_time
        )
        total_elapsed = end_time - original_start
        active_time = total_elapsed - self.total_break_time
        break_time = self.total_break_time

        # Update session data (all_data already loaded above)
        if self.session_name in all_data:
            all_data[self.session_name]["end_time"] = datetime.now().strftime(
                "%H:%M:%S"
            )
            all_data[self.session_name]["end_timestamp"] = end_time
            all_data[self.session_name]["total_duration"] = total_elapsed
            all_data[self.session_name]["active_duration"] = active_time
            all_data[self.session_name]["break_duration"] = break_time

            # Apply defaults to any unassigned periods so data is complete for analysis
            session = all_data[self.session_name]

            # Get defaults using helper methods that parse JSON structure correctly
            default_sphere = self._get_default_sphere()
            default_project = self.get_default_project(default_sphere)
            _, default_break_action = self.get_active_break_actions()

            # Fallback if helpers return None
            if not default_sphere:
                default_sphere = "General"
            if not default_project:
                default_project = "General"
            if not default_break_action:
                default_break_action = "Break"

            # Apply default sphere if not set
            if not session.get("sphere"):
                session["sphere"] = default_sphere

            # Apply default project to active periods without project
            for active_period in session.get("active", []):
                has_project = active_period.get("project") or active_period.get(
                    "projects"
                )
                if not has_project:
                    active_period["project"] = default_project

            # Apply default action to break periods without action
            for break_period in session.get("breaks", []):
                has_action = break_period.get("action") or break_period.get("actions")
                if not has_action:
                    break_period["action"] = default_break_action

            # Apply default action to idle periods without action
            for idle_period in session.get("idle_periods", []):
                has_action = idle_period.get("action") or idle_period.get("actions")
                if not has_action:
                    idle_period["action"] = default_break_action

            self.save_data(all_data)

        # Reset state (but keep session_name for completion frame)
        self.session_active = False
        self.session_start_time = None
        self.session_elapsed = 0

        # Update UI
        self.start_button.config(state=tk.NORMAL)
        self.end_button.config(state=tk.DISABLED)
        self.break_button.config(state=tk.DISABLED)
        self.status_label.config(text="Session ended")
        self.session_timer_label.config(text="00:00:00")
        self.session_start_label.config(text="")
        self.total_active_label.config(text="00:00:00")
        self.total_break_label.config(text="00:00:00")

        # Show completion frame to label actions
        self.show_completion_frame()

    def toggle_break(self):
        """Start or end a break period.

        Toggles between break and active states during a session. When starting a break,
        saves the current active period with screenshot data and switches screenshot
        capture to the break period. When ending a break, saves the break period data
        and starts a new active period.

        If the break was auto-started due to idle detection, uses the idle start time
        as the break start time instead of the current time.

        Side effects:
            Starting a break:
                - Saves current active period to data.json
                - Switches screenshot capture to break period
                - Updates status label to "On break"
                - Changes button text to "End Break"

            Ending a break:
                - Saves break period to data.json
                - Increments total_break_time counter
                - Switches screenshot capture back to active period
                - Updates status label to "Session active"
                - Changes button text to "Start Break"
        """
        if not self.session_active:
            return

        if not self.break_active:
            # Start break
            self.break_active = True
            self.break_start_time = time.time()
            # if break started due to idle, use that start time
            if self.auto_break_start_time_from_idle:
                self.break_start_time = self.auto_break_start_time_from_idle
                self.auto_break_start_time_from_idle = None
            self.break_elapsed = 0
            self.break_button.config(text="End Break")
            self.status_label.config(text="On break")
            # Save the end of the active period before break
            all_data = self.load_data()
            if self.session_name in all_data:
                all_data[self.session_name]["active"] = all_data[self.session_name].get(
                    "active", []
                )
                # Add screenshot folder to the active period
                active_period = {
                    "start": datetime.fromtimestamp(
                        self.active_period_start_time
                    ).strftime("%H:%M:%S"),
                    "start_timestamp": self.active_period_start_time,
                    "end": datetime.fromtimestamp(self.break_start_time).strftime(
                        "%H:%M:%S"
                    ),
                    "end_timestamp": self.break_start_time,
                    "duration": self.break_start_time - self.active_period_start_time,
                }
                # Add screenshot info if any were captured
                current_screenshots = (
                    self.screenshot_capture.get_current_period_screenshots()
                )
                if self.screenshot_capture.enabled and current_screenshots:
                    screenshot_folder = (
                        self.screenshot_capture.get_screenshot_folder_path()
                    )
                    if screenshot_folder:
                        active_period["screenshot_folder"] = os.path.relpath(
                            screenshot_folder, os.path.dirname(self.data_file)
                        )
                        active_period["screenshots"] = current_screenshots
                all_data[self.session_name]["active"].append(active_period)
                self.save_data(all_data)

            # Switch screenshot capture to break period
            break_period_count = len(all_data[self.session_name].get("breaks", []))
            self.screenshot_capture.set_current_session(
                self.session_name, "break", break_period_count
            )
        else:
            # End break
            break_duration = time.time() - self.break_start_time

            # Save break data
            all_data = self.load_data()
            if self.session_name in all_data:
                break_period = {
                    "start": datetime.fromtimestamp(self.break_start_time).strftime(
                        "%H:%M:%S"
                    ),
                    "start_timestamp": self.break_start_time,
                    "end": datetime.now().strftime("%H:%M:%S"),
                    "end_timestamp": time.time(),
                    "duration": break_duration,
                }
                # Add screenshot info if any were captured
                current_screenshots = (
                    self.screenshot_capture.get_current_period_screenshots()
                )
                if self.screenshot_capture.enabled and current_screenshots:
                    screenshot_folder = (
                        self.screenshot_capture.get_screenshot_folder_path()
                    )
                    if screenshot_folder:
                        break_period["screenshot_folder"] = os.path.relpath(
                            screenshot_folder, os.path.dirname(self.data_file)
                        )
                        break_period["screenshots"] = current_screenshots
                all_data[self.session_name]["breaks"].append(break_period)
                self.save_data(all_data)

            # Track cumulative break time
            self.total_break_time += break_duration

            # Reset break state
            self.break_active = False
            self.break_start_time = None
            self.break_elapsed = 0
            self.break_button.config(text="Start Break")
            self.status_label.config(text="Session active")

            # Start new active period
            self.active_period_start_time = time.time()

            # Switch screenshot capture back to active period
            active_period_count = len(all_data[self.session_name].get("active", []))
            self.screenshot_capture.set_current_session(
                self.session_name, "active", active_period_count
            )

    def show_completion_frame(self):
        """Display session completion UI for labeling and saving session data.

        Called at the end of every session to allow user to categorize the session
        with sphere, project, break actions, and notes. Creates a ScrollableFrame
        container with CompletionFrame inside.

        CompletionFrame loads all session data (times, breaks, etc.) from data.json
        using self.session_name, so no parameters are needed.

        Called from:
        - end_session() - After session ends normally

        Side effects:
            - Hides main_frame_container via grid_remove()
            - Creates completion_container (ScrollableFrame)
            - Creates completion_frame (CompletionFrame) inside container
            - Passes session_name to CompletionFrame for data lookup
            - Stores canvas reference in completion_frame for scrolling
            - Updates window title (done by CompletionFrame)

        Note:
            CompletionFrame handles all session data editing and saving.
            After save/skip, calls back to tracker.show_main_frame().
        """
        # Hide main frame
        self.main_frame_container.grid_remove()

        # Create scrollable container for completion frame
        self.completion_container = ScrollableFrame(self.root)
        self.completion_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Get content frame and create completion frame with session name
        completion_parent = self.completion_container.get_content_frame()
        self.completion_frame = CompletionFrame(
            completion_parent, self, self.session_name
        )
        self.completion_frame.pack(fill="both", expand=True)

    def show_main_frame(self):
        """Return to main tracker view from any other frame (analysis/completion/session view).

        Central navigation hub that cleanly destroys all other frame types and
        restores the main time tracking interface. Handles 3 possible frame sources:
        - Analysis frame (from viewing statistics)
        - Completion/Session View container (CompletionFrame - from ending session or viewing past sessions)
        - Multiple frames simultaneously (edge case, handles gracefully)

        Called from:
        - CompletionFrame.save_and_close() - After saving session
        - CompletionFrame.skip_session() - After skipping session
        - close_analysis() - When closing analysis frame
        - Navigation buttons in various frames

        Side effects:
        - Destroys analysis_frame if present (grid_remove + destroy + clear ref)
        - Destroys completion_container and completion_frame (grid_remove + destroy + clear refs)
        - Destroys session_view_container and session_view_frame (grid_remove + destroy + clear refs)
        - Re-enables main_frame_container scrolling (sets _is_alive = True)
        - Shows main_frame_container via grid(row=0, column=0, sticky all sides)
        - Restores window title to "Time Aligned - Time Tracker"
        - Clears session_name if no active session (prevents stale data)

        Error handling:
            Uses try/except around all destroy() calls to handle already-destroyed frames.
            Ensures main frame always becomes visible even if cleanup fails.

        Note:
            Order of operations ensures no orphaned frames. Always clears references
            after destroying to prevent use-after-free bugs.
        """
        # Remove analysis frame if present
        if hasattr(self, "analysis_frame") and self.analysis_frame:
            self.analysis_frame.grid_remove()
            self.analysis_frame.destroy()
            self.analysis_frame = None

        # Remove completion container (from end session)
        if hasattr(self, "completion_container") and self.completion_container:
            self.completion_container.grid_remove()
            self.completion_container.destroy()
            self.completion_container = None

        if hasattr(self, "completion_frame") and self.completion_frame:
            self.completion_frame = None

        # Remove session view container (from session view)
        if hasattr(self, "session_view_container") and self.session_view_container:
            self.session_view_container.grid_remove()
            self.session_view_container.destroy()
            self.session_view_container = None

        if hasattr(self, "session_view_frame") and self.session_view_frame:
            self.session_view_frame = None

        # Show main frame
        self.main_frame_container._is_alive = True  # Re-enable scrolling
        self.main_frame_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Restore window title
        self.root.title("Time Aligned - Time Tracker")

        # Clear session name only if no active session
        if not self.session_active:
            self.session_name = None

    def check_idle(self):
        """Check if user is idle and update session status accordingly.

        Monitors time since last user input (mouse/keyboard activity) and detects idle
        periods based on the configured idle threshold. When idle is detected, records
        the start of the idle period. If idle exceeds the break threshold, automatically
        starts a break.

        IMPORTANT: Idle detection is threshold-based. The period before idle is detected
        still counts as active time. Idle time is only tracked from the moment the
        threshold is exceeded, not retroactively.

        Does nothing if:
            - No session is active
            - A break is already active
            - Idle tracking is disabled in settings

        Side effects:
            When newly idle:
                - Sets session_idle flag to True
                - Records idle_start_time as current time
                - Saves idle period start to data.json
                - Updates status label to "Idle detected"

            When idle exceeds break threshold:
                - Auto-starts a break using toggle_break()
                - Sets auto_break_start_time_from_idle for accurate break timing
        """
        if not self.session_active or self.break_active:
            return

        # Skip idle tracking if disabled in settings
        if not self.settings.get("idle_settings", {}).get(
            "idle_tracking_enabled", True
        ):
            return

        idle_time = time.time() - self.last_user_input

        # Check if newly idle
        if (
            not self.session_idle
            and idle_time >= self.settings["idle_settings"]["idle_threshold"]
        ):
            self.session_idle = True
            # CRITICAL: Idle starts NOW (when detected), not retroactively from last input
            # The threshold period counts as active time
            self.idle_start_time = time.time()
            self.status_label.config(text="Idle detected")

            # Save idle period start
            all_data = self.load_data()
            if self.session_name in all_data:
                all_data[self.session_name]["idle_periods"].append(
                    {
                        "start": datetime.fromtimestamp(self.idle_start_time).strftime(
                            "%H:%M:%S"
                        ),
                        "start_timestamp": self.idle_start_time,
                    }
                )
                self.save_data(all_data)

        # Check if idle long enough for auto-break
        elif (
            self.session_idle
            and idle_time >= self.settings["idle_settings"]["idle_break_threshold"]
        ):
            if not self.break_active:
                # stat of break should be idle start time
                self.auto_break_start_time_from_idle = self.idle_start_time
                self.toggle_break()

    def update_timers(self):
        """Update timer displays and perform periodic background tasks.

        Called every 100ms (UPDATE_TIMER_INTERVAL_MS) by the Tkinter event loop.
        Updates session timer, break timer, total active time, and total break time
        labels. Also performs periodic tasks like idle checking and auto-backup.

        Side effects:
            - Updates system tray icon with current session status
            - Updates session_timer_label with current active time
            - Updates break_timer_label with current break duration
            - Updates total_active_label with cumulative active time
            - Updates total_break_label with cumulative break time
            - Calls check_idle() to monitor for idle periods
            - Auto-saves session data every minute to prevent data loss
            - Triggers screenshot capture (if enabled)

        Note:
            This method implements a backup loop counter that triggers auto-save
            every minute (60000ms / 100ms = 600 iterations) to protect against
            unexpected program termination.
        """
        # Update tray icon periodically
        self.update_tray_icon()

        if self.session_active and not self.break_active:
            # Calculate active time by subtracting breaks from total elapsed
            total_elapsed = time.time() - self.session_start_time
            self.session_elapsed = total_elapsed - self.total_break_time
            self.session_timer_label.config(text=self.format_time(self.session_elapsed))

            # Update total active time
            self.total_active_label.config(text=self.format_time(self.session_elapsed))

            # Check for idle
            self.check_idle()

        if self.break_active:
            # Get current time once for all calculations
            current_time = time.time()
            self.break_elapsed = current_time - self.break_start_time

            # Update break timer (current break)
            self.break_timer_label.config(text=self.format_time(self.break_elapsed))

            # Total break stays at previous cumulative value (updates only when break ends)
            # No need to update total_break_label here
        else:
            self.break_timer_label.config(text="00:00:00")

            # Update total break time when not on break (shows cumulative total)
            if self.session_active:
                self.total_break_label.config(
                    text=self.format_time(self.total_break_time)
                )
            else:
                # Reset total break when no session is active
                self.total_break_label.config(text="00:00:00")

        # save in case computer crashes or runtime stops unexpectedly
        if self.backup_loop_count == self.backup_frequency:
            # Update session data
            if self.session_active:
                all_data = self.load_data()
                if self.session_name in all_data:
                    all_data[self.session_name]["end_time"] = datetime.now().strftime(
                        "%H:%M:%S"
                    )
                    all_data[self.session_name]["end_timestamp"] = time.time()
                    all_data[self.session_name]["total_duration"] = (
                        time.time() - all_data[self.session_name]["start_timestamp"]
                    )
                    all_data[self.session_name]["active_duration"] = (
                        all_data[self.session_name]["total_duration"]
                        - self.total_break_time
                    )
                    all_data[self.session_name][
                        "break_duration"
                    ] = self.total_break_time
                    self.save_data(all_data)

                # Collect screenshot if capture is enabled (monitor thread handles actual capture)
                # Just check if new screenshots were captured and add to tracking list
                # This is handled automatically by the ScreenshotCapture monitor thread

            self.backup_loop_count = 0
        self.backup_loop_count += 1

        # Schedule next update
        self.root.after(self.update_timer_interval, self.update_timers)

    def open_settings(self):
        """Open the settings window"""
        # Don't allow opening settings while tracking time
        if self.session_active:
            messagebox.showwarning(
                "Session Active",
                "Cannot open settings while tracking time. Please end the session first.",
            )
            return

        if self.settings_frame is not None:
            # Settings already open, do nothing
            return

        # Hide main frame
        self.main_frame_container.grid_forget()

        # Create settings frame in main window
        self.settings_frame = SettingsFrame(self.root, self, self.root)
        self.settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Update window title
        self.root.title("Time Aligned - Settings")

    def close_settings(self):
        """Close settings and return to main view"""
        if self.settings_frame is not None:
            # Destroy settings frame
            self.settings_frame.destroy()
            self.settings_frame = None

            # Reload settings in case they changed
            self.settings = self.get_settings()

            # Update screenshot capture settings
            self.screenshot_capture.update_settings(self.settings)

            # Show main frame again
            self.main_frame_container._is_alive = True  # Re-enable scrolling
            self.main_frame_container.grid(
                row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S)
            )

            # Restore window title
            self.root.title("Time Aligned - Time Tracker")
            # Re-enable main frame scrolling
            self.main_frame_container._is_alive = True

    def open_analysis(self):
        """Open the analysis frame with proper state management and navigation handling.

        Displays the analysis view for reviewing session data, statistics, and timeline.
        Handles complex navigation scenarios:
        - Coming from main tracker view (normal case)
        - Coming from completion/session view (CompletionFrame - prompts to save unsaved data)
        - Re-opening analysis while already open (destroys old instance)

        Always creates a fresh AnalysisFrame instance to avoid state persistence bugs
        (e.g., after CSV export the frame needs clean state).

        Side effects:
            - Blocks if session is active (shows warning and returns)
            - Destroys existing analysis_frame if present
            - If coming from completion frame:
                - Prompts user to save/skip/cancel unsaved session data
                - Sets analysis_from_completion flag for proper back navigation
            - Hides main_frame_container and disables its scrolling
            - Hides/destroys completion_container if present
            - Closes session_view properly (destroys container, clears references)
            - Creates new AnalysisFrame instance
            - Updates window title to "Time Aligned - Analysis"

        Navigation Flow:
            Main → Analysis: Standard open
            Completion → Analysis: Save prompt → sets analysis_from_completion flag
            Session View → Analysis: If analysis exists, just close session view
            Analysis → Analysis: Destroys old instance, creates fresh one
        """
        # Don't allow opening analysis while tracking time
        if self.session_active:
            messagebox.showwarning(
                "Session Active",
                "Cannot open analysis while tracking time. Please end the session first.",
            )
            return

        # Special case: if we're in session view and analysis already exists,
        # just close session view to return to analysis
        if (
            hasattr(self, "session_view_frame")
            and self.session_view_frame is not None
            and hasattr(self, "analysis_frame")
            and self.analysis_frame is not None
        ):
            self.close_session_view()
            return

        # CRITICAL: Always create a fresh AnalysisFrame instance
        # Reusing the old instance causes state persistence bugs (e.g., after CSV export)
        # If analysis frame already exists, destroy it first
        if hasattr(self, "analysis_frame") and self.analysis_frame is not None:
            self.analysis_frame.destroy()
            self.analysis_frame = None

        # Track if we're coming from completion frame (for proper back navigation)
        self.analysis_from_completion = False

        # If we're in completion frame or session view, save data first
        if hasattr(self, "completion_frame") and self.completion_frame:
            # Ask user to save or skip before going to analysis
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved session data. Would you like to save before viewing analysis?\n\nYes = Save and open analysis\nNo = Skip and open analysis\nCancel = Stay here",
            )
            if result is None:  # Cancel
                return
            elif result:  # Yes - save
                # Save the completion frame data without navigating
                if hasattr(self.completion_frame, "save_and_close"):
                    self.completion_frame.save_and_close(navigate=False)
            # If No, just continue without saving

            # Mark that we came from completion frame
            self.analysis_from_completion = True

        # Hide current frames
        self.main_frame_container.grid_forget()
        # Disable main frame scrolling while hidden
        self.main_frame_container._is_alive = False

        # Hide completion container if present
        if hasattr(self, "completion_container") and self.completion_container:
            self.completion_container.grid_forget()

        # Close session view if present (don't just hide it)
        if hasattr(self, "session_view_frame") and self.session_view_frame is not None:
            # Properly close session view to clear references
            if hasattr(self, "session_view_container") and self.session_view_container:
                self.session_view_container.destroy()
                self.session_view_container = None
            self.session_view_frame = None
            self.session_view_from_analysis = False

        # Create analysis frame in main window
        self.analysis_frame = AnalysisFrame(self.root, self, self.root)
        self.analysis_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Update window title
        self.root.title("Time Aligned - Analysis")

    def close_analysis(self):
        """Close analysis frame and return to appropriate previous view.

        Handles complex navigation logic based on where user came from:
        - From completion frame: Returns to main tracker (not back to completion)
        - From main tracker: Returns to main tracker
        - From session view: Returns to session view

        Navigation states tracked:
        - analysis_from_completion: Flag set when opened from completion
        - session_view_open: Flag set when opened from session view

        Side effects:
            - Destroys analysis_frame and clears reference
            - If from completion: Clears analysis_from_completion flag,
              shows main_frame_container (skips completion frame)
            - If from session view: Re-opens session view to previous state
            - Otherwise: Shows main_frame_container normally
            - Re-enables main_frame scrolling via _is_alive flag
            - Reloads settings to pick up any changes made in analysis
            - Updates window title to "Time Aligned - Time Tracker"

        Note:
            Analysis frame is always destroyed when closing, never reused.
            Fresh instance created on next open to avoid state bugs.
        """
        if hasattr(self, "analysis_frame") and self.analysis_frame is not None:
            # Destroy analysis frame
            self.analysis_frame.destroy()
            self.analysis_frame = None

            # If we came from completion frame, user wants to go to tracker (not back to completion)
            if (
                hasattr(self, "analysis_from_completion")
                and self.analysis_from_completion
            ):
                # Destroy completion frame/container
                if hasattr(self, "completion_container") and self.completion_container:
                    self.completion_container.destroy()
                    self.completion_container = None
                if hasattr(self, "completion_frame"):
                    self.completion_frame = None

                # Show main tracker
                self.main_frame_container.grid(
                    row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S)
                )
                self.root.title("Time Aligned - Time Tracker")
                self.analysis_from_completion = False

            # Otherwise determine which frame to show based on what's available
            # If session view exists but was hidden (we're closing from analysis), go to main
            # Priority: main frame (session view was hidden when analysis opened)
            elif (
                hasattr(self, "session_view_frame")
                and self.session_view_frame is not None
                and hasattr(self, "session_view_container")
                and self.session_view_container
            ):
                # Session view was open but hidden - close it and go to main
                self.close_session_view()
                # Main frame will already be shown by close_session_view
            else:
                # Show main frame
                self.main_frame_container._is_alive = True  # Re-enable scrolling
                self.main_frame_container.grid(
                    row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S)
                )
                self.root.title("Time Aligned - Time Tracker")

            # Reload settings after closing analysis
            self.settings = self.get_settings()

    def open_session_view(self, from_analysis=False):
        """Open session view for viewing and editing past sessions.

        Creates a new window (or reuses existing) showing the CompletionFrame UI
        loaded with historical session data. Allows user to review and edit any
        past session from data.json.

        Called from:
        - Analysis frame "View Session" button
        - Tray menu "View Sessions"
        - Direct navigation from main tracker

        Args:
            from_analysis: Boolean, True if opened from analysis frame.
                          Sets session_view_open flag for proper back navigation.

        Side effects:
            - Blocks if session_active (shows warning and returns)
            - Hides analysis_frame if present (grid_remove, not destroy)
            - Hides main_frame_container if no analysis open
            - Disables main_frame scrolling (_is_alive = False)
            - Creates session_view_container (ScrollableFrame)
            - Creates session_view_frame (CompletionFrame) in "session view" mode
            - Sets session_view_open flag if from_analysis (for proper close_session_view)
            - Updates window title to "Time Aligned - Session View"

        Navigation state:
            If from_analysis=True, close_session_view() will restore analysis frame
            instead of main frame. This preserves user's workflow when viewing a
            session from the analysis timeline.

        Note:
            Session view uses CompletionFrame in special mode where it loads
            historical session data and allows editing without affecting active session.
        """
        # Don't allow opening session view while tracking time
        if self.session_active:
            messagebox.showwarning(
                "Session Active",
                "Cannot open session view while tracking time. Please end the session first.",
            )
            return

        if hasattr(self, "session_view_frame") and self.session_view_frame is not None:
            # Session view already open, do nothing
            return

        # Track where we came from
        self.session_view_from_analysis = from_analysis

        # Hide current frame
        if from_analysis and hasattr(self, "analysis_frame") and self.analysis_frame:
            self.analysis_frame.grid_forget()
        else:
            self.main_frame_container.grid_forget()

        # Create scrollable container for completion frame
        self.session_view_container = ScrollableFrame(self.root)
        self.session_view_container.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S)
        )

        # Get content frame and create completion frame (session view)
        session_view_parent = self.session_view_container.get_content_frame()
        self.session_view_frame = CompletionFrame(session_view_parent, self, None)
        self.session_view_frame.pack(fill="both", expand=True)

        # Update window title
        self.root.title("Time Aligned - Session View")

    def close_session_view(self):
        """Close session view and return to previous view"""
        if hasattr(self, "session_view_frame") and self.session_view_frame is not None:
            # Check where we came from before destroying
            came_from_analysis = (
                hasattr(self, "session_view_from_analysis")
                and self.session_view_from_analysis
            )

            # Destroy session view container
            if hasattr(self, "session_view_container"):
                self.session_view_container.destroy()
                self.session_view_container = None

            self.session_view_frame = None

            # Return to analysis frame if we came from there
            if came_from_analysis:
                # Destroy existing analysis frame to avoid state persistence bugs
                if hasattr(self, "analysis_frame") and self.analysis_frame is not None:
                    self.analysis_frame.destroy()
                    self.analysis_frame = None

                # Create fresh analysis instance
                self.open_analysis()
                self.session_view_from_analysis = False
            else:
                # Show main frame
                self.main_frame_container._is_alive = True  # Re-enable scrolling
                self.main_frame_container.grid(
                    row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S)
                )
                self.root.title("Time Aligned - Time Tracker")

    def create_tray_icon_image(self, state="idle"):
        """Generate colored circle icon for system tray based on application state.

        Creates 64x64 PIL Image with colored circle indicating current app state.
        Called by setup_tray_icon() for initial icon and update_tray_icon() for
        state changes.

        State color mapping:
        - "idle": Blue-gray (#607D8B) - No active session
        - "active": Green (#4CAF50) - Session active, working
        - "session_idle": Yellow (#FFEB3B) - Session active but user idle
        - "break": Amber (#FFC107) - Session active, on break

        Args:
            state: String state name ("idle", "active", "session_idle", "break")
                  Defaults to "idle" if unrecognized state

        Returns:
            PIL Image object (64x64 RGB) with colored circle on white background

        Note:
            Circle drawn with 8px margin, 2px black outline for visibility.
            Image format compatible with pystray.Icon.
        """
        image = Image.new("RGB", (TRAY_ICON_SIZE, TRAY_ICON_SIZE), "white")
        dc = ImageDraw.Draw(image)

        colors = {
            "idle": COLOR_TRAY_IDLE,
            "active": COLOR_TRAY_ACTIVE,
            "break": COLOR_TRAY_BREAK,
            "session_idle": COLOR_TRAY_SESSION_IDLE,
        }

        color = colors.get(state, COLOR_TRAY_IDLE)

        # Draw circle
        dc.ellipse(
            [
                TRAY_ICON_MARGIN,
                TRAY_ICON_MARGIN,
                TRAY_ICON_SIZE - TRAY_ICON_MARGIN,
                TRAY_ICON_SIZE - TRAY_ICON_MARGIN,
            ],
            fill=color,
            outline="black",
            width=TRAY_ICON_OUTLINE_WIDTH,
        )

        return image

    def setup_tray_icon(self):
        """Initialize system tray icon with menu in separate daemon thread.

        Creates pystray system tray icon with context menu for background operation.
        Allows users to control app without main window visible.

        Menu structure:
        - Show/Hide Window (default action, double-click)
        - SEPARATOR
        - Start Session (enabled only when no session active)
        - Start Break (enabled only when session active, not on break)
        - End Break (enabled only when session active, on break)
        - End Session (enabled only when session active)
        - SEPARATOR
        - Settings
        - Analysis
        - SEPARATOR
        - Quit

        Threading:
        - Runs in separate daemon thread (tray_thread)
        - Thread calls run_tray() which blocks on tray_icon.run()
        - Daemon thread exits automatically when main thread exits

        Side effects:
            - Creates tray_icon (pystray.Icon instance)
            - Starts tray_thread (daemon Thread)
            - Stores tray_icon reference for later updates via update_tray_icon()
            - Initial icon state is "idle" with title "Time Aligned - Ready"

        Note:
            Menu items use lambda for dynamic enable/disable based on session state.
            All menu handlers use root.after() for thread-safe tkinter operations.
        """

        def run_tray():
            # Create menu
            menu = pystray.Menu(
                pystray.MenuItem("Show/Hide Window", self.toggle_window, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "Start Session",
                    self.tray_start_session,
                    enabled=lambda item: not self.session_active,
                ),
                pystray.MenuItem(
                    "Start Break",
                    self.tray_toggle_break,
                    enabled=lambda item: self.session_active and not self.break_active,
                ),
                pystray.MenuItem(
                    "End Break",
                    self.tray_toggle_break,
                    enabled=lambda item: self.session_active and self.break_active,
                ),
                pystray.MenuItem(
                    "End Session",
                    self.tray_end_session,
                    enabled=lambda item: self.session_active,
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Settings", self.tray_open_settings),
                pystray.MenuItem("Analysis", self.tray_open_analysis),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", self.tray_quit),
            )

            # Create icon
            self.tray_icon = pystray.Icon(
                "TimeAligned",
                self.create_tray_icon_image("idle"),
                "Time Aligned - Ready",
                menu,
            )

            # Run icon (blocks until stopped)
            self.tray_icon.run()

        # Start tray icon in separate thread
        self.tray_thread = threading.Thread(target=run_tray, daemon=True)
        self.tray_thread.start()

    def update_tray_icon(self):
        """Update tray icon appearance and tooltip based on current session state.

        Called every 100ms by update_timers() to reflect real-time state changes.
        Updates both icon color and tooltip text.

        State transitions:
        - No session: "idle" state, blue-gray icon, "Time Aligned - Ready"
        - Session active (working): "active" state, green icon, "Time Aligned - Active (HH:MM:SS)"
        - Session active (idle): "session_idle" state, yellow icon, "Time Aligned - Idle (HH:MM:SS)"
        - Session active (break): "break" state, amber icon, "Time Aligned - Break (HH:MM:SS)"

        Tooltip format:
        - Shows current timer value in HH:MM:SS format
        - Active: Shows session_elapsed time
        - Break: Shows break_elapsed time
        - Idle: Shows "Ready" (no timer)

        Side effects:
            - Updates tray_icon.icon via create_tray_icon_image()
            - Updates tray_icon.title (tooltip text)
            - No-op if tray_icon is None (not initialized)

        Note:
            Uses format_time() to convert elapsed seconds to HH:MM:SS string.
            Called very frequently (10 times per second) so must be efficient.
        """
        if self.tray_icon is None:
            return

        if self.session_active:
            if self.break_active:
                state = "break"
                title = f"Time Aligned - Break ({self.format_time(int(self.break_elapsed))})"
            elif self.session_idle:
                state = "session_idle"
                title = f"Time Aligned - Idle ({self.format_time(int(self.session_elapsed))})"
            else:
                state = "active"
                title = f"Time Aligned - Active ({self.format_time(int(self.session_elapsed))})"
        else:
            state = "idle"
            title = "Time Aligned - Ready"

        self.tray_icon.icon = self.create_tray_icon_image(state)
        self.tray_icon.title = title

    def setup_global_hotkeys(self):
        """Register global keyboard shortcuts using pynput library.

        Sets up system-wide hotkeys that work even when app window not focused.
        Uses pynput.keyboard.GlobalHotKeys listener in separate thread.

        Registered hotkeys:
        - Ctrl+Shift+S: Start new session (_hotkey_start_session)
        - Ctrl+Shift+B: Toggle break state (_hotkey_toggle_break)
        - Ctrl+Shift+E: End current session (_hotkey_end_session)
        - Ctrl+Shift+W: Show/hide main window (_hotkey_toggle_window)

        Key format:
        - Uses pynput canonical key format: "<ctrl>+<shift>+<key>"
        - All keys lowercase, wrapped in angle brackets

        Side effects:
            - Creates hotkey_listener (keyboard.GlobalHotKeys instance)
            - Starts listener thread (managed by pynput, auto-cleanup)
            - Stores listener reference for cleanup in on_closing()

        Note:
            All hotkey handlers use root.after(0, func) for thread-safe tkinter calls.
            Listener stopped in on_closing() via hotkey_listener.stop().
            Hotkeys are optional - app continues if registration fails.
        """
        try:
            # Define hotkey handlers using proper key format
            hotkeys = {
                "<ctrl>+<shift>+s": self._hotkey_start_session,
                "<ctrl>+<shift>+b": self._hotkey_toggle_break,
                "<ctrl>+<shift>+e": self._hotkey_end_session,
                "<ctrl>+<shift>+w": self._hotkey_toggle_window,
            }

            # Start global hotkey listener in a separate thread
            self.hotkey_listener = keyboard.GlobalHotKeys(hotkeys)
            self.hotkey_listener.start()
        except Exception:
            # Hotkeys are optional - continue without them if registration fails
            pass

    def _hotkey_start_session(self):
        """Hotkey handler: Start new session if none active (Ctrl+Shift+S)."""

        def do_start():
            if not self.session_active:
                self.start_session()

        self.root.after(0, do_start)

    def _hotkey_toggle_break(self):
        """Hotkey handler: Toggle break state if session active (Ctrl+Shift+B)."""

        def do_break():
            if self.session_active:
                self.toggle_break()

        self.root.after(0, do_break)

    def _hotkey_end_session(self):
        """Hotkey handler: End session and show completion UI (Ctrl+Shift+E)."""

        def do_end():
            if self.session_active:
                # Show window when ending session
                if not self.window_visible:
                    self.toggle_window()
                self.root.state("zoomed")
                self.end_session()

        self.root.after(0, do_end)

    def _hotkey_toggle_window(self):
        """Hotkey handler: Show/hide main window (Ctrl+Shift+W)."""
        self.root.after(0, self.toggle_window)

    def toggle_window(self, icon=None, item=None):
        """Show or hide main window, updating visibility tracking flag.

        Args:
            icon: Pystray icon instance (unused, required for tray menu callback)
            item: Pystray menu item instance (unused, required for tray menu callback)
        """
        if self.window_visible:
            self.root.withdraw()
            self.window_visible = False
        else:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.window_visible = True

    def tray_start_session(self, icon=None, item=None):
        """Tray menu handler: Start new session via root.after for thread safety."""
        self.root.after(0, self.start_session)

    def tray_toggle_break(self, icon=None, item=None):
        """Tray menu handler: Toggle break state via root.after for thread safety."""
        self.root.after(0, self.toggle_break)

    def tray_end_session(self, icon=None, item=None):
        """Tray menu handler: Show window then end session to display completion frame."""
        # Show window when ending session (completion frame needs to be visible)
        if not self.window_visible:
            self.toggle_window()
        self.root.after(0, self.end_session)

    def tray_open_settings(self, icon=None, item=None):
        """Tray menu handler: Show window then open settings frame."""
        if not self.window_visible:
            self.toggle_window()
        self.root.after(0, self.open_settings)

    def tray_open_analysis(self, icon=None, item=None):
        """Tray menu handler: Show window then open analysis frame."""
        if not self.window_visible:
            self.toggle_window()
        self.root.after(0, self.open_analysis)

    def tray_quit(self, icon=None, item=None):
        """Tray menu handler: Quit application via root.after for clean shutdown."""
        self.root.after(0, self.on_closing)

    def on_closing(self):
        """Cleanup and shutdown handler for application exit.

        Called when user closes main window (X button) or quits from tray menu.
        Ensures proper cleanup of all resources before app termination.

        Cleanup sequence:
        1. Disable all ScrollableFrame mouse handlers (set _is_alive = False)
           - main_frame_container
           - analysis_frame.scrollable_container
           - session_view_container

        2. Check for active session:
           - If active: Show "Quit?" confirmation dialog
           - If confirmed: Call end_session() to save work
           - If cancelled: Abort shutdown, return to app

        3. Stop all background threads/listeners:
           - Stop input monitoring (pynput mouse/keyboard listeners)
           - Stop hotkey listener (global keyboard shortcuts)
           - Stop tray icon (system tray menu)

        4. Exit tkinter:
           - Call root.quit() to exit mainloop
           - Call root.destroy() to destroy all widgets

        Dialog behavior:
        - Active session: Shows askokcancel confirmation
        - No session: Quits immediately without prompt

        Side effects:
            - Disables all ScrollableFrame instances (_is_alive = False)
            - May call end_session() if user confirms
            - Stops input_monitoring via stop_input_monitoring()
            - Stops hotkey_listener via hotkey_listener.stop()
            - Stops tray_icon via tray_icon.stop()
            - Calls root.quit() and root.destroy()

        Note:
            Critical to call root.quit() BEFORE root.destroy() to properly
            exit mainloop and prevent tkinter errors.
        """
        # Disable all ScrollableFrame handlers before destroying
        if hasattr(self, "main_frame_container") and self.main_frame_container:
            self.main_frame_container._is_alive = False
        if hasattr(self, "analysis_frame") and self.analysis_frame:
            if hasattr(self.analysis_frame, "scrollable_container"):
                self.analysis_frame.scrollable_container._is_alive = False
        if hasattr(self, "session_view_container") and self.session_view_container:
            self.session_view_container._is_alive = False

        if self.session_active:
            if messagebox.askokcancel(
                "Quit", "A session is active. Do you want to end it and quit?"
            ):
                self.end_session()
                self.stop_input_monitoring()
                if self.hotkey_listener:
                    self.hotkey_listener.stop()
                if self.tray_icon:
                    self.tray_icon.stop()
                self.root.quit()
                self.root.destroy()
        else:
            self.stop_input_monitoring()
            if self.hotkey_listener:
                self.hotkey_listener.stop()
            if self.tray_icon:
                self.tray_icon.stop()
            self.root.quit()
            self.root.destroy()


def main():
    root = tk.Tk()
    app = TimeTracker(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
