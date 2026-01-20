import tkinter as tk
from tkinter import ttk, messagebox
import time
import os
import json
from datetime import datetime
import warnings
import logging
import sys
import threading
from PIL import Image, ImageDraw
import pystray

# Suppress pynput's harmless Python 3.13 compatibility warnings
logging.getLogger("pynput").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pynput")

# Monkey-patch to suppress pynput exception output in Python 3.13
import traceback

_original_print_exception = traceback.print_exception


def _patched_print_exception(
    exc, /, value=None, tb=None, limit=None, file=None, chain=True
):
    """Suppress pynput listener callback exceptions that are harmless in Python 3.13"""
    if value and isinstance(value, (NotImplementedError, TypeError)):
        exc_str = str(value)
        if "_thread._ThreadHandle" in exc_str or "listener callback" in str(exc):
            return  # Suppress this specific pynput error
    _original_print_exception(exc, value, tb, limit, file, chain)


traceback.print_exception = _patched_print_exception

from pynput import mouse, keyboard

from frames.completion_frame import CompletionFrame
from settings_frame import SettingsFrame
from analysis_frame import AnalysisFrame
from screenshot_capture import ScreenshotCapture


class TimeTracker:
    def __init__(self, root):
        # Initialize main window
        self.root = root
        self.root.title("Time Aligned - Time Tracker")
        self.root.geometry("600x400")

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
        self.update_timer_interval = 100  # in milliseconds
        self.one_minute_ms = 60000  # one minute in milliseconds
        self.backup_frequency = (
            self.one_minute_ms // self.update_timer_interval
        )  # save every minute

        # File paths
        self.settings_file = "settings.json"
        self.data_file = "data.json"

        # Load settings
        self.settings = self.get_settings()

        # Input monitoring
        self.input_listener_running = False
        self.mouse_listener = None
        self.keyboard_listener = None

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
                "idle_threshold": 60,  # seconds before considering idle
                "idle_break_threshold": 300,  # seconds of idle before auto-break
            },
            "screenshot_settings": {
                "enabled": False,  # enable/disable screenshot capture
                "capture_on_focus_change": True,  # capture on window focus change
                "min_seconds_between_captures": 10,  # minimum seconds between captures
                "screenshot_path": "screenshots",  # base path for screenshots
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
        except Exception as e:
            print(f"Failed to read settings file: {e}")
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

    def load_data(self):
        """Load existing session data"""
        if not os.path.exists(self.data_file):
            return {}

        try:
            with open(self.data_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to read data file: {e}")
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
                all_data = session_data

            with open(self.data_file, "w") as f:
                json.dump(all_data, f, indent=2)
        except Exception as e:
            print(f"Failed to save data: {e}")

    def create_widgets(self):
        """Create the main GUI elements"""
        # Create scrollable container for main frame
        main_frame_container = ttk.Frame(self.root)
        main_frame_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create canvas and scrollbar
        canvas = tk.Canvas(main_frame_container)
        scrollbar = ttk.Scrollbar(
            main_frame_container, orient="vertical", command=canvas.yview
        )

        # Main frame inside canvas
        main_frame = ttk.Frame(canvas, padding="10")

        # Configure canvas
        main_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=main_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Update canvas window width when canvas resizes
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel for scrolling (bind to container, not globally)
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        main_frame_container.bind("<MouseWheel>", on_mousewheel)

        # Store reference to main frame container for show/hide
        self.main_frame_container = main_frame_container

        # Session timer
        ttk.Label(main_frame, text="Session Time:", font=("Arial", 12, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=10
        )
        self.session_timer_label = ttk.Label(
            main_frame, text="00:00:00", font=("Arial", 20)
        )
        self.session_timer_label.grid(row=1, column=1, columnspan=2, pady=10)

        # Break timer
        ttk.Label(main_frame, text="Break Time:", font=("Arial", 12, "bold")).grid(
            row=2, column=0, sticky=tk.W, pady=10
        )
        self.break_timer_label = ttk.Label(
            main_frame, text="00:00:00", font=("Arial", 20)
        )
        self.break_timer_label.grid(row=2, column=1, columnspan=2, pady=10)

        # Status label
        self.status_label = ttk.Label(
            main_frame, text="Ready to start", font=("Arial", 10)
        )
        self.status_label.grid(row=3, column=0, columnspan=3, pady=10)

        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)

        self.start_button = ttk.Button(
            button_frame, text="Start Session", command=self.start_session
        )
        self.start_button.grid(row=0, column=0, padx=5)

        self.end_button = ttk.Button(
            button_frame,
            text="End Session",
            command=self.end_session,
            state=tk.DISABLED,
        )
        self.end_button.grid(row=0, column=2, padx=5)

        self.break_button = ttk.Button(
            button_frame,
            text="Start Break",
            command=self.toggle_break,
            state=tk.DISABLED,
        )
        self.break_button.grid(row=0, column=1, padx=5)

        # Settings button
        settings_button = ttk.Button(
            button_frame, text="Settings", command=self.open_settings
        )
        settings_button.grid(row=0, column=3, padx=5)

        # Analysis button
        analysis_button = ttk.Button(
            button_frame, text="Analysis", command=self.open_analysis
        )
        analysis_button.grid(row=0, column=4, padx=5)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Bind mousewheel recursively to all widgets
        def bind_mousewheel(widget):
            # Skip Combobox widgets - they have their own mousewheel handling
            if not isinstance(widget, ttk.Combobox):
                widget.bind("<MouseWheel>", on_mousewheel)
            for child in widget.winfo_children():
                bind_mousewheel(child)

        bind_mousewheel(main_frame_container)
        bind_mousewheel(main_frame)

        # Store references
        self.main_frame = main_frame
        self.main_frame_container = main_frame_container
        self.main_canvas = canvas

    def format_time(self, seconds):
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def start_input_monitoring(self):
        """Start monitoring keyboard and mouse input"""
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
                            self.save_data(all_data)
            except Exception:
                # Suppress harmless pynput Python 3.13 compatibility exceptions
                pass

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
        """Start a new tracking session"""
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

        # Start input monitoring
        self.start_input_monitoring()

        # Start screenshot capture for first active period
        self.screenshot_capture.set_current_session(self.session_name, "active", 0)
        self.screenshot_capture.start_monitoring()

    def end_session(self):
        """End the current session"""
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

        # Show completion frame to label actions
        self.show_completion_frame(
            total_elapsed, active_time, break_time, original_start, end_time
        )

    def toggle_break(self):
        """Start or end a break"""
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

    def show_completion_frame(
        self, total_elapsed, active_time, break_time, original_start, end_time
    ):
        """Show completion frame for labeling session actions"""
        # Hide main frame
        self.main_frame_container.grid_remove()

        # Create scrollable container for completion frame
        completion_container = ttk.Frame(self.root)
        completion_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create canvas and scrollbar
        canvas = tk.Canvas(completion_container)
        scrollbar = ttk.Scrollbar(
            completion_container, orient="vertical", command=canvas.yview
        )

        # Create completion frame with session name
        self.completion_frame = CompletionFrame(canvas, self, self.session_name)

        # Configure canvas
        self.completion_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window(
            (0, 0), window=self.completion_frame, anchor="nw"
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        # Update canvas window width when canvas resizes
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Store container reference
        self.completion_container = completion_container
        self.completion_canvas = canvas

        # Bind mousewheel for scrolling (bind to all widgets recursively)
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def bind_mousewheel(widget):
            # Skip Combobox widgets - they have their own mousewheel handling
            if not isinstance(widget, ttk.Combobox):
                widget.bind("<MouseWheel>", on_mousewheel)
            for child in widget.winfo_children():
                bind_mousewheel(child)

        bind_mousewheel(completion_container)
        bind_mousewheel(self.completion_frame)

        # Store canvas reference and binding function in completion frame
        self.completion_frame.canvas = canvas
        self.completion_frame.bind_mousewheel_func = lambda: bind_mousewheel(
            self.completion_frame
        )

    def show_main_frame(self):
        """Show main timer frame (called from other frames to navigate back)"""
        # Remove completion container
        if hasattr(self, "completion_container") and self.completion_container:
            self.completion_container.grid_remove()
            self.completion_container.destroy()
            self.completion_container = None

        if self.completion_frame:
            self.completion_frame = None

        # Show main frame
        self.main_frame_container.grid()

        # Clear session name
        self.session_name = None

    def check_idle(self):
        """Check if user is idle and update status"""
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
            self.idle_start_time = self.last_user_input
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
        """Update timer displays"""
        # Update tray icon periodically
        self.update_tray_icon()

        if self.session_active and not self.break_active:
            # Calculate active time by subtracting breaks from total elapsed
            total_elapsed = time.time() - self.session_start_time
            self.session_elapsed = total_elapsed - self.total_break_time
            self.session_timer_label.config(text=self.format_time(self.session_elapsed))

            # Check for idle
            self.check_idle()

        if self.break_active:
            self.break_elapsed = time.time() - self.break_start_time
            self.break_timer_label.config(text=self.format_time(self.break_elapsed))
        else:
            self.break_timer_label.config(text="00:00:00")

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
            self.main_frame_container.grid(
                row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S)
            )

            # Restore window title
            self.root.title("Time Aligned - Time Tracker")

    def open_analysis(self):
        """Open the analysis window"""
        # Don't allow opening analysis while tracking time
        if self.session_active:
            messagebox.showwarning(
                "Session Active",
                "Cannot open analysis while tracking time. Please end the session first.",
            )
            return

        if hasattr(self, "analysis_frame") and self.analysis_frame is not None:
            # Analysis already open, do nothing
            return

        # Hide main frame
        self.main_frame_container.grid_forget()

        # Create analysis frame in main window
        self.analysis_frame = AnalysisFrame(self.root, self, self.root)
        self.analysis_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Update window title
        self.root.title("Time Aligned - Analysis")

    def close_analysis(self):
        """Close analysis and return to main view"""
        if hasattr(self, "analysis_frame") and self.analysis_frame is not None:
            # Destroy analysis frame
            self.analysis_frame.destroy()
            self.analysis_frame = None

            # Show main frame again
            self.main_frame_container.grid(
                row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S)
            )

            # Restore window title
            self.root.title("Time Aligned - Time Tracker")

            # Reload settings after closing settings window
            self.settings = self.get_settings()

    def create_tray_icon_image(self, state="idle"):
        """Create icon image for system tray based on state"""
        # Create a simple colored circle icon
        size = 64
        image = Image.new("RGB", (size, size), "white")
        dc = ImageDraw.Draw(image)

        # Color based on state
        colors = {
            "idle": "#808080",  # Gray
            "active": "#4CAF50",  # Green
            "break": "#FFC107",  # Amber/Yellow
            "paused": "#FF9800",  # Orange
        }

        color = colors.get(state, "#808080")

        # Draw circle
        dc.ellipse([8, 8, size - 8, size - 8], fill=color, outline="black", width=2)

        return image

    def setup_tray_icon(self):
        """Setup system tray icon with menu"""

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
        """Update tray icon based on current state"""
        if self.tray_icon is None:
            return

        if self.session_active:
            if self.break_active:
                state = "break"
                title = f"Time Aligned - Break ({self.format_time(int(self.break_elapsed))})"
            else:
                state = "active"
                title = f"Time Aligned - Active ({self.format_time(int(self.session_elapsed))})"
        else:
            state = "idle"
            title = "Time Aligned - Ready"

        self.tray_icon.icon = self.create_tray_icon_image(state)
        self.tray_icon.title = title

    def setup_global_hotkeys(self):
        """Setup global keyboard shortcuts"""
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
            print("Global hotkeys enabled:")
            print("  Ctrl+Shift+S - Start session")
            print("  Ctrl+Shift+B - Toggle break")
            print("  Ctrl+Shift+E - End session")
            print("  Ctrl+Shift+W - Show/hide window")
        except Exception as e:
            print(f"Failed to setup global hotkeys: {e}")
            import traceback

            traceback.print_exc()

    def _hotkey_start_session(self):
        """Start session via hotkey"""

        def do_start():
            if not self.session_active:
                self.start_session()

        self.root.after(0, do_start)

    def _hotkey_toggle_break(self):
        """Toggle break via hotkey"""

        def do_break():
            if self.session_active:
                self.toggle_break()

        self.root.after(0, do_break)

    def _hotkey_end_session(self):
        """End session via hotkey"""

        def do_end():
            if self.session_active:
                # Show window when ending session
                if not self.window_visible:
                    self.toggle_window()
                self.end_session()

        self.root.after(0, do_end)

    def _hotkey_toggle_window(self):
        """Toggle window visibility via hotkey"""
        self.root.after(0, self.toggle_window)

    def toggle_window(self, icon=None, item=None):
        """Toggle main window visibility"""
        if self.window_visible:
            self.root.withdraw()
            self.window_visible = False
        else:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.window_visible = True

    def tray_start_session(self, icon=None, item=None):
        """Start session from tray menu"""
        self.root.after(0, self.start_session)

    def tray_toggle_break(self, icon=None, item=None):
        """Toggle break from tray menu"""
        self.root.after(0, self.toggle_break)

    def tray_end_session(self, icon=None, item=None):
        """End session from tray menu"""
        # Show window when ending session (completion frame needs to be visible)
        if not self.window_visible:
            self.toggle_window()
        self.root.after(0, self.end_session)

    def tray_open_settings(self, icon=None, item=None):
        """Open settings from tray menu"""
        if not self.window_visible:
            self.toggle_window()
        self.root.after(0, self.open_settings)

    def tray_open_analysis(self, icon=None, item=None):
        """Open analysis from tray menu"""
        if not self.window_visible:
            self.toggle_window()
        self.root.after(0, self.open_analysis)

    def tray_quit(self, icon=None, item=None):
        """Quit application from tray menu"""
        self.root.after(0, self.on_closing)

    def on_closing(self):
        """Clean up before closing"""
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
                self.root.destroy()
        else:
            self.stop_input_monitoring()
            if self.hotkey_listener:
                self.hotkey_listener.stop()
            if self.tray_icon:
                self.tray_icon.stop()
            self.root.destroy()


def main():
    root = tk.Tk()
    app = TimeTracker(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
