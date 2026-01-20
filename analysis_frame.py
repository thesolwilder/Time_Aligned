import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
from datetime import datetime, timedelta
import random


class AnalysisFrame(ttk.Frame):
    def __init__(self, parent, tracker, root):
        """
        Initialize the analysis frame

        Args:
            parent: Parent window/frame
            tracker: TimeTracker instance to access methods and settings
            root: Main root window
        """
        super().__init__(parent)
        self.tracker = tracker
        self.root = root

        # Date range options
        self.date_ranges = [
            "Last 7 Days",
            "Last 14 Days",
            "Last 30 Days",
            "This Week",
            "Last Week",
            "This Month",
            "Last Month",
            "All Time",
        ]

        # Default card ranges (saved in settings)
        self.card_ranges = self.load_card_ranges()

        # Currently selected card for timeline
        self.selected_card = 0

        self.create_widgets()

    def load_card_ranges(self):
        """Load saved card range preferences from settings"""
        analysis_settings = self.tracker.settings.get("analysis_settings", {})
        return analysis_settings.get(
            "card_ranges", ["Last 7 Days", "Last 30 Days", "All Time"]
        )

    def save_card_ranges(self):
        """Save card range preferences to settings"""
        if "analysis_settings" not in self.tracker.settings:
            self.tracker.settings["analysis_settings"] = {}

        self.tracker.settings["analysis_settings"]["card_ranges"] = self.card_ranges

        try:
            with open(self.tracker.settings_file, "w") as f:
                json.dump(self.tracker.settings, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def create_widgets(self):
        """Create all UI elements for the analysis frame"""
        # Back button and CSV export
        header_frame = ttk.Frame(self)
        header_frame.grid(
            row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10, padx=10
        )

        ttk.Button(
            header_frame, text="Back to Tracker", command=self.tracker.close_analysis
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            header_frame, text="Session View", command=self.open_latest_session
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            header_frame, text="Generate Dummy Data", command=self.generate_dummy_data
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(header_frame, text="Export to CSV", command=self.export_to_csv).pack(
            side=tk.RIGHT, padx=5
        )

        # Filters
        filter_frame = ttk.Frame(self)
        filter_frame.grid(
            row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10, padx=10
        )

        ttk.Label(filter_frame, text="Sphere:").pack(side=tk.LEFT, padx=5)

        self.sphere_var = tk.StringVar(value="All Spheres")
        spheres = ["All Spheres"] + list(
            self.tracker.settings.get("spheres", {}).keys()
        )
        self.sphere_filter = ttk.Combobox(
            filter_frame,
            textvariable=self.sphere_var,
            values=spheres,
            state="readonly",
            width=15,
        )
        self.sphere_filter.pack(side=tk.LEFT, padx=5)
        self.sphere_filter.bind("<<ComboboxSelected>>", self.on_filter_changed)

        ttk.Label(filter_frame, text="Project:").pack(side=tk.LEFT, padx=5)

        self.project_var = tk.StringVar(value="All Projects")
        self.project_filter = ttk.Combobox(
            filter_frame, textvariable=self.project_var, state="readonly", width=15
        )
        self.project_filter.pack(side=tk.LEFT, padx=5)
        self.project_filter.bind("<<ComboboxSelected>>", self.on_filter_changed)
        self.update_project_filter()

        # Three cards
        cards_frame = ttk.Frame(self)
        cards_frame.grid(
            row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10, padx=10
        )

        self.cards = []
        for i in range(3):
            card = self.create_card(cards_frame, i)
            card.grid(row=0, column=i, padx=10, sticky=(tk.N, tk.S, tk.W, tk.E))
            self.cards.append(card)

        # Configure column weights for equal spacing
        for i in range(3):
            cards_frame.columnconfigure(i, weight=1)

        # Timeline section
        timeline_label_frame = ttk.Frame(self)
        timeline_label_frame.grid(
            row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10, padx=10
        )

        self.timeline_title = ttk.Label(
            timeline_label_frame,
            text=f"Timeline: {self.card_ranges[0]}",
            font=("Arial", 12, "bold"),
        )
        self.timeline_title.pack(side=tk.LEFT)

        # Timeline with scrollbar
        timeline_container = ttk.Frame(self)
        timeline_container.grid(
            row=4,
            column=0,
            columnspan=3,
            sticky=(tk.N, tk.S, tk.W, tk.E),
            padx=10,
            pady=5,
        )

        # Create canvas and scrollbar for timeline
        timeline_canvas = tk.Canvas(timeline_container, height=400)
        timeline_scrollbar = ttk.Scrollbar(
            timeline_container, orient="vertical", command=timeline_canvas.yview
        )

        self.timeline_frame = ttk.Frame(timeline_canvas)

        timeline_canvas.configure(yscrollcommand=timeline_scrollbar.set)
        timeline_canvas_window = timeline_canvas.create_window(
            (0, 0), window=self.timeline_frame, anchor="nw"
        )

        def on_timeline_configure(event):
            timeline_canvas.configure(scrollregion=timeline_canvas.bbox("all"))
            timeline_canvas.itemconfig(timeline_canvas_window, width=event.width)

        self.timeline_frame.bind("<Configure>", on_timeline_configure)
        timeline_canvas.bind("<Configure>", on_timeline_configure)

        # Add mousewheel scrolling to timeline
        def on_timeline_mousewheel(event):
            timeline_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        timeline_canvas.bind("<MouseWheel>", on_timeline_mousewheel)
        self.timeline_frame.bind("<MouseWheel>", on_timeline_mousewheel)

        timeline_canvas.pack(side="left", fill="both", expand=True)
        timeline_scrollbar.pack(side="right", fill="y")

        # Store reference for later use
        self.timeline_canvas = timeline_canvas

        # Configure grid weights
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(4, weight=1)
        # Load initial data
        self.refresh_all()

    def create_card(self, parent, index):
        """Create a single analysis card"""
        card_frame = ttk.LabelFrame(parent, relief=tk.RIDGE, borderwidth=2, padding=10)

        # Date range dropdown
        range_var = tk.StringVar(value=self.card_ranges[index])
        range_dropdown = ttk.Combobox(
            card_frame,
            textvariable=range_var,
            values=self.date_ranges,
            state="readonly",
            width=15,
        )
        range_dropdown.grid(row=0, column=0, pady=5)
        range_dropdown.bind(
            "<<ComboboxSelected>>",
            lambda e, idx=index: self.on_range_changed(idx, range_var.get()),
        )

        # Active time label
        active_label = ttk.Label(card_frame, text="Active: --", font=("Arial", 14))
        active_label.grid(row=1, column=0, pady=5)

        # Break time label
        break_label = ttk.Label(card_frame, text="Break: --", font=("Arial", 14))
        break_label.grid(row=2, column=0, pady=5)

        # Select button
        select_btn = ttk.Button(
            card_frame,
            text="Show Timeline",
            command=lambda idx=index: self.select_card(idx),
        )
        select_btn.grid(row=3, column=0, pady=10)

        # Store references
        card_frame.range_var = range_var
        card_frame.active_label = active_label
        card_frame.break_label = break_label
        card_frame.select_btn = select_btn

        return card_frame

    def on_range_changed(self, card_index, new_range):
        """Handle when a card's date range changes"""
        self.card_ranges[card_index] = new_range
        self.save_card_ranges()
        self.update_card(card_index)

        # If this is the selected card, update timeline
        if card_index == self.selected_card:
            self.update_timeline()

    def select_card(self, card_index):
        """Select a card and show its timeline"""
        self.selected_card = card_index
        self.update_timeline()
        self.timeline_title.config(text=f"Timeline: {self.card_ranges[card_index]}")

    def update_project_filter(self):
        """Update project filter based on selected sphere"""
        sphere = self.sphere_var.get()
        projects = ["All Projects"]

        if sphere == "All Spheres":
            # Disable project filter - all spheres always shows all projects
            self.project_filter.config(state="disabled")
            self.project_var.set("All Projects")
        else:
            # Get projects for selected sphere
            self.project_filter.config(state="readonly")
            for proj, data in self.tracker.settings.get("projects", {}).items():
                if data.get("sphere") == sphere and data.get("active", True):
                    projects.append(proj)

            self.project_filter["values"] = projects
            self.project_var.set("All Projects")

    def on_filter_changed(self, event=None):
        """Handle when filters change"""
        if event and event.widget == self.sphere_filter:
            self.update_project_filter()

        self.refresh_all()

    def refresh_all(self):
        """Refresh all cards and timeline"""
        for i in range(3):
            self.update_card(i)
        self.update_timeline()

    def get_date_range(self, range_name):
        """Get start and end dates for a given range name"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if range_name == "Last 7 Days":
            start = today - timedelta(days=6)
            end = today + timedelta(days=1)
        elif range_name == "Last 14 Days":
            start = today - timedelta(days=13)
            end = today + timedelta(days=1)
        elif range_name == "Last 30 Days":
            start = today - timedelta(days=29)
            end = today + timedelta(days=1)
        elif range_name == "This Week":
            # Monday to Sunday
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=7)
        elif range_name == "Last Week":
            start = today - timedelta(days=today.weekday() + 7)
            end = start + timedelta(days=7)
        elif range_name == "This Month":
            start = today.replace(day=1)
            end = (start + timedelta(days=32)).replace(day=1)
        elif range_name == "Last Month":
            end = today.replace(day=1)
            start = (end - timedelta(days=1)).replace(day=1)
        else:  # All Time
            start = datetime(2000, 1, 1)
            end = datetime(2100, 1, 1)

        return start, end

    def calculate_totals(self, range_name):
        """Calculate total active and break time for a date range"""
        start_date, end_date = self.get_date_range(range_name)
        all_data = self.tracker.load_data()

        total_active = 0
        total_break = 0

        sphere_filter = self.sphere_var.get()
        project_filter = self.project_var.get()

        for session_name, session_data in all_data.items():
            # Check if session is in date range
            session_date = datetime.strptime(
                session_data.get("date", "2000-01-01"), "%Y-%m-%d"
            )
            if not (start_date <= session_date < end_date):
                continue

            # Check sphere filter
            session_sphere = session_data.get("sphere", "")
            if sphere_filter != "All Spheres" and session_sphere != sphere_filter:
                continue

            # Calculate active time
            for period in session_data.get("active", []):
                # Check project filter
                if project_filter != "All Projects":
                    period_project = period.get("project", "")
                    if period_project != project_filter:
                        # Check if it's in projects list (for multi-project periods)
                        found = False
                        for proj in period.get("projects", []):
                            if proj.get("name") == project_filter:
                                found = True
                                break
                        if not found:
                            continue

                total_active += period.get("duration", 0)

            # Calculate break time
            for period in session_data.get("breaks", []):
                total_break += period.get("duration", 0)

            # Calculate idle time
            for period in session_data.get("idle_periods", []):
                if period.get("end_timestamp"):
                    total_break += period.get("duration", 0)

        return total_active, total_break

    def format_duration(self, seconds):
        """Format seconds as Xh Ym"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

    def format_time_12hr(self, time_str):
        """Convert 24hr time to 12hr format"""
        try:
            time_obj = datetime.strptime(time_str, "%H:%M:%S")
            return time_obj.strftime("%I:%M %p")
        except:
            return time_str

    def update_card(self, card_index):
        """Update a single card's data"""
        card = self.cards[card_index]
        range_name = self.card_ranges[card_index]

        active_time, break_time = self.calculate_totals(range_name)

        card.active_label.config(text=f"Active: {self.format_duration(active_time)}")
        card.break_label.config(text=f"Break: {self.format_duration(break_time)}")

    def update_timeline(self):
        """Update the timeline display"""
        # Clear existing timeline
        for widget in self.timeline_frame.winfo_children():
            widget.destroy()

        # Get data for selected card's range
        range_name = self.card_ranges[self.selected_card]
        start_date, end_date = self.get_date_range(range_name)
        all_data = self.tracker.load_data()

        sphere_filter = self.sphere_var.get()
        project_filter = self.project_var.get()

        # Collect all periods
        periods = []

        for session_name, session_data in all_data.items():
            # Check if session is in date range
            session_date = datetime.strptime(
                session_data.get("date", "2000-01-01"), "%Y-%m-%d"
            )
            if not (start_date <= session_date < end_date):
                continue

            # Check sphere filter
            session_sphere = session_data.get("sphere", "")
            if sphere_filter != "All Spheres" and session_sphere != sphere_filter:
                continue

            # Add active periods
            for period in session_data.get("active", []):
                # Check project filter
                project_name = period.get("project", "")
                if project_filter != "All Projects" and project_name != project_filter:
                    # Check multi-project
                    found = False
                    for proj in period.get("projects", []):
                        if proj.get("name") == project_filter:
                            project_name = proj.get("name")
                            found = True
                            break
                    if not found:
                        continue

                periods.append(
                    {
                        "date": session_data.get("date"),
                        "type": "Active",
                        "sphere": session_sphere,
                        "project": project_name,
                        "start": period.get("start", ""),
                        "duration": period.get("duration", 0),
                        "comment": period.get("comment", ""),
                    }
                )

            # Add break periods
            for period in session_data.get("breaks", []):
                periods.append(
                    {
                        "date": session_data.get("date"),
                        "type": "Break",
                        "sphere": session_sphere,
                        "action": period.get("action", "Break"),
                        "start": period.get("start", ""),
                        "duration": period.get("duration", 0),
                        "comment": period.get("comment", ""),
                    }
                )

            # Add idle periods
            for period in session_data.get("idle_periods", []):
                if period.get("end_timestamp"):
                    periods.append(
                        {
                            "date": session_data.get("date"),
                            "type": "Idle",
                            "sphere": session_sphere,
                            "action": period.get("action", "Idle"),
                            "start": period.get("start", ""),
                            "duration": period.get("duration", 0),
                            "comment": period.get("comment", ""),
                        }
                    )

        # Sort by date and start time (or by selected column)
        if not hasattr(self, "timeline_sort_column"):
            self.timeline_sort_column = "date"
            self.timeline_sort_reverse = True

        # Sort by current column
        sort_key_map = {
            "date": lambda x: (x["date"], x["start"]),
            "type": lambda x: x["type"],
            "sphere": lambda x: x["sphere"],
            "project": lambda x: x.get("project") or x.get("action", ""),
            "start": lambda x: x["start"],
            "duration": lambda x: x["duration"],
        }
        periods.sort(
            key=sort_key_map.get(self.timeline_sort_column, sort_key_map["date"]),
            reverse=self.timeline_sort_reverse,
        )

        # Limit to 100 entries
        periods = periods[:100]

        # Create header with proper frame layout for alignment
        header_frame = tk.Frame(
            self.timeline_frame, relief=tk.RIDGE, borderwidth=1, bg="#d0d0d0"
        )
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)

        def create_header_label(text, column_key, width):
            """Create clickable header label for sorting"""
            label = tk.Label(
                header_frame,
                text=(
                    text + " ▼"
                    if self.timeline_sort_column == column_key
                    and self.timeline_sort_reverse
                    else (
                        text + " ▲" if self.timeline_sort_column == column_key else text
                    )
                ),
                font=("Arial", 9, "bold"),
                width=width,
                anchor="w",
                padx=5,
                bg="#d0d0d0",
                cursor="hand2",
            )
            label.bind("<Button-1>", lambda e: self.sort_timeline(column_key))
            return label

        create_header_label("Date", "date", 12).pack(side=tk.LEFT)
        create_header_label("Type", "type", 8).pack(side=tk.LEFT)
        create_header_label("Sphere", "sphere", 12).pack(side=tk.LEFT)
        create_header_label("Project/Action", "project", 18).pack(side=tk.LEFT)
        create_header_label("Start", "start", 10).pack(side=tk.LEFT)
        create_header_label("Duration", "duration", 10).pack(side=tk.LEFT)
        tk.Label(
            header_frame,
            text="Comment",
            font=("Arial", 9, "bold"),
            width=35,
            anchor="w",
            padx=5,
            bg="#d0d0d0",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Create timeline entries with color coding
        for idx, period in enumerate(periods):
            # Color code based on type
            if period["type"] == "Active":
                bg_color = "#e8f5e9"  # Light green
            else:  # Break or Idle
                bg_color = "#fff3e0"  # Light orange

            row_frame = tk.Frame(self.timeline_frame, bg=bg_color)
            row_frame.grid(row=idx + 1, column=0, sticky=(tk.W, tk.E), pady=1)

            tk.Label(
                row_frame,
                text=period["date"],
                width=12,
                anchor="w",
                padx=5,
                bg=bg_color,
            ).pack(side=tk.LEFT)
            tk.Label(
                row_frame, text=period["type"], width=8, anchor="w", padx=5, bg=bg_color
            ).pack(side=tk.LEFT)
            tk.Label(
                row_frame,
                text=period["sphere"],
                width=12,
                anchor="w",
                padx=5,
                bg=bg_color,
            ).pack(side=tk.LEFT)

            proj_action = period.get("project") or period.get("action", "")
            tk.Label(
                row_frame, text=proj_action, width=18, anchor="w", padx=5, bg=bg_color
            ).pack(side=tk.LEFT)
            tk.Label(
                row_frame,
                text=self.format_time_12hr(period["start"]),
                width=10,
                anchor="w",
                padx=5,
                bg=bg_color,
            ).pack(side=tk.LEFT)
            tk.Label(
                row_frame,
                text=self.format_duration(period["duration"]),
                width=10,
                anchor="w",
                padx=5,
                bg=bg_color,
            ).pack(side=tk.LEFT)
            tk.Label(
                row_frame,
                text=period["comment"][:35],
                width=35,
                anchor="w",
                padx=5,
                bg=bg_color,
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        if not periods:
            ttk.Label(
                self.timeline_frame,
                text="No data for selected filters",
                font=("Arial", 12),
            ).grid(row=1, column=0, pady=20)

    def sort_timeline(self, column):
        """Sort timeline by column"""
        if self.timeline_sort_column == column:
            self.timeline_sort_reverse = not self.timeline_sort_reverse
        else:
            self.timeline_sort_column = column
            self.timeline_sort_reverse = False
        self.update_timeline()

    def export_to_csv(self):
        """Export timeline data to CSV"""
        # Get data for selected card's range
        range_name = self.card_ranges[self.selected_card]
        start_date, end_date = self.get_date_range(range_name)
        all_data = self.tracker.load_data()

        sphere_filter = self.sphere_var.get()
        project_filter = self.project_var.get()

        # Collect all periods
        periods = []

        for session_name, session_data in all_data.items():
            session_date = datetime.strptime(
                session_data.get("date", "2000-01-01"), "%Y-%m-%d"
            )
            if not (start_date <= session_date < end_date):
                continue

            session_sphere = session_data.get("sphere", "")
            if sphere_filter != "All Spheres" and session_sphere != sphere_filter:
                continue

            for period in session_data.get("active", []):
                project_name = period.get("project", "")
                if project_filter != "All Projects" and project_name != project_filter:
                    continue

                periods.append(
                    {
                        "Date": session_data.get("date"),
                        "Type": "Active",
                        "Sphere": session_sphere,
                        "Project/Action": project_name,
                        "Start Time": period.get("start", ""),
                        "Duration (seconds)": period.get("duration", 0),
                        "Duration": self.format_duration(period.get("duration", 0)),
                        "Comment": period.get("comment", ""),
                    }
                )

            for period in session_data.get("breaks", []):
                periods.append(
                    {
                        "Date": session_data.get("date"),
                        "Type": "Break",
                        "Sphere": session_sphere,
                        "Project/Action": period.get("action", "Break"),
                        "Start Time": period.get("start", ""),
                        "Duration (seconds)": period.get("duration", 0),
                        "Duration": self.format_duration(period.get("duration", 0)),
                        "Comment": period.get("comment", ""),
                    }
                )

        if not periods:
            messagebox.showinfo("No Data", "No data to export for selected filters")
            return

        # Ask user for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"time_tracker_{range_name.replace(' ', '_')}.csv",
        )

        if not filename:
            return

        try:
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = [
                    "Date",
                    "Type",
                    "Sphere",
                    "Project/Action",
                    "Start Time",
                    "Duration (seconds)",
                    "Duration",
                    "Comment",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for period in periods:
                    writer.writerow(period)

            messagebox.showinfo(
                "Success", f"Exported {len(periods)} entries to {filename}"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {e}")

    def open_latest_session(self):
        """Open completion frame with the most recent session"""
        all_data = self.tracker.load_data()

        if not all_data:
            messagebox.showinfo("No Data", "No sessions found")
            return

        # Get most recent session
        sessions = sorted(all_data.keys(), reverse=True)
        latest_session = sessions[0]
        session_data = all_data[latest_session]

        # Set up session data in tracker
        self.tracker.session_name = latest_session
        self.tracker.current_session = session_data

        # Close analysis frame
        self.tracker.close_analysis()

        # Open completion frame with latest session
        self.tracker.show_completion_screen(
            session_data.get("total_duration", 0),
            session_data.get("active_duration", 0),
            session_data.get("break_duration", 0),
            session_data.get("start_timestamp", 0),
            session_data.get("end_timestamp", 0),
        )

    def generate_dummy_data(self):
        """Generate two months of dummy data for testing"""
        all_data = self.tracker.load_data()

        # Get spheres and projects from settings
        spheres = list(self.tracker.settings.get("spheres", {}).keys())
        projects_by_sphere = {}
        for proj, data in self.tracker.settings.get("projects", {}).items():
            sphere = data.get("sphere", "General")
            if sphere not in projects_by_sphere:
                projects_by_sphere[sphere] = []
            projects_by_sphere[sphere].append(proj)

        break_actions = list(self.tracker.settings.get("break_actions", {}).keys())

        if not spheres:
            spheres = ["General"]
        if not break_actions:
            break_actions = ["Resting"]

        # Generate data for last 60 days
        today = datetime.now()
        for days_ago in range(60):
            current_date = today - timedelta(days=days_ago)
            date_str = current_date.strftime("%Y-%m-%d")

            # Generate 1-3 sessions per day
            num_sessions = random.randint(1, 3)
            for session_num in range(num_sessions):
                # Create session timestamp
                hour = 8 + (session_num * 4) + random.randint(0, 2)
                minute = random.randint(0, 59)
                start_dt = current_date.replace(hour=hour, minute=minute, second=0)
                start_timestamp = start_dt.timestamp()

                session_name = f"{date_str}_{int(start_timestamp)}"

                # Skip if already exists
                if session_name in all_data:
                    continue

                # Pick random sphere
                sphere = random.choice(spheres)
                projects = projects_by_sphere.get(sphere, ["General"])

                # Generate active periods (2-5 periods)
                active_periods = []
                current_time = start_timestamp
                num_active = random.randint(2, 5)

                for _ in range(num_active):
                    period_start = current_time
                    duration = random.randint(600, 3600)  # 10 min to 1 hour
                    period_end = period_start + duration

                    active_periods.append(
                        {
                            "start": datetime.fromtimestamp(period_start).strftime(
                                "%H:%M:%S"
                            ),
                            "start_timestamp": period_start,
                            "end": datetime.fromtimestamp(period_end).strftime(
                                "%H:%M:%S"
                            ),
                            "end_timestamp": period_end,
                            "duration": duration,
                            "project": random.choice(projects),
                            "comment": f"Work session {_ + 1}",
                        }
                    )

                    current_time = period_end

                # Generate break periods (1-3 breaks)
                breaks = []
                num_breaks = random.randint(1, 3)
                break_time = start_timestamp + 1800  # Start breaks after 30 min

                for _ in range(num_breaks):
                    duration = random.randint(300, 900)  # 5-15 min
                    breaks.append(
                        {
                            "start": datetime.fromtimestamp(break_time).strftime(
                                "%H:%M:%S"
                            ),
                            "start_timestamp": break_time,
                            "duration": duration,
                            "action": random.choice(break_actions),
                            "comment": "",
                        }
                    )
                    break_time += duration + random.randint(1800, 3600)

                # Calculate totals
                total_active = sum(p["duration"] for p in active_periods)
                total_break = sum(b["duration"] for b in breaks)
                end_timestamp = current_time

                all_data[session_name] = {
                    "sphere": sphere,
                    "date": date_str,
                    "start_time": datetime.fromtimestamp(start_timestamp).strftime(
                        "%H:%M:%S"
                    ),
                    "start_timestamp": start_timestamp,
                    "breaks": breaks,
                    "active": active_periods,
                    "idle_periods": [],
                    "end_time": datetime.fromtimestamp(end_timestamp).strftime(
                        "%H:%M:%S"
                    ),
                    "end_timestamp": end_timestamp,
                    "total_duration": end_timestamp - start_timestamp,
                    "active_duration": total_active,
                    "break_duration": total_break,
                }

        # Save the data
        try:
            with open(self.tracker.data_file, "w") as f:
                json.dump(all_data, f, indent=2)
            messagebox.showinfo("Success", "Generated 2 months of dummy data!")
            self.refresh_all()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save dummy data: {e}")
