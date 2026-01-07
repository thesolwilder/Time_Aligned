"""
Completion Frame - Displayed when a session ends.
Allows user to tag actions for active time, breaks, and idle periods.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime


class CompletionFrame(ttk.Frame):
    def __init__(self, parent, tracker, session_data):
        """
        Initialize the completion frame.

        Args:
            parent: The parent widget (root window)
            tracker: Reference to TimeTracker instance
            session_data: Dict with session_name, total_elapsed, active_time, break_time
        """
        super().__init__(parent, padding="10")
        self.tracker = tracker
        self.session_data = session_data
        self.session_name = session_data["session_name"]

        self.create_widgets()

    def create_widgets(self):
        """Create all UI elements for the completion frame"""
        # Title
        ttk.Label(self, text="Session Complete", font=("Arial", 16, "bold")).grid(
            row=0, column=0, columnspan=2, pady=10
        )

        # Display durations
        self._create_duration_display()

        # Separator
        ttk.Separator(self, orient="horizontal").grid(
            row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15
        )

        # Timeline of all periods
        self._create_timeline()

        # Separator
        ttk.Separator(self, orient="horizontal").grid(
            row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15
        )

        # Action tags section
        self._create_action_tags()

        # Buttons
        self._create_buttons()

    def _create_duration_display(self):
        """Create the duration display section"""
        total_elapsed = self.session_data["total_elapsed"]
        active_time = self.session_data["active_time"]
        break_time = self.session_data["break_time"]

        # Total time
        ttk.Label(self, text="Total Time:", font=("Arial", 12, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        ttk.Label(
            self, text=self.tracker.format_time(total_elapsed), font=("Arial", 12)
        ).grid(row=1, column=1, sticky=tk.W, pady=5)

        # Active time
        ttk.Label(self, text="Active Time:", font=("Arial", 12, "bold")).grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        ttk.Label(
            self, text=self.tracker.format_time(active_time), font=("Arial", 12)
        ).grid(row=2, column=1, sticky=tk.W, pady=5)

        # Break time
        ttk.Label(self, text="Break Time:", font=("Arial", 12, "bold")).grid(
            row=3, column=0, sticky=tk.W, pady=5
        )
        ttk.Label(
            self, text=self.tracker.format_time(break_time), font=("Arial", 12)
        ).grid(row=3, column=1, sticky=tk.W, pady=5)

        # Calculate and display idle time
        total_idle = self._calculate_total_idle()
        ttk.Label(self, text="Idle Time:", font=("Arial", 12, "bold")).grid(
            row=4, column=0, sticky=tk.W, pady=5
        )
        ttk.Label(
            self, text=self.tracker.format_time(total_idle), font=("Arial", 12)
        ).grid(row=4, column=1, sticky=tk.W, pady=5)

    def _calculate_total_idle(self):
        """Calculate total idle time from session data"""
        total_idle = 0
        all_data = self.tracker.load_data()

        if self.session_name in all_data:
            for idle_period in all_data[self.session_name]["idle_periods"]:
                if "duration" in idle_period:
                    total_idle += idle_period["duration"]

        return total_idle

    def _create_timeline(self):
        """Create chronological timeline of all active/break/idle periods"""
        # Container for timeline section
        timeline_container = ttk.Frame(self)
        timeline_container.grid(
            row=6, column=0, columnspan=2, pady=(5, 0), sticky=(tk.W, tk.E)
        )

        # Title
        ttk.Label(
            timeline_container, text="Session Timeline", font=("Arial", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        # Build master list of all periods
        all_periods = []
        all_data = self.tracker.load_data()

        if self.session_name in all_data:
            session = all_data[self.session_name]

            # Add active periods
            for period in session.get("active", []):
                all_periods.append(
                    {
                        "type": "Active",
                        "start": period.get("start", ""),
                        "start_timestamp": period.get("start_timestamp", 0),
                        "duration": period.get("duration", 0),
                    }
                )

            # Add breaks
            for period in session.get("breaks", []):
                all_periods.append(
                    {
                        "type": "Break",
                        "start": period.get("start", ""),
                        "start_timestamp": period.get("start_timestamp", 0),
                        "duration": period.get("duration", 0),
                    }
                )

            # Add idle periods
            for period in session.get("idle_periods", []):
                all_periods.append(
                    {
                        "type": "Idle",
                        "start": period.get("start", ""),
                        "start_timestamp": period.get("start_timestamp", 0),
                        "duration": period.get("duration", 0),
                    }
                )

        # Sort by start timestamp
        all_periods.sort(key=lambda x: x["start_timestamp"])

        # Display timeline directly in frame
        periods_frame = ttk.Frame(timeline_container)
        periods_frame.pack(fill="both", expand=True)

        for idx, period in enumerate(all_periods):
            # Period type with color coding
            type_label = ttk.Label(
                periods_frame,
                text=period["type"],
                font=("Arial", 10, "bold"),
                width=10,
            )
            type_label.grid(row=idx, column=0, sticky=tk.W, padx=5, pady=2)

            # Start time
            ttk.Label(periods_frame, text=period["start"], font=("Arial", 10)).grid(
                row=idx, column=1, sticky=tk.W, padx=5, pady=2
            )

            # Duration
            ttk.Label(
                periods_frame,
                text=self.tracker.format_time(period["duration"]),
                font=("Arial", 10),
            ).grid(row=idx, column=2, sticky=tk.W, padx=5, pady=2)

    def _create_action_tags(self):
        """Create the action tags input section"""
        ttk.Label(
            self, text="Label Your Session Actions", font=("Arial", 12, "bold")
        ).grid(row=8, column=0, columnspan=2, pady=10)

        # Active work action
        ttk.Label(self, text="Active Work Action:", font=("Arial", 10)).grid(
            row=9, column=0, sticky=tk.W, pady=5
        )
        self.active_action_entry = ttk.Entry(self, width=30)
        self.active_action_entry.grid(row=9, column=1, sticky=tk.W, pady=5)

        # Break action
        ttk.Label(self, text="Break Action:", font=("Arial", 10)).grid(
            row=10, column=0, sticky=tk.W, pady=5
        )
        self.break_action_entry = ttk.Entry(self, width=30)
        self.break_action_entry.grid(row=10, column=1, sticky=tk.W, pady=5)

        # Idle notes
        ttk.Label(self, text="Idle Notes:", font=("Arial", 10)).grid(
            row=11, column=0, sticky=tk.W, pady=5
        )
        self.idle_notes_entry = ttk.Entry(self, width=30)
        self.idle_notes_entry.grid(row=11, column=1, sticky=tk.W, pady=5)

        # Session notes
        ttk.Label(self, text="Session Notes:", font=("Arial", 10)).grid(
            row=12, column=0, sticky=tk.W, pady=5
        )
        self.session_notes_text = tk.Text(self, width=30, height=4, font=("Arial", 10))
        self.session_notes_text.grid(row=12, column=1, sticky=tk.W, pady=5)

    def _create_buttons(self):
        """Create action buttons"""
        button_frame = ttk.Frame(self)
        button_frame.grid(row=13, column=0, columnspan=2, pady=20)

        ttk.Button(
            button_frame, text="Save & Complete", command=self.save_and_close
        ).grid(row=0, column=0, padx=5)

        ttk.Button(button_frame, text="Skip", command=self.skip_and_close).grid(
            row=0, column=1, padx=5
        )

    def save_and_close(self):
        """Save action tags and return to main frame"""
        # Save action tags to session data
        all_data = self.tracker.load_data()

        if self.session_name in all_data:
            all_data[self.session_name]["actions"] = {
                "active_action": self.active_action_entry.get(),
                "break_action": self.break_action_entry.get(),
                "idle_notes": self.idle_notes_entry.get(),
                "session_notes": self.session_notes_text.get("1.0", tk.END).strip(),
            }
            self.tracker.save_data(all_data)

        self.tracker.show_main_frame()

    def skip_and_close(self):
        """Return to main frame without saving"""
        self.tracker.show_main_frame()
