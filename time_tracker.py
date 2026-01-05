import tkinter as tk
from tkinter import ttk, messagebox
import time
import os
import json
import threading
from datetime import datetime
from pynput import mouse, keyboard


class TimeTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Time Aligned - Time Tracker")
        self.root.geometry("600x400")

        # Session state variables
        self.session_name = None
        self.session_active = False
        self.session_start_time = None
        self.session_elapsed = 0

        self.break_active = False
        self.break_start_time = None
        self.break_elapsed = 0
        self.total_break_time = 0  # Track cumulative break time

        self.session_idle = False
        self.idle_start_time = None
        self.last_user_input = time.time()

        # File paths
        self.settings_file = "settings.json"
        self.data_file = "data.json"

        # Load settings
        self.settings = self.get_settings()

        # Input monitoring
        self.input_listener_running = False
        self.mouse_listener = None
        self.keyboard_listener = None

        # Create GUI
        self.create_widgets()

        # Start update loop
        self.update_timers()

    def get_settings(self):
        """Load or create settings file"""
        default_settings = {
            "idle_threshold": 60,  # seconds before considering idle
            "idle_break_threshold": 300,  # seconds of idle before auto-break
            "default_sphere": "General",
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
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

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
        self.end_button.grid(row=0, column=1, padx=5)

        self.break_button = ttk.Button(
            button_frame,
            text="Start Break",
            command=self.toggle_break,
            state=tk.DISABLED,
        )
        self.break_button.grid(row=0, column=2, padx=5)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

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
                "sphere": settings["default_sphere"] if settings else "General",
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

        # Calculate final time
        end_time = time.time()
        total_elapsed = end_time - self.session_start_time

        # Update session data
        all_data = self.load_data()
        if self.session_name in all_data:
            all_data[self.session_name]["end_time"] = datetime.now().strftime(
                "%H:%M:%S"
            )
            all_data[self.session_name]["end_timestamp"] = end_time
            all_data[self.session_name]["total_duration"] = total_elapsed
            self.save_data(all_data)

        # Reset state
        self.session_active = False
        self.session_start_time = None
        self.session_elapsed = 0
        self.session_name = None

        # Update UI
        self.start_button.config(state=tk.NORMAL)
        self.end_button.config(state=tk.DISABLED)
        self.break_button.config(state=tk.DISABLED)
        self.status_label.config(text="Session ended")

        messagebox.showinfo(
            "Session Ended", f"Total time: {self.format_time(total_elapsed)}"
        )

    def toggle_break(self):
        """Start or end a break"""
        if not self.session_active:
            return

        if not self.break_active:
            # Start break
            self.break_active = True
            self.break_start_time = time.time()
            self.break_elapsed = 0
            self.break_button.config(text="End Break")
            self.status_label.config(text="On break")
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
                        "duration": break_duration,
                    }
                )
                self.save_data(all_data)

            # Adjust session start time to exclude break duration
            self.session_start_time += break_duration
            self.total_break_time += break_duration
            
            # Reset break state
            self.break_active = False
            self.break_start_time = None
            self.break_elapsed = 0
            self.break_button.config(text="Start Break")
            self.status_label.config(text="Session active")

    def check_idle(self):
        """Check if user is idle and update status"""
        if not self.session_active or self.break_active:
            return

        idle_time = time.time() - self.last_user_input

        # Check if newly idle
        if not self.session_idle and idle_time >= self.settings["idle_threshold"]:
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
        elif self.session_idle and idle_time >= self.settings["idle_break_threshold"]:
            if not self.break_active:
                self.toggle_break()

    def update_timers(self):
        """Update timer displays"""
        if self.session_active and not self.break_active:
            self.session_elapsed = time.time() - self.session_start_time
            self.session_timer_label.config(text=self.format_time(self.session_elapsed))

            # Check for idle
            self.check_idle()

        if self.break_active:
            self.break_elapsed = time.time() - self.break_start_time
            self.break_timer_label.config(text=self.format_time(self.break_elapsed))
        else:
            self.break_timer_label.config(text="00:00:00")

        # Schedule next update
        self.root.after(100, self.update_timers)

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
