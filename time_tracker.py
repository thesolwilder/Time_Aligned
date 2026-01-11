import tkinter as tk
from tkinter import ttk, messagebox
import time
import os
import json
from datetime import datetime
from pynput import mouse, keyboard

from frames.completion_frame import CompletionFrame


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

        # Frame references
        self.completion_frame = None

        # Create GUI
        self.create_widgets()

        # Start update loop
        self.update_timers()

    def get_settings(self):
        """Load or create settings file"""
        default_settings = {
            "idle_settings": {
                "idle_threshold": 60,  # seconds before considering idle
                "idle_break_threshold": 300,  # seconds of idle before auto-break
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

    def save_data(self, session_data):
        """Save session data to file"""
        try:
            all_data = self.load_data()
            all_data.update(session_data)

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

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Bind mousewheel recursively to all widgets
        def bind_mousewheel(widget):
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
                            last_idle["end_timestamp"] - last_idle["start_timestamp"]
                        )
                        self.save_data(all_data)

        # Start mouse listener
        self.mouse_listener = mouse.Listener(
            on_move=on_activity, on_click=on_activity, on_scroll=on_activity
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

    def end_session(self):
        """End the current session"""
        if not self.session_active:
            return

        # End any active break
        if self.break_active:
            self.toggle_break()

        # Stop input monitoring
        self.stop_input_monitoring()

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
                all_data[self.session_name]["active"].append(
                    {
                        "start": datetime.fromtimestamp(
                            self.active_period_start_time
                        ).strftime("%H:%M:%S"),
                        "start_timestamp": self.active_period_start_time,
                        "end": datetime.fromtimestamp(self.break_start_time).strftime(
                            "%H:%M:%S"
                        ),
                        "end_timestamp": self.break_start_time,
                        "duration": self.break_start_time
                        - self.active_period_start_time,
                    }
                )
                self.save_data(all_data)
        else:
            # End break
            break_duration = time.time() - self.break_start_time

            # Save break data
            all_data = self.load_data()
            if self.session_name in all_data:
                all_data[self.session_name]["breaks"].append(
                    {
                        "start": datetime.fromtimestamp(self.break_start_time).strftime(
                            "%H:%M:%S"
                        ),
                        "start_timestamp": self.break_start_time,
                        "end": datetime.now().strftime("%H:%M:%S"),
                        "end_timestamp": time.time(),
                        "duration": break_duration,
                    }
                )
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

        # Create completion frame with session data
        session_data = {
            "session_name": self.session_name,
            "total_elapsed": total_elapsed,
            "active_time": active_time,
            "break_time": break_time,
            "session_start_timestamp": original_start,
            "session_end_timestamp": end_time,
        }
        self.completion_frame = CompletionFrame(canvas, self, session_data)

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
            widget.bind("<MouseWheel>", on_mousewheel)
            for child in widget.winfo_children():
                bind_mousewheel(child)

        bind_mousewheel(completion_container)
        bind_mousewheel(self.completion_frame)

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
            self.backup_loop_count = 0
        self.backup_loop_count += 1

        # Schedule next update
        self.root.after(self.update_timer_interval, self.update_timers)

    def on_closing(self):
        """Clean up before closing"""
        if self.session_active:
            if messagebox.askokcancel(
                "Quit", "A session is active. Do you want to end it and quit?"
            ):
                self.end_session()
                self.stop_input_monitoring()
                self.root.destroy()
        else:
            self.stop_input_monitoring()
            self.root.destroy()


def main():
    root = tk.Tk()
    app = TimeTracker(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
