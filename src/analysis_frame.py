import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
from datetime import datetime, timedelta
import random

from src.ui_helpers import ScrollableFrame


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
            "Today",
            "Yesterday",
            "Last 7 Days",
            "Last 14 Days",
            "Last 30 Days",
            "This Week (Mon-Sun)",
            "Last Week (Mon-Sun)",
            "This Month",
            "Last Month",
            "Custom Date",
            "All Time",
        ]

        # Default card ranges (saved in settings)
        self.card_ranges = self.load_card_ranges()

        # Currently selected card for timeline
        self.selected_card = 0

        # Status filter (active, all, archived) - controls both sphere and project dropdowns
        self.status_filter = tk.StringVar(master=root, value="active")

        # Load More pagination state
        self.periods_per_page = 50  # Load 50 periods at a time
        self.timeline_data_all = []  # Full dataset
        self.periods_loaded = 0  # How many periods currently displayed
        self.load_more_button = None  # Reference to Load More button

        self.create_widgets()

    def load_card_ranges(self):
        """Load saved card range preferences from settings"""
        analysis_settings = self.tracker.settings.get("analysis_settings", {})
        return analysis_settings.get(
            "card_ranges", ["Last 7 Days", "Last 30 Days", "All Time"]
        )

    def get_default_project(self, sphere):
        """Get the default project for a given sphere"""
        result = self.tracker.get_default_project(sphere)
        return result if result else "All Projects"

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
        # Create scrollable container for entire frame
        scrollable_container = ScrollableFrame(
            self, debug_name="AnalysisFrame Scrollable"
        )
        scrollable_container.pack(fill="both", expand=True)

        content_frame = scrollable_container.get_content_frame()

        # Store references
        self.main_canvas = scrollable_container.canvas
        self.content_frame = content_frame
        self.scrollable_container = scrollable_container

        # Back button and CSV export
        header_frame = ttk.Frame(content_frame)
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
        filter_frame = ttk.Frame(content_frame)
        filter_frame.grid(
            row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10, padx=10
        )

        # Sphere label and dropdown
        ttk.Label(filter_frame, text="Sphere:").pack(side=tk.LEFT, padx=5)

        # Get default sphere using tracker's method
        default_sphere = self.tracker._get_default_sphere()

        # Build sphere list based on filter (default is active)
        spheres = self.get_filtered_spheres()

        self.sphere_var = tk.StringVar(master=self.root, value=default_sphere)
        self.sphere_filter = ttk.Combobox(
            filter_frame,
            textvariable=self.sphere_var,
            values=spheres,
            state="readonly",
            width=15,
        )
        self.sphere_filter.pack(side=tk.LEFT, padx=5)
        self.sphere_filter.bind("<<ComboboxSelected>>", self.on_filter_changed)

        # Project label and dropdown
        ttk.Label(filter_frame, text="Project:").pack(side=tk.LEFT, padx=5)

        # Get default project for the default sphere
        self.default_project = self.get_default_project(default_sphere)
        self.project_var = tk.StringVar(master=self.root, value="All Projects")
        self.project_filter = ttk.Combobox(
            filter_frame, textvariable=self.project_var, state="readonly", width=15
        )
        self.project_filter.pack(side=tk.LEFT, padx=5)
        self.project_filter.bind("<<ComboboxSelected>>", self.on_filter_changed)
        self.update_project_filter(set_default=True)

        # Radio buttons for status filter (controls both sphere and project)
        radio_frame = ttk.Frame(filter_frame)
        radio_frame.pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            radio_frame,
            text="Active",
            variable=self.status_filter,
            value="active",
            command=self.refresh_dropdowns,
        ).pack(side=tk.LEFT, padx=2)

        ttk.Radiobutton(
            radio_frame,
            text="All",
            variable=self.status_filter,
            value="all",
            command=self.refresh_dropdowns,
        ).pack(side=tk.LEFT, padx=2)

        ttk.Radiobutton(
            radio_frame,
            text="Archived",
            variable=self.status_filter,
            value="archived",
            command=self.refresh_dropdowns,
        ).pack(side=tk.LEFT, padx=2)

        # Three cards
        cards_frame = ttk.Frame(content_frame)
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
        timeline_label_frame = ttk.Frame(content_frame)
        timeline_label_frame.grid(
            row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10, padx=10
        )

        self.timeline_title = ttk.Label(
            timeline_label_frame,
            text=f"Timeline: {self.card_ranges[0]}",
            font=("Arial", 12, "bold"),
        )
        self.timeline_title.pack(side=tk.LEFT)

        # Timeline header (frozen at top)
        self.timeline_header_frame = tk.Frame(
            content_frame, relief=tk.RIDGE, borderwidth=1, bg="#d0d0d0"
        )
        self.timeline_header_frame.grid(
            row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=10, pady=(5, 2)
        )

        # Headers will be created by update_timeline_header() using grid() layout
        # Do NOT create initial headers with pack() here - it conflicts with grid()

        # Timeline with scrollbar
        timeline_container = ttk.Frame(content_frame)
        timeline_container.grid(
            row=5,
            column=0,
            columnspan=3,
            sticky=(tk.N, tk.S, tk.W, tk.E),
            padx=10,
            pady=(0, 5),
        )

        # Create canvas and scrollbar for timeline
        # Use a simple frame for timeline - no separate scrollbar
        self.timeline_frame = ttk.Frame(timeline_container)
        self.timeline_frame.pack(fill="both", expand=True)

        # Configure grid weights for content_frame
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.columnconfigure(2, weight=1)
        content_frame.rowconfigure(5, weight=1)

        # Disable mousewheel scrolling on all comboboxes
        scrollable_container.rebind_mousewheel()

        # Load initial data
        self.refresh_all()

    def destroy(self):
        """Log when AnalysisFrame is destroyed for debugging."""
        try:
            import traceback

            stack = traceback.extract_stack(limit=8)
            caller = stack[-2] if len(stack) >= 2 else None
            if caller:
                print(
                    f"[ANALYSIS DESTROY] AnalysisFrame destroyed (ID: {id(self)}) "
                    f"called from {caller.filename}:{caller.lineno} in {caller.name}"
                )
            else:
                print(f"[ANALYSIS DESTROY] AnalysisFrame destroyed (ID: {id(self)})")
        except Exception:
            print(f"[ANALYSIS DESTROY] AnalysisFrame destroyed (ID: {id(self)})")

        super().destroy()

    def create_card(self, parent, index):
        """Create a single analysis card"""
        card_frame = ttk.LabelFrame(parent, relief=tk.RIDGE, borderwidth=2, padding=10)

        # Date range dropdown
        range_var = tk.StringVar(master=self.root, value=self.card_ranges[index])
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
        # If "Custom Date" is selected, open date picker dialog
        if new_range == "Custom Date":
            custom_date = self.open_custom_date_dialog()
            if custom_date:
                # Format as "Custom: YYYY-MM-DD"
                new_range = f"Custom: {custom_date}"
            else:
                # User cancelled, revert to previous selection
                if hasattr(self, "cards") and card_index < len(self.cards):
                    self.cards[card_index].range_var.set(self.card_ranges[card_index])
                return

        self.card_ranges[card_index] = new_range
        self.save_card_ranges()
        self.update_card(card_index)

        # If this is the selected card, update timeline
        if card_index == self.selected_card:
            self.update_timeline()

    def open_custom_date_dialog(self):
        """
        Open a dialog for custom date selection

        Returns:
            str: Date in YYYY-MM-DD format, or None if cancelled
        """
        from tkinter import simpledialog

        # Ask for date in YYYY-MM-DD format
        date_str = simpledialog.askstring(
            "Custom Date", "Enter date (YYYY-MM-DD):", parent=self.root
        )

        if date_str:
            try:
                # Validate date format
                datetime.strptime(date_str, "%Y-%m-%d")
                return date_str
            except ValueError:
                messagebox.showerror(
                    "Invalid Date",
                    "Please enter date in YYYY-MM-DD format",
                    parent=self.root,
                )
                return None

        return None

    def select_card(self, card_index):
        """Select a card and show its timeline"""
        print("\n" + "=" * 80)
        print("SELECT_CARD CALLED")
        print("=" * 80)
        print(f"[SELECT] Card index: {card_index}")
        print(f"[SELECT] Card range: {self.card_ranges[card_index]}")
        print(f"[SELECT] Instance ID: {id(self)}")
        print(f"[SELECT] timeline_frame exists: {hasattr(self, 'timeline_frame')}")
        print(
            f"[SELECT] timeline_frame ID: {id(self.timeline_frame) if hasattr(self, 'timeline_frame') else 'N/A'}"
        )

        # Check scrollable frame state
        if hasattr(self, "timeline_scroll"):
            try:
                print(f"[SELECT] timeline_scroll exists: True")
                print(f"[SELECT] timeline_scroll ID: {id(self.timeline_scroll)}")
                print(
                    f"[SELECT] timeline_scroll.winfo_exists(): {self.timeline_scroll.winfo_exists()}"
                )
                if hasattr(self.timeline_scroll, "canvas"):
                    print(f"[SELECT] timeline_scroll.canvas exists: True")
                    print(
                        f"[SELECT] timeline_scroll.canvas ID: {id(self.timeline_scroll.canvas)}"
                    )
                    print(
                        f"[SELECT] timeline_scroll.canvas.winfo_exists(): {self.timeline_scroll.canvas.winfo_exists()}"
                    )
                    # Check canvas bindings
                    canvas_bindings = self.timeline_scroll.canvas.bind()
                    print(f"[SELECT] Canvas bindings: {canvas_bindings}")
            except Exception as e:
                print(f"[SELECT ERROR] Error checking timeline_scroll: {e}")
                import traceback

                traceback.print_exc()

        if hasattr(self, "timeline_frame") and self.timeline_frame:
            try:
                exists = self.timeline_frame.winfo_exists()
                print(f"[SELECT] timeline_frame.winfo_exists(): {exists}")
                master = self.timeline_frame.master
                print(f"[SELECT] timeline_frame.master: {master}")
                children = len(self.timeline_frame.winfo_children())
                print(f"[SELECT] timeline_frame children count: {children}")
            except Exception as e:
                print(f"[SELECT ERROR] Error checking timeline_frame state: {e}")

        self.selected_card = card_index
        print(f"[SELECT] Calling update_timeline()...")
        self.update_timeline()
        print(f"[SELECT] update_timeline() completed")

        # Check scrollable frame state AFTER update
        if hasattr(self, "timeline_scroll"):
            try:
                print(f"[SELECT AFTER] timeline_scroll still exists: True")
                print(
                    f"[SELECT AFTER] timeline_scroll.winfo_exists(): {self.timeline_scroll.winfo_exists()}"
                )
                if hasattr(self.timeline_scroll, "canvas"):
                    canvas_bindings = self.timeline_scroll.canvas.bind()
                    print(f"[SELECT AFTER] Canvas bindings: {canvas_bindings}")
                    print(
                        f"[SELECT AFTER] Canvas scrollregion: {self.timeline_scroll.canvas.cget('scrollregion')}"
                    )
            except Exception as e:
                print(
                    f"[SELECT AFTER ERROR] Error checking timeline_scroll after update: {e}"
                )

        self.timeline_title.config(text=f"Timeline: {self.card_ranges[card_index]}")
        print("=" * 80)
        print("SELECT_CARD COMPLETED")
        print("=" * 80 + "\n")

    def update_project_filter(self, set_default=False):
        """
        Update project filter based on selected sphere and project status filter

        Filter behavior:
        - active: Only active projects from selected sphere
        - archived: For active spheres show inactive projects; for inactive spheres show all projects
        - all: All projects from selected sphere
        """
        sphere = self.sphere_var.get()
        filter_status = self.status_filter.get()
        projects = ["All Projects"]

        if sphere == "All Spheres":
            # Disable project filter - all spheres always shows all projects
            self.project_filter.config(state="disabled")
            self.project_var.set("All Projects")
        else:
            # Get projects for selected sphere based on filter status
            self.project_filter.config(state="readonly")

            # Check if the selected sphere is active or inactive
            sphere_is_active = (
                self.tracker.settings.get("spheres", {})
                .get(sphere, {})
                .get("active", True)
            )

            for proj, data in self.tracker.settings.get("projects", {}).items():
                if data.get("sphere") == sphere:
                    is_active = data.get("active", True)

                    if filter_status == "active":
                        # Only show active projects
                        if is_active:
                            projects.append(proj)
                    elif filter_status == "archived":
                        # If sphere is active, show only inactive projects
                        # If sphere is inactive, show all projects
                        if sphere_is_active:
                            if not is_active:
                                projects.append(proj)
                        else:
                            projects.append(proj)
                    elif filter_status == "all":
                        # Show all projects
                        projects.append(proj)

            self.project_filter["values"] = projects

            # Set default project if requested and it exists in the list
            if (
                set_default
                and hasattr(self, "default_project")
                and self.default_project in projects
            ):
                self.project_var.set(self.default_project)
            else:
                self.project_var.set("All Projects")

    def on_filter_changed(self, event=None):
        """Handle when filters change"""
        if event and event.widget == self.sphere_filter:
            self.update_project_filter()

        self.refresh_all()

    def get_filtered_spheres(self):
        """
        Get list of spheres based on current filter status (active/all/archived)

        Filter behavior:
        - active: Only active spheres (with active projects)
        - archived: Both active spheres (for their inactive projects) and inactive spheres
        - all: All spheres

        Returns:
            list: List of sphere names including "All Spheres" option
        """
        filter_status = self.status_filter.get()
        spheres = ["All Spheres"]

        for sphere, data in self.tracker.settings.get("spheres", {}).items():
            is_active = data.get("active", True)

            if filter_status == "active":
                # Only show active spheres
                if is_active:
                    spheres.append(sphere)
            elif filter_status == "archived":
                # Show ALL spheres (both active and inactive)
                # Active spheres will show their inactive projects
                # Inactive spheres will show all their projects
                spheres.append(sphere)
            elif filter_status == "all":
                # Show all spheres
                spheres.append(sphere)

        return spheres

    def refresh_dropdowns(self):
        """
        Refresh both sphere and project dropdowns based on the current filter status
        Updates the dropdown values and resets selections if needed
        """
        # Get filtered spheres
        spheres = self.get_filtered_spheres()

        # Update sphere dropdown values
        self.sphere_filter["values"] = spheres

        # If current sphere selection is not in the new list, reset to "All Spheres"
        current_sphere = self.sphere_var.get()
        if current_sphere not in spheres:
            self.sphere_var.set("All Spheres")

        # Update project filter with current sphere and status filter
        self.update_project_filter()

        # If current project selection is not in the new list, reset to "All Projects"
        current_project = self.project_var.get()
        current_values = list(self.project_filter["values"])
        if current_project not in current_values:
            self.project_var.set("All Projects")

        # Refresh the data display
        self.refresh_all()

    def refresh_all(self):
        """Refresh all cards and timeline"""
        for i in range(3):
            self.update_card(i)
        self.update_timeline()

    def get_date_range(self, range_name):
        """Get start and end dates for a given range name"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if range_name == "Today":
            start = today
            end = today + timedelta(days=1)
        elif range_name == "Yesterday":
            yesterday = today - timedelta(days=1)
            start = yesterday
            end = yesterday + timedelta(days=1)
        elif range_name.startswith("Custom:"):
            # Parse custom date from format "Custom: YYYY-MM-DD"
            try:
                date_str = range_name.split(":", 1)[1].strip()
                custom_date = datetime.strptime(date_str, "%Y-%m-%d")
                start = custom_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end = start + timedelta(days=1)
            except (ValueError, IndexError):
                # If parsing fails, default to today
                start = today
                end = today + timedelta(days=1)
        elif range_name == "Last 7 Days":
            start = today - timedelta(days=6)
            end = today + timedelta(days=1)
        elif range_name == "Last 14 Days":
            start = today - timedelta(days=13)
            end = today + timedelta(days=1)
        elif range_name == "Last 30 Days":
            start = today - timedelta(days=29)
            end = today + timedelta(days=1)
        elif range_name == "This Week (Mon-Sun)" or range_name == "This Week":
            # Monday to Sunday
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=7)
        elif range_name == "Last Week (Mon-Sun)" or range_name == "Last Week":
            start = today - timedelta(days=today.weekday() + 7)
            end = start + timedelta(days=7)
        elif range_name == "This Month":
            start = today.replace(day=1)
            end = (start + timedelta(days=32)).replace(day=1)
        elif range_name == "Last Month":
            end = today.replace(day=1)
            start = (end - timedelta(days=1)).replace(day=1)
        elif range_name == "Custom Date":
            # Open dialog to select custom date
            start = today
            end = today + timedelta(days=1)
        else:  # All Time
            start = datetime(2000, 1, 1)
            end = datetime(2100, 1, 1)

        return start, end

    def get_date_range_for_filter(self, range_name):
        """
        Get date range for filter (alias for get_date_range for testing)

        Returns:
            tuple: (start_date, end_date) as datetime objects
        """
        return self.get_date_range(range_name)

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
        """Format seconds as Xh Ym Zs"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

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

    def get_timeline_data(self, range_name):
        """
        Get structured timeline data for the specified date range.

        Returns a list of dictionaries with the following keys:
        - date: Date string (YYYY-MM-DD)
        - period_start: Start time of the period
        - duration: Duration in seconds
        - type: Type of period (Active, Break, Idle)
        - primary_project: Primary project/action name
        - primary_comment: Primary comment
        - secondary_project: Secondary project/action name
        - secondary_comment: Secondary comment
        - session_active_comments: Session-level active comments
        - session_break_idle_comments: Session-level break/idle comments
        - session_notes: Session-level notes
        """
        start_date, end_date = self.get_date_range(range_name)
        all_data = self.tracker.load_data()

        sphere_filter = self.sphere_var.get()
        project_filter = self.project_var.get()
        status_filter = (
            self.status_filter.get()
        )  # Get the radio button filter (active/all/archived)

        # Collect all periods
        timeline_data = []

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

            # Get sphere active status for this session (used by all period types)
            sphere_name = session_data.get("sphere", "")
            sphere_active = (
                self.tracker.settings.get("spheres", {})
                .get(sphere_name, {})
                .get("active", True)
            )

            # Get session-level comments
            # Handle both old format (direct fields) and new format (session_comments dict)
            session_comments_dict = session_data.get("session_comments", {})
            if session_comments_dict:
                # New format: session comments are in a nested dict
                session_active_comments = session_comments_dict.get("active_notes", "")
                break_notes = session_comments_dict.get("break_notes", "")
                idle_notes = session_comments_dict.get("idle_notes", "")
                session_notes = session_comments_dict.get("session_notes", "")
            else:
                # Old format: session comments are direct fields (backwards compatibility)
                session_active_comments = session_data.get(
                    "session_active_comments", ""
                )
                # For old format, we can't separate break and idle, so use the combined field for both
                session_break_idle_comments = session_data.get(
                    "session_break_idle_comments", ""
                )
                break_notes = session_break_idle_comments
                idle_notes = session_break_idle_comments
                session_notes = session_data.get("session_notes", "")

            # Add active periods
            for period in session_data.get("active", []):
                # Determine primary and secondary projects
                primary_project = ""
                primary_comment = ""
                secondary_project = ""
                secondary_comment = ""

                if period.get("project"):
                    # Single project case
                    primary_project = period.get("project", "")
                    primary_comment = period.get("comment", "")
                else:
                    # Multiple projects case
                    for project_item in period.get("projects", []):
                        if project_item.get("project_primary", True):
                            primary_project = project_item.get("name", "")
                            primary_comment = project_item.get("comment", "")
                        else:
                            secondary_project = project_item.get("name", "")
                            secondary_comment = project_item.get("comment", "")

                # Check project filter
                if project_filter != "All Projects":
                    if (
                        primary_project != project_filter
                        and secondary_project != project_filter
                    ):
                        continue

                # Get project active status
                project_active = (
                    self.tracker.settings.get("projects", {})
                    .get(primary_project, {})
                    .get("active", True)
                )

                # Apply status filter (Active/All/Archived radio button)
                # Active: Show only if BOTH sphere AND project are active
                # All: Show everything (no filtering)
                # Archived: Show if EITHER sphere OR project is inactive (but not both active)
                if status_filter == "active":
                    if not (sphere_active and project_active):
                        continue  # Skip inactive combinations
                elif status_filter == "archived":
                    if sphere_active and project_active:
                        continue  # Skip fully active combinations
                # For "all", don't skip anything

                timeline_data.append(
                    {
                        "date": session_data.get("date"),
                        "period_start": period.get("start", ""),
                        "duration": period.get("duration", 0),
                        "sphere": sphere_name,
                        "sphere_active": sphere_active,
                        "project": primary_project,
                        "project_active": project_active,
                        "type": "Active",
                        "primary_project": primary_project,
                        "primary_comment": primary_comment,
                        "secondary_project": secondary_project,
                        "secondary_comment": secondary_comment,
                        "session_active_comments": session_active_comments,
                        "session_break_idle_comments": "",  # Don't show break/idle comments on active periods
                        "session_notes": session_notes,
                    }
                )

            # Add break periods
            for period in session_data.get("breaks", []):
                # Determine primary and secondary actions
                primary_action = ""
                primary_comment = ""
                secondary_action = ""
                secondary_comment = ""

                if period.get("action"):
                    # Single action case
                    primary_action = period.get("action", "")
                    primary_comment = period.get("comment", "")
                else:
                    # Multiple actions case
                    for action_item in period.get("actions", []):
                        if action_item.get("break_primary", True):
                            primary_action = action_item.get("name", "")
                            primary_comment = action_item.get("comment", "")
                        else:
                            secondary_action = action_item.get("name", "")
                            secondary_comment = action_item.get("comment", "")

                # Apply status filter for break periods
                # Since break actions don't have active status, filter based on sphere only
                if status_filter == "active":
                    if not sphere_active:
                        continue  # Skip if sphere is inactive
                elif status_filter == "archived":
                    if sphere_active:
                        continue  # Archived filter only shows inactive spheres for breaks
                # For "all", don't skip anything

                timeline_data.append(
                    {
                        "date": session_data.get("date"),
                        "period_start": period.get("start", ""),
                        "duration": period.get("duration", 0),
                        "sphere": sphere_name,
                        "sphere_active": sphere_active,
                        "project": primary_action,
                        "project_active": True,  # Break actions don't have active status
                        "type": "Break",
                        "primary_project": primary_action,
                        "primary_comment": primary_comment,
                        "secondary_project": secondary_action,
                        "secondary_comment": secondary_comment,
                        "session_active_comments": "",  # Don't show active comments on break periods
                        "session_break_idle_comments": break_notes,  # Only show break notes on break periods
                        "session_notes": session_notes,
                    }
                )

            # Add idle periods
            for period in session_data.get("idle_periods", []):
                if period.get("end_timestamp"):
                    # Determine primary and secondary actions
                    primary_action = ""
                    primary_comment = ""
                    secondary_action = ""
                    secondary_comment = ""

                    if period.get("action"):
                        # Single action case
                        primary_action = period.get("action", "")
                        primary_comment = period.get("comment", "")
                    else:
                        # Multiple actions case
                        for action_item in period.get("actions", []):
                            if action_item.get("idle_primary", True):
                                primary_action = action_item.get("name", "")
                                primary_comment = action_item.get("comment", "")
                            else:
                                secondary_action = action_item.get("name", "")
                                secondary_comment = action_item.get("comment", "")

                    # Apply status filter for idle periods
                    # Since idle actions don't have active status, filter based on sphere only
                    if status_filter == "active":
                        if not sphere_active:
                            continue  # Skip if sphere is inactive
                    elif status_filter == "archived":
                        if sphere_active:
                            continue  # Archived filter only shows inactive spheres for idle
                    # For "all", don't skip anything

                    timeline_data.append(
                        {
                            "date": session_data.get("date"),
                            "period_start": period.get("start", ""),
                            "duration": period.get("duration", 0),
                            "sphere": sphere_name,
                            "sphere_active": sphere_active,
                            "project": primary_action,
                            "project_active": True,  # Idle actions don't have active status
                            "type": "Idle",
                            "primary_project": primary_action,
                            "primary_comment": primary_comment,
                            "secondary_project": secondary_action,
                            "secondary_comment": secondary_comment,
                            "session_active_comments": "",  # Don't show active comments on idle periods
                            "session_break_idle_comments": idle_notes,  # Only show idle notes on idle periods
                            "session_notes": session_notes,
                        }
                    )

        # Sort by date and start time
        timeline_data.sort(key=lambda x: (x["date"], x["period_start"]))

        return timeline_data

    def load_more_periods(self):
        """Load the next batch of periods (50 at a time) into the timeline"""
        # Remove Load More button if it exists
        if self.load_more_button:
            self.load_more_button.destroy()
            self.load_more_button = None

        # Calculate range for this batch
        start_idx = self.periods_loaded
        end_idx = min(start_idx + self.periods_per_page, len(self.timeline_data_all))

        # Get periods for this batch
        periods_to_render = self.timeline_data_all[start_idx:end_idx]

        # Render this batch of periods
        for idx, period in enumerate(periods_to_render, start=start_idx):
            self._render_timeline_period(period, idx)

        # Update loaded count
        self.periods_loaded = end_idx

        # Add Load More button if there are more periods to load
        if self.periods_loaded < len(self.timeline_data_all):
            remaining = len(self.timeline_data_all) - self.periods_loaded
            next_batch = min(self.periods_per_page, remaining)

            button_frame = ttk.Frame(self.timeline_frame)
            button_frame.grid(row=self.periods_loaded, column=0, pady=10)

            button_text = f"Load {next_batch} More ({self.periods_loaded} of {len(self.timeline_data_all)} shown)"
            self.load_more_button = ttk.Button(
                button_frame, text=button_text, command=self.load_more_periods
            )
            self.load_more_button.pack()
        else:
            # All periods loaded
            if len(self.timeline_data_all) > self.periods_per_page:
                # Only show "all loaded" message if we had multiple pages
                label_frame = ttk.Frame(self.timeline_frame)
                label_frame.grid(row=self.periods_loaded, column=0, pady=10)
                ttk.Label(
                    label_frame,
                    text=f"All {len(self.timeline_data_all)} periods loaded",
                    font=("Arial", 10, "italic"),
                ).pack()

    def _render_timeline_period(self, period, idx):
        """Render a single period row in the timeline

        Args:
            period: Period dict with timeline data
            idx: Row index for grid placement
        """
        # Color code based on type
        if period["type"] == "Active":
            bg_color = "#e8f5e9"  # Light green
        else:  # Break or Idle
            bg_color = "#fff3e0"  # Light orange

        row_frame = tk.Frame(self.timeline_frame, bg=bg_color)
        row_frame.grid(row=idx, column=0, sticky=(tk.W, tk.E), pady=1)

        # NOTE: Removed individual mousewheel binding on row_frame
        # ScrollableFrame's bind_all handler will handle scrolling automatically
        # Adding bindings here was causing the handler to stop working after
        # multiple update_timeline() calls

        # Configure row_frame columns for grid layout
        for col in range(14):  # 14 columns total
            if col == 13:  # Session Notes (last column) expands
                row_frame.columnconfigure(col, weight=1)
            else:
                row_frame.columnconfigure(col, weight=0)

        # Create label helper function
        col_idx = 0  # Track current column index

        def create_label(
            text, width, wraplength=0, expand=False, use_text_widget=False
        ):
            """Create a label or text widget with optional text wrapping

            Args:
                text: Text to display
                width: Width in characters
                wraplength: Pixel width for text wrapping (0 = no wrap) - only for Label
                expand: Whether to expand to fill remaining space
                use_text_widget: Use Text widget instead of Label (for better wrapping)
            """
            nonlocal col_idx

            if use_text_widget:
                # Use Text widget for better text wrapping
                txt = tk.Text(
                    row_frame,
                    width=width,
                    height=1,
                    wrap=tk.WORD,
                    bg=bg_color,
                    font=("Arial", 8),
                    relief=tk.FLAT,
                    state=tk.NORMAL,
                )
                txt.insert("1.0", text)
                txt.config(state=tk.DISABLED)  # Make read-only

                # CRITICAL FIX: Text widgets have class bindings that interfere with bind_all
                # Unbind the Text widget's default mousewheel handling
                txt.bind("<MouseWheel>", lambda e: "break")

                if expand:
                    txt.grid(row=0, column=col_idx, sticky=(tk.W, tk.E))
                else:
                    txt.grid(row=0, column=col_idx, sticky=tk.W)

                # NOTE: Removed mousewheel binding - ScrollableFrame handles it
                col_idx += 1
                return txt
            else:
                lbl = tk.Label(
                    row_frame,
                    text=text,
                    width=width,
                    anchor="w",
                    padx=3,
                    bg=bg_color,
                    font=("Arial", 8),
                    wraplength=wraplength,
                    justify="left",
                )
                if expand:
                    lbl.grid(row=0, column=col_idx, sticky=(tk.W, tk.E))
                else:
                    lbl.grid(row=0, column=col_idx, sticky=tk.W)
                # NOTE: Removed mousewheel binding - ScrollableFrame handles it
                col_idx += 1
                return lbl

        # Render all columns with proper widths using grid layout
        create_label(period["date"], 10)
        create_label(self.format_time_12hr(period["period_start"]), 9)
        create_label(self.format_duration(period["duration"]), 8)
        create_label(period.get("sphere", ""), 12)
        create_label("✓" if period.get("sphere_active", True) else "", 5)
        create_label("✓" if period.get("project_active", True) else "", 5)
        create_label(period["type"], 7)
        create_label(period["primary_project"], 15)
        create_label(period["primary_comment"], 21, use_text_widget=True)
        create_label(period["secondary_project"], 15)
        create_label(period["secondary_comment"], 21, use_text_widget=True)
        create_label(period["session_active_comments"], 21, use_text_widget=True)
        create_label(period["session_break_idle_comments"], 21, use_text_widget=True)
        create_label(period["session_notes"], 21, use_text_widget=True, expand=True)

    def update_timeline(self):
        """Update the timeline display with Load More pagination"""
        if not hasattr(self, "timeline_frame") or self.timeline_frame is None:
            return

        # Check if timeline_frame is valid
        try:
            if not self.timeline_frame.winfo_exists():
                return
        except tk.TclError:
            return

        # CRITICAL FIX: Clear children instead of destroying the frame itself
        # Destroying the frame was breaking the ScrollableFrame's canvas
        for widget in self.timeline_frame.winfo_children():
            widget.destroy()

        # Configure timeline_frame column to expand
        self.timeline_frame.columnconfigure(0, weight=1)

        # Get ALL data using new get_timeline_data method
        range_name = self.card_ranges[self.selected_card]
        periods = self.get_timeline_data(range_name)

        # Sort by date and start time (or by selected column)
        if not hasattr(self, "timeline_sort_column"):
            self.timeline_sort_column = "date"
            self.timeline_sort_reverse = True

        # Sort by current column
        sort_key_map = {
            "date": lambda x: (x["date"], x["period_start"]),
            "type": lambda x: x["type"],
            "primary_project": lambda x: x["primary_project"],
            "secondary_project": lambda x: x["secondary_project"],
            "start": lambda x: x["period_start"],
            "duration": lambda x: x["duration"],
        }
        periods.sort(
            key=sort_key_map.get(self.timeline_sort_column, sort_key_map["date"]),
            reverse=self.timeline_sort_reverse,
        )

        # Store full sorted dataset
        self.timeline_data_all = periods

        # Reset pagination - show only first 50 periods
        self.periods_loaded = 0

        # Load first page (50 periods)
        self.load_more_periods()

        # Update frozen header
        self.update_timeline_header()

        # CRITICAL FIX: Force canvas scrollregion recalculation and visual update
        # After clearing/recreating children, the canvas needs explicit update
        if hasattr(self, "scrollable_container") and hasattr(
            self.scrollable_container, "canvas"
        ):
            # Force immediate geometry update
            self.scrollable_container.content_frame.update_idletasks()
            # Recalculate scrollregion based on actual content
            bbox = self.scrollable_container.canvas.bbox("all")
            if bbox:
                self.scrollable_container.canvas.configure(scrollregion=bbox)
            # Force visual redraw
            self.scrollable_container.canvas.update_idletasks()
            # Reset scroll position to top
            self.scrollable_container.canvas.yview_moveto(0)

    def sort_timeline(self, column):
        """Sort timeline by column"""
        if self.timeline_sort_column == column:
            self.timeline_sort_reverse = not self.timeline_sort_reverse
        else:
            self.timeline_sort_column = column
            self.timeline_sort_reverse = False
        self.update_timeline()

    def update_timeline_header(self):
        """Update the frozen timeline header with current sort indicators"""
        # Clear existing header
        for widget in self.timeline_header_frame.winfo_children():
            widget.destroy()

        # Configure timeline_header_frame columns for grid layout
        for col in range(14):  # 14 columns total
            if col == 13:  # Session Notes (last column) expands
                self.timeline_header_frame.columnconfigure(col, weight=1)
            else:
                self.timeline_header_frame.columnconfigure(col, weight=0)

        col_idx = 0  # Track current column index

        def create_single_row_header(text, column_key, width):
            """Create single-row header with vertical centering for alignment with two-row headers"""
            nonlocal col_idx

            label = tk.Label(
                self.timeline_header_frame,
                text=(
                    text + " ▼"
                    if self.timeline_sort_column == column_key
                    and self.timeline_sort_reverse
                    else (
                        text + " ▲" if self.timeline_sort_column == column_key else text
                    )
                ),
                font=("Arial", 8),
                width=width,
                anchor="w",
                padx=3,
                pady=6,  # Vertical padding to center with two-row headers
                bg="#d0d0d0",
                cursor="hand2",
            )
            label.grid(row=0, column=col_idx, sticky=tk.W)
            label.bind("<Button-1>", lambda e: self.sort_timeline(column_key))
            col_idx += 1
            return label

        def create_two_row_header(top_text, bottom_text, width):
            """Create two-row header with stacked labels using a temporary container Frame"""
            nonlocal col_idx

            # For two-row headers, we need a container Frame to stack the labels
            container = tk.Frame(self.timeline_header_frame, bg="#d0d0d0")
            container.grid(row=0, column=col_idx, sticky=tk.W)

            # Top row label
            tk.Label(
                container,
                text=top_text,
                font=("Arial", 8),
                width=width,
                anchor="w",
                padx=3,
                bg="#d0d0d0",
            ).pack()

            # Bottom row label (slightly smaller font)
            tk.Label(
                container,
                text=bottom_text,
                font=("Arial", 7),
                width=width,
                anchor="w",
                padx=3,
                bg="#d0d0d0",
            ).pack()

            col_idx += 1
            return container

        def create_non_sortable_single_row_header(
            text, width, expand=False, use_text_widget=False
        ):
            """Create non-sortable single-row header with vertical centering

            Args:
                use_text_widget: If True, use Text widget instead of Label to match data row widget type.
                                 This ensures pixel-perfect width matching for comment columns.
            """
            nonlocal col_idx

            if use_text_widget:
                # Use Text widget to match data row widget type (for comment columns)
                txt = tk.Text(
                    self.timeline_header_frame,
                    width=width,
                    height=1,
                    wrap=tk.NONE,
                    bg="#d0d0d0",
                    font=("Arial", 8),
                    relief=tk.FLAT,
                    state=tk.NORMAL,
                )
                txt.insert("1.0", text)
                txt.config(state=tk.DISABLED)  # Make read-only
                if expand:
                    txt.grid(row=0, column=col_idx, sticky=(tk.W, tk.E))
                else:
                    txt.grid(row=0, column=col_idx, sticky=tk.W)
                col_idx += 1
                return txt
            else:
                label = tk.Label(
                    self.timeline_header_frame,
                    text=text,
                    font=("Arial", 8),
                    width=width,
                    anchor="w",
                    padx=3,
                    pady=6,  # Vertical padding to center with two-row headers
                    bg="#d0d0d0",
                )
                if expand:
                    label.grid(row=0, column=col_idx, sticky=(tk.W, tk.E))
                else:
                    label.grid(row=0, column=col_idx, sticky=tk.W)

                col_idx += 1
                return label

        # Header columns with new two-row design for "Active" columns
        create_single_row_header("Date", "date", 10)
        create_single_row_header("Start", "start", 9)
        create_single_row_header("Duration", "duration", 8)
        create_single_row_header("Sphere", "sphere", 12)
        create_two_row_header("Sphere", "Active", 5)  # Two-row: "Sphere" / "Active"
        create_two_row_header("Project", "Active", 5)  # Two-row: "Project" / "Active"
        create_single_row_header("Type", "type", 7)
        create_single_row_header("Primary Action", "primary_project", 15)
        # Use Text widget for comment columns to match data row widget type (pixel-perfect alignment)
        create_non_sortable_single_row_header(
            "Primary Comment", 21, use_text_widget=True
        )
        create_single_row_header("Secondary Action", "secondary_project", 15)
        create_non_sortable_single_row_header(
            "Secondary Comment", 21, use_text_widget=True
        )
        create_non_sortable_single_row_header(
            "Active Comments", 21, use_text_widget=True
        )
        create_non_sortable_single_row_header(
            "Break Comments", 21, use_text_widget=True
        )
        create_non_sortable_single_row_header(
            "Session Notes", 21, use_text_widget=True, expand=True
        )

    def export_to_csv(self):
        """Export timeline data to CSV"""
        print("\n" + "=" * 80)
        print("CSV EXPORT STARTED")
        print("=" * 80)
        print(f"[CSV] Instance ID: {id(self)}")
        print(f"[CSV] timeline_frame exists: {hasattr(self, 'timeline_frame')}")
        print(
            f"[CSV] timeline_frame ID: {id(self.timeline_frame) if hasattr(self, 'timeline_frame') else 'N/A'}"
        )
        print(
            f"[CSV] timeline_data_all size: {len(self.timeline_data_all) if hasattr(self, 'timeline_data_all') else 'N/A'}"
        )
        print(f"[CSV] selected_card: {self.selected_card}")
        print(f"[CSV] card_ranges: {self.card_ranges}")

        # Get data for selected card's range
        range_name = self.card_ranges[self.selected_card]
        print(f"[CSV] Exporting range: {range_name}")
        start_date, end_date = self.get_date_range(range_name)
        print(f"[CSV] Date range: {start_date} to {end_date}")
        all_data = self.tracker.load_data()
        print(f"[CSV] Loaded {len(all_data)} sessions from file")

        sphere_filter = self.sphere_var.get()
        project_filter = self.project_var.get()
        status_filter = (
            self.status_filter.get()
        )  # Get the radio button filter (active/all/archived)

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

            # Get sphere active status for filtering
            sphere_active = (
                self.tracker.settings.get("spheres", {})
                .get(session_sphere, {})
                .get("active", True)
            )

            for period in session_data.get("active", []):
                project_name = period.get("project", "")
                if project_filter != "All Projects" and project_name != project_filter:
                    continue

                # Get project active status
                project_active = (
                    self.tracker.settings.get("projects", {})
                    .get(project_name, {})
                    .get("active", True)
                )

                # Apply status filter (Active/All/Archived radio button)
                # Active: Show only if BOTH sphere AND project are active
                # All: Show everything (no filtering)
                # Archived: Show if EITHER sphere OR project is inactive (but not both active)
                if status_filter == "active":
                    if not (sphere_active and project_active):
                        continue  # Skip inactive combinations
                elif status_filter == "archived":
                    if sphere_active and project_active:
                        continue  # Skip fully active combinations
                # For "all", don't skip anything

                # Get primary and secondary project data
                primary_project = ""
                primary_comment = ""
                secondary_project = ""
                secondary_comment = ""

                if period.get("project"):
                    # Single project case
                    primary_project = period.get("project", "")
                    primary_comment = period.get("comment", "")
                else:
                    # Multiple projects case
                    for project_item in period.get("projects", []):
                        if project_item.get("project_primary", True):
                            primary_project = project_item.get("name", "")
                            primary_comment = project_item.get("comment", "")
                        else:
                            secondary_project = project_item.get("name", "")
                            secondary_comment = project_item.get("comment", "")

                # Get session-level comments
                session_comments_dict = session_data.get("session_comments", {})
                if session_comments_dict:
                    session_active_comments = session_comments_dict.get(
                        "active_notes", ""
                    )
                    session_notes = session_comments_dict.get("session_notes", "")
                else:
                    session_active_comments = session_data.get(
                        "session_active_comments", ""
                    )
                    session_notes = session_data.get("session_notes", "")

                periods.append(
                    {
                        "Date": session_data.get("date"),
                        "Start": period.get("start", ""),
                        "Duration": self.format_duration(period.get("duration", 0)),
                        "Sphere": session_sphere,
                        "Sphere Active": "Yes" if sphere_active else "No",
                        "Project Active": "Yes" if project_active else "No",
                        "Type": "Active",
                        "Primary Action": primary_project,
                        "Primary Comment": primary_comment,
                        "Secondary Action": secondary_project,
                        "Secondary Comment": secondary_comment,
                        "Active Comments": session_active_comments,
                        "Break Comments": "",
                        "Session Notes": session_notes,
                    }
                )

            for period in session_data.get("breaks", []):
                # Apply status filter for break periods
                # Since break actions don't have active status, filter based on sphere only
                if status_filter == "active":
                    if not sphere_active:
                        continue  # Skip if sphere is inactive
                elif status_filter == "archived":
                    if sphere_active:
                        continue  # Archived filter only shows inactive spheres for breaks
                # For "all", don't skip anything

                # Get primary and secondary action data
                primary_action = ""
                primary_comment = ""
                secondary_action = ""
                secondary_comment = ""

                if period.get("action"):
                    # Single action case
                    primary_action = period.get("action", "")
                    primary_comment = period.get("comment", "")
                else:
                    # Multiple actions case
                    for action_item in period.get("actions", []):
                        if action_item.get("break_primary", True):
                            primary_action = action_item.get("name", "")
                            primary_comment = action_item.get("comment", "")
                        else:
                            secondary_action = action_item.get("name", "")
                            secondary_comment = action_item.get("comment", "")

                # Get session-level comments
                session_comments_dict = session_data.get("session_comments", {})
                if session_comments_dict:
                    break_notes = session_comments_dict.get("break_notes", "")
                    session_notes = session_comments_dict.get("session_notes", "")
                else:
                    break_notes = session_data.get("session_break_idle_comments", "")
                    session_notes = session_data.get("session_notes", "")

                periods.append(
                    {
                        "Date": session_data.get("date"),
                        "Start": period.get("start", ""),
                        "Duration": self.format_duration(period.get("duration", 0)),
                        "Sphere": session_sphere,
                        "Sphere Active": "Yes" if sphere_active else "No",
                        "Project Active": "N/A",
                        "Type": "Break",
                        "Primary Action": primary_action,
                        "Primary Comment": primary_comment,
                        "Secondary Action": secondary_action,
                        "Secondary Comment": secondary_comment,
                        "Active Comments": "",
                        "Break Comments": break_notes,
                        "Session Notes": session_notes,
                    }
                )

        if not periods:
            print(f"[CSV] No data to export")
            messagebox.showinfo("No Data", "No data to export for selected filters")
            print("=" * 80)
            print("CSV EXPORT ABORTED - No Data")
            print("=" * 80 + "\n")
            return

        print(f"[CSV] Collected {len(periods)} periods to export")

        # Ask user for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"time_tracker_{range_name.replace(' ', '_')}.csv",
        )

        if not filename:
            print(f"[CSV] User cancelled export")
            print("=" * 80)
            print("CSV EXPORT CANCELLED")
            print("=" * 80 + "\n")
            return

        print(f"[CSV] Saving to: {filename}")

        try:
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                # CSV headers match timeline headers in order
                fieldnames = [
                    "Date",
                    "Start",
                    "Duration",
                    "Sphere",
                    "Sphere Active",
                    "Project Active",
                    "Type",
                    "Primary Action",
                    "Primary Comment",
                    "Secondary Action",
                    "Secondary Comment",
                    "Active Comments",
                    "Break Comments",
                    "Session Notes",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for period in periods:
                    writer.writerow(period)

            print(f"[CSV] Successfully exported {len(periods)} entries")
            messagebox.showinfo(
                "Success", f"Exported {len(periods)} entries to {filename}"
            )

            print("\n[CSV STATE AFTER EXPORT]:")
            print(f"[CSV] Instance ID: {id(self)}")
            print(f"[CSV] timeline_frame ID: {id(self.timeline_frame)}")
            print(f"[CSV] timeline_data_all size: {len(self.timeline_data_all)}")
            print(f"[CSV] periods_loaded: {self.periods_loaded}")
            print(
                f"[CSV] Timeline frame children count: {len(self.timeline_frame.winfo_children())}"
            )
            print("=" * 80)
            print("CSV EXPORT COMPLETED SUCCESSFULLY")
            print("=" * 80 + "\n")

        except Exception as e:
            print(f"[CSV ERROR] Failed to export: {e}")
            import traceback

            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to export CSV: {e}")
            print("=" * 80)
            print("CSV EXPORT FAILED")
            print("=" * 80 + "\n")

    def open_latest_session(self):
        """Open session view from analysis frame"""
        # Open session view with flag indicating we came from analysis
        self.tracker.open_session_view(from_analysis=True)

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
