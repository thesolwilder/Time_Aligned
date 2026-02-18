import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import csv
from datetime import datetime, timedelta

from src.ui_helpers import ScrollableFrame, get_frame_background
from src.constants import (
    COLOR_ACTIVE_LIGHT_GREEN,
    COLOR_BREAK_LIGHT_ORANGE,
    COLOR_GRAY_BACKGROUND,
    COLOR_LINK_BLUE,
    COLOR_TRAY_ACTIVE,
    COLOR_TRAY_BREAK,
    FONT_BODY,
    FONT_EXTRA_SMALL,
    FONT_HEADING,
    FONT_LINK,
    FONT_MICRO,
    FONT_NORMAL_ITALIC,
    FONT_TIMER_SMALL,
    PIE_CHART_FONT,
    PIE_CHART_MARGIN,
    PIE_CHART_SIZE,
    PIE_TEXT_MIN_PERCENT,
)


def draw_pie_chart(canvas, active_secs, break_secs):
    """Draw a two-section pie chart on a tk.Canvas showing active vs break/idle.

    Active slice uses COLOR_TRAY_ACTIVE (green); break/idle uses COLOR_TRAY_BREAK
    (amber). Percentage labels are rendered inside each slice when the slice is
    >= PIE_TEXT_MIN_PERCENT percent. If both values are zero, a grey 'No data'
    placeholder circle is drawn instead.

    The chart starts at 12 o'clock and proceeds clockwise so the active (usually
    larger) slice fills from the top.

    Args:
        canvas: tk.Canvas widget to draw on (must have width and height set).
        active_secs: Total active time in seconds (>= 0).
        break_secs: Total break/idle time in seconds (>= 0).
    """
    canvas.delete("all")
    size = int(canvas["width"])
    margin = PIE_CHART_MARGIN
    x0, y0 = margin, margin
    x1, y1 = size - margin, size - margin
    cx = size / 2
    cy = size / 2
    # Radius used for placing percentage text at 55% of the arc radius
    text_radius = (size - 2 * margin) / 2 * 0.55

    total = active_secs + break_secs

    if total == 0:
        canvas.create_arc(
            x0,
            y0,
            x1,
            y1,
            start=0,
            extent=359.9,
            fill="#BDBDBD",
            outline="",
            style=tk.PIESLICE,
        )
        canvas.create_text(
            cx,
            cy,
            text="No data",
            fill="#FFFFFF",
            font=PIE_CHART_FONT,
        )
        return

    active_frac = active_secs / total
    break_frac = break_secs / total
    active_pct = round(active_frac * 100)
    break_pct = 100 - active_pct

    # --- Full-circle edge cases ---
    if break_secs == 0:
        canvas.create_arc(
            x0,
            y0,
            x1,
            y1,
            start=0,
            extent=359.9,
            fill=COLOR_TRAY_ACTIVE,
            outline="",
            style=tk.PIESLICE,
        )
        canvas.create_text(
            cx,
            cy,
            text="100%",
            fill="#FFFFFF",
            font=PIE_CHART_FONT,
        )
        return

    if active_secs == 0:
        canvas.create_arc(
            x0,
            y0,
            x1,
            y1,
            start=0,
            extent=359.9,
            fill=COLOR_TRAY_BREAK,
            outline="",
            style=tk.PIESLICE,
        )
        canvas.create_text(
            cx,
            cy,
            text="100%",
            fill="#FFFFFF",
            font=PIE_CHART_FONT,
        )
        return

    # --- Two-section chart ---
    # Angles: Tkinter measures counterclockwise from 3 o'clock.
    # start=90 places the origin at 12 o'clock; negative extent = clockwise.
    start_angle = 90
    active_extent = -(active_frac * 360)
    break_start = start_angle + active_extent
    break_extent = -(break_frac * 360)

    canvas.create_arc(
        x0,
        y0,
        x1,
        y1,
        start=start_angle,
        extent=active_extent,
        fill=COLOR_TRAY_ACTIVE,
        outline="",
        style=tk.PIESLICE,
    )
    canvas.create_arc(
        x0,
        y0,
        x1,
        y1,
        start=break_start,
        extent=break_extent,
        fill=COLOR_TRAY_BREAK,
        outline="",
        style=tk.PIESLICE,
    )

    # --- Percentage labels at midpoint of each slice ---
    active_mid_rad = math.radians(start_angle + active_extent / 2)
    break_mid_rad = math.radians(break_start + break_extent / 2)

    if active_pct >= PIE_TEXT_MIN_PERCENT:
        ax = cx + text_radius * math.cos(active_mid_rad)
        ay = cy - text_radius * math.sin(active_mid_rad)
        canvas.create_text(
            ax,
            ay,
            text=f"{active_pct}%",
            fill="#FFFFFF",
            font=PIE_CHART_FONT,
        )

    if break_pct >= PIE_TEXT_MIN_PERCENT:
        bx = cx + text_radius * math.cos(break_mid_rad)
        by = cy - text_radius * math.sin(break_mid_rad)
        canvas.create_text(
            bx,
            by,
            text=f"{break_pct}%",
            fill="#FFFFFF",
            font=PIE_CHART_FONT,
        )


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
        except Exception as error:
            messagebox.showerror("Error", f"Failed to save settings: {error}")

    def create_widgets(self):
        """Create all UI elements for the analysis frame"""
        # Create scrollable container for entire frame
        scrollable_container = ScrollableFrame(self)
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

        # Get background color to match frame
        frame_bg = get_frame_background()

        # Back to Tracker link
        back_link = tk.Label(
            header_frame,
            text="← Back to Tracker",
            fg=COLOR_LINK_BLUE,
            bg=frame_bg,
            cursor="hand2",
            font=FONT_LINK,
        )
        back_link.pack(side=tk.LEFT, padx=5)
        back_link.bind("<Button-1>", lambda e: self.tracker.close_analysis())

        # Session View link
        session_view_link = tk.Label(
            header_frame,
            text="Session View",
            fg=COLOR_LINK_BLUE,
            bg=frame_bg,
            cursor="hand2",
            font=FONT_LINK,
        )
        session_view_link.pack(side=tk.LEFT, padx=5)
        session_view_link.bind("<Button-1>", lambda e: self.open_latest_session())

        ttk.Button(header_frame, text="Export to CSV", command=self.export_to_csv).pack(
            side=tk.RIGHT, padx=5
        )

        # Filters
        filter_frame = ttk.Frame(content_frame)
        filter_frame.grid(
            row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10, padx=10
        )

        # Apply header font style to filter comboboxes
        filter_combo_style = ttk.Style()
        filter_combo_style.configure(
            "Filter.TCombobox", font=FONT_HEADING, padding=[4, 4]
        )
        filter_combo_style.configure("Filter.TRadiobutton", font=FONT_BODY)

        # Sphere label and dropdown
        ttk.Label(filter_frame, text="Sphere:", font=FONT_BODY).pack(
            side=tk.LEFT, padx=5
        )

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
            style="Filter.TCombobox",
            width=12,
        )
        self.sphere_filter.pack(side=tk.LEFT, padx=5)
        self.sphere_filter.configure(font=FONT_HEADING)
        self.sphere_filter.bind("<<ComboboxSelected>>", self.on_filter_changed)

        # Project label and dropdown
        ttk.Label(filter_frame, text="Project:", font=FONT_BODY).pack(
            side=tk.LEFT, padx=5
        )

        # Get default project for the default sphere
        self.default_project = self.get_default_project(default_sphere)
        self.project_var = tk.StringVar(master=self.root, value="All Projects")
        self.project_filter = ttk.Combobox(
            filter_frame,
            textvariable=self.project_var,
            state="readonly",
            style="Filter.TCombobox",
            width=12,
        )
        self.project_filter.pack(side=tk.LEFT, padx=5)
        self.project_filter.configure(font=FONT_HEADING)
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
            style="Filter.TRadiobutton",
        ).pack(side=tk.LEFT, padx=2)

        ttk.Radiobutton(
            radio_frame,
            text="All",
            variable=self.status_filter,
            value="all",
            command=self.refresh_dropdowns,
            style="Filter.TRadiobutton",
        ).pack(side=tk.LEFT, padx=2)

        ttk.Radiobutton(
            radio_frame,
            text="Archived",
            variable=self.status_filter,
            value="archived",
            command=self.refresh_dropdowns,
            style="Filter.TRadiobutton",
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
            font=FONT_HEADING,
        )
        self.timeline_title.pack(side=tk.LEFT)

        # Timeline header
        self.timeline_header_frame = tk.Frame(
            content_frame, relief=tk.RIDGE, borderwidth=1, bg=COLOR_GRAY_BACKGROUND
        )
        self.timeline_header_frame.grid(
            row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=10, pady=(5, 2)
        )

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
        # a simple frame for timeline - no separate scrollbar
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
        """Clean up when AnalysisFrame is destroyed."""
        super().destroy()

    def create_card(self, parent, index):
        """Create a single analysis card"""
        card_frame = ttk.LabelFrame(parent, relief=tk.RIDGE, borderwidth=2, padding=10)
        frame_bg = get_frame_background()

        # Col 0: all interactive/informational widgets — sized to natural width,
        # never compressed. Col 1: pie chart only — clips first on narrow windows
        # because both columns use weight=0 (default) and Tkinter overflows right.

        # Row 0, col 0: date range dropdown
        range_var = tk.StringVar(master=self.root, value=self.card_ranges[index])
        range_dropdown = ttk.Combobox(
            card_frame,
            textvariable=range_var,
            values=self.date_ranges,
            state="readonly",
            width=15,
        )
        range_dropdown.grid(row=0, column=0, pady=5, padx=(8, 0), sticky="W")
        range_dropdown.bind(
            "<<ComboboxSelected>>",
            lambda e, card_index=index: self.on_range_changed(
                card_index, range_var.get()
            ),
        )

        # Row 1, col 0: active time — green box, auto-width, black text
        active_label = tk.Label(
            card_frame,
            text="Active: --",
            bg=COLOR_TRAY_ACTIVE,
            fg="black",
            font=FONT_TIMER_SMALL,
            relief=tk.SOLID,
            borderwidth=1,
            padx=8,
            pady=4,
            anchor="center",
        )
        active_label.grid(row=1, column=0, pady=(5, 2), padx=(8, 0), sticky="W")

        # Row 2, col 0: break/idle time — amber box, auto-width, black text
        break_label = tk.Label(
            card_frame,
            text="Break: --",
            bg=COLOR_TRAY_BREAK,
            fg="black",
            font=FONT_TIMER_SMALL,
            relief=tk.SOLID,
            borderwidth=1,
            padx=8,
            pady=4,
            anchor="center",
        )
        break_label.grid(row=2, column=0, pady=(2, 5), padx=(8, 0), sticky="W")

        # Row 3, col 0: Show Timeline button
        select_btn = ttk.Button(
            card_frame,
            text="Show Timeline",
            command=lambda card_index=index: self.select_card(card_index),
        )
        select_btn.grid(row=3, column=0, pady=10, padx=(8, 0), sticky="W")

        # Col 1, rows 0-3: pie chart — active (green) vs break/idle (amber)
        pie_canvas = tk.Canvas(
            card_frame,
            width=PIE_CHART_SIZE,
            height=PIE_CHART_SIZE,
            bg=frame_bg,
            highlightthickness=0,
        )
        pie_canvas.grid(row=0, column=1, rowspan=5, padx=(8, 8), sticky="NS")

        # Col 1 expands to fill remaining card width so pie floats centered
        card_frame.columnconfigure(1, weight=1)

        # Store references
        card_frame.range_var = range_var
        card_frame.pie_canvas = pie_canvas
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
        self.selected_card = card_index
        self.update_timeline()
        self.timeline_title.config(text=f"Timeline: {self.card_ranges[card_index]}")

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

            # Filter projects by sphere and status
            for project_name, data in self.tracker.settings.get("projects", {}).items():
                # Skip if not in selected sphere
                if data.get("sphere") != sphere:
                    continue

                is_active = data.get("active", True)

                # Determine if project should be included based on filter status
                if filter_status == "active" and is_active:
                    projects.append(project_name)
                elif filter_status == "archived":
                    # Show inactive projects if sphere is active, or all projects if sphere inactive
                    if (sphere_is_active and not is_active) or not sphere_is_active:
                        projects.append(project_name)
                elif filter_status == "all":
                    projects.append(project_name)

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
        """Handle filter changes by updating dependent filters and refreshing display."""
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
                if is_active:
                    spheres.append(sphere)
            elif filter_status == "archived":
                spheres.append(sphere)
            elif filter_status == "all":
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
        """Refresh all cards and timeline display after filter or data changes.

        Coordinates full UI refresh when filters change or data is modified.
        Updates all three summary cards (Active, Break, Idle) and the complete
        timeline period list.

        Called from filter change events:
        - on_sphere_filter_changed() - Sphere filter dropdown
        - on_project_filter_changed() - Project filter dropdown
        - on_range_changed() - Date range filter
        - on_status_changed() - Active/All/Archived toggle

        Side effects:
            - Updates all 3 card displays with recalculated totals
            - Refreshes timeline with filtered periods
            - Resets pagination to first page
            - Updates scrollable area

        Note:
            Always updates cards before timeline to ensure summary
            stats are available for display.
        """
        for i in range(3):
            self.update_card(i)
        self.update_timeline()

    def get_date_range(self, range_name):
        """Convert date range string to start/end datetime objects for filtering.

        Converts user-friendly range names ("Today", "Last 7 Days") into precise
        datetime boundaries for filtering timeline data. All times normalized to
        midnight (00:00:00) for consistent day-based filtering.

        Called from 4 key locations:
        - calculate_totals() - Time aggregation filtering
        - get_timeline_data() - Timeline period filtering
        - export_to_csv() - CSV export date filtering
        - get_date_range_for_filter() - Test compatibility wrapper

        Supported range names:
        - "Today" - Current day (midnight to midnight+1)
        - "Yesterday" - Previous day
        - "Last 7 Days" - Rolling 7-day window ending today
        - "Last 14 Days", "Last 30 Days" - Rolling windows
        - "This Week (Mon-Sun)" - Current Monday through next Monday
        - "Last Week (Mon-Sun)" - Previous Monday through Monday
        - "This Month" - 1st of month through 1st of next month
        - "Last Month" - 1st of previous month through 1st of current month
        - "Custom: YYYY-MM-DD" - Specific single day
        - "All Time" - Extremely wide range (2000-2100)

        Args:
            range_name: User-friendly date range string

        Returns:
            Tuple of (start_datetime, end_datetime) normalized to midnight.
            End datetime is exclusive (represents start of next period).

        Note:
            Invalid custom dates fall back to "Today" range.
            Week ranges use Monday as first day of week.
        """
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
        """Calculate total active and break time for a date range.

        Sums up all active periods and break/idle periods that fall within the
        specified date range and match current filter settings (sphere, project).

        Args:
            range_name: Name of the date range (e.g., "Last 7 Days", "This Month", "All Time")

        Returns:
            tuple: (total_active_seconds, total_break_seconds) as float values

        Note:
            - Idle periods with end timestamps are counted as break time
            - Applies current sphere_filter and project_filter selections
            - For multi-project periods, checks if any project matches the filter
        """
        start_date, end_date = self.get_date_range(range_name)
        all_data = self.tracker.load_data()

        total_active = 0
        total_break = 0

        sphere_filter = self.sphere_var.get()
        project_filter = self.project_var.get()

        for _, session_data in all_data.items():
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

            # Determine whether any active period in this session matches the project filter.
            # Break/idle totals are session-contextual: only counted when the session has at
            # least one active period matching the current project filter.
            # If the session has NO active periods, break/idle are counted regardless.
            active_periods = session_data.get("active", [])
            if project_filter == "All Projects" or not active_periods:
                session_has_matching_project = True
            else:
                session_has_matching_project = any(
                    period.get("project") == project_filter
                    or any(
                        p.get("name") == project_filter
                        for p in period.get("projects", [])
                    )
                    for period in active_periods
                )

            # Calculate active time
            for period in session_data.get("active", []):
                if project_filter == "All Projects":
                    total_active += period.get("duration", 0)
                    continue

                # Single-project period: direct "project" field matches filter
                period_project = period.get("project", "")
                if period_project == project_filter:
                    total_active += period.get("duration", 0)
                    continue

                # Multi-project period: add only this project's allocated duration
                for project_dict in period.get("projects", []):
                    if project_dict.get("name") == project_filter:
                        total_active += project_dict.get("duration", 0)
                        break

            # Calculate break time (only for sessions with at least one matching active period)
            if session_has_matching_project:
                for period in session_data.get("breaks", []):
                    total_break += period.get("duration", 0)

                # Calculate idle time (only for sessions with at least one matching active period)
                for period in session_data.get("idle_periods", []):
                    if period.get("end_timestamp"):
                        total_break += period.get("duration", 0)

        return total_active, total_break

    def format_duration(self, seconds):
        """Format duration in seconds to human-readable string with intelligent rounding.

        Converts seconds into a compact human-readable format:
        - Hours + minutes when >= 1 hour ("2h 15m")
        - Minutes + seconds when >= 1 minute ("15m 30s")
        - Seconds only when < 1 minute ("45s")

        Called from 9+ locations across the UI:
        - Card displays (active/break/idle labels)
        - Timeline period duration display
        - CSV export duration columns
        - Total duration summaries

        Args:
            seconds: Duration in seconds (can be float or int)

        Returns:
            Formatted string (e.g., "2h 15m", "30m 5s", "45s")

        Note:
            Intelligent rounding drops least significant unit for readability.
            Hours display omits seconds, minutes display omits milliseconds.
        """
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
        """Convert 24-hour time string to 12-hour format with AM/PM.

        Formats time strings for user-friendly timeline display.
        Converts from 24-hour format ("14:30:00") to 12-hour format ("02:30 PM").
        Times are displayed in local system timezone (as originally captured).

        Called from:
        - render_timeline() - Timeline period start time display
        - create_timeline_period() - Period row time labels

        Args:
            time_str: Time string in 24-hour format ("HH:MM:SS")

        Returns:
            Time string in 12-hour format ("HH:MM AM/PM")
            Returns original string if parsing fails

        Note:
            Gracefully handles malformed input by returning original string.
            Primarily used for user-facing time displays in timeline.
            Does not perform timezone conversion - displays times as stored.
        """
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
        draw_pie_chart(card.pie_canvas, active_time, break_time)

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

        for _, session_data in all_data.items():
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
            session_comments_dict = session_data.get("session_comments", {})
            session_active_comments = session_comments_dict.get("active_notes", "")
            break_notes = session_comments_dict.get("break_notes", "")
            idle_notes = session_comments_dict.get("idle_notes", "")
            session_notes = session_comments_dict.get("session_notes", "")

            # Determine whether any active period in this session matches the project filter.
            # Break/idle periods are session-contextual: they are only shown when the session
            # contains at least one active period that matches the current project filter.
            # If the session has NO active periods, break/idle are shown regardless (no project
            # to filter by — e.g. a session that consists only of breaks or idle time).
            active_periods = session_data.get("active", [])
            if project_filter == "All Projects" or not active_periods:
                session_has_matching_project = True
            else:
                session_has_matching_project = any(
                    period.get("project") == project_filter
                    or any(
                        p.get("name") == project_filter
                        for p in period.get("projects", [])
                    )
                    for period in active_periods
                )

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
                # Skip break periods if no active period in this session matches the project filter
                if not session_has_matching_project:
                    continue

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
                        "session_break_idle_comments": break_notes,  # Show break notes on break periods
                        "session_notes": session_notes,
                    }
                )

            # Add idle periods
            for period in session_data.get("idle_periods", []):
                # Skip idle periods if no active period in this session matches the project filter
                if not session_has_matching_project:
                    continue

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
                            "session_break_idle_comments": idle_notes,  # Show idle notes on idle periods
                            "session_notes": session_notes,
                        }
                    )

        # Sort by date and start time
        timeline_data.sort(key=lambda x: (x["date"], x["period_start"]))

        return timeline_data

    def load_more_periods(self):
        """Load the next batch of timeline periods using pagination.

        Implements incremental loading to prevent UI lag with large datasets.
        Loads 50 periods at a time from timeline_data_all (set by update_timeline).

        Batch calculation:
        - start_idx = periods_loaded (tracks how many shown so far)
        - end_idx = min(start_idx + 50, total_periods)
        - Renders periods[start_idx:end_idx]

        After rendering batch:
        - If more periods exist: Shows "Load X More (Y of Z shown)" button
        - If all loaded and >50 total: Shows "All X periods loaded" message
        - If ≤50 total: No message (all fit on first page)

        Side effects:
            - Destroys existing load_more_button if present
            - Calls _render_timeline_period() for each period in batch
            - Increments self.periods_loaded by batch size
            - Creates new load_more_button if more periods remain
            - Adds "all loaded" message if this was the final batch

        Called by:
            - update_timeline() for first page load
            - Load More button click for subsequent pages

        Note:
            Uses self.periods_per_page = 50 as batch size. This balance was
            chosen to minimize initial load time while showing meaningful data.
        """
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
        for period_index, period in enumerate(periods_to_render, start=start_idx):
            self._render_timeline_period(period, period_index)

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
                    font=FONT_NORMAL_ITALIC,
                ).pack()

    def _render_timeline_period(self, period, row_index):
        """Render a single period row in the timeline

        Args:
            period: Period dict with timeline data
            row_index: Row index for grid placement
        """
        # Color code based on type
        if period["type"] == "Active":
            bg_color = COLOR_ACTIVE_LIGHT_GREEN
        else:  # Break or Idle
            bg_color = COLOR_BREAK_LIGHT_ORANGE

        row_frame = tk.Frame(self.timeline_frame, bg=bg_color)
        row_frame.grid(row=row_index, column=0, sticky=(tk.W, tk.E), pady=1)

        # NOTE: Removed individual mousewheel binding on row_frame
        # ScrollableFrame's bind_all handler will handle scrolling automatically
        # Adding bindings here was causing the handler to stop working after
        # multiple update_timeline() calls

        # Configure row_frame columns for grid layout
        for column_index in range(14):  # 14 columns total
            if column_index == 13:  # Session Notes (last column) expands
                row_frame.columnconfigure(column_index, weight=1)
            else:
                row_frame.columnconfigure(column_index, weight=0)

        # Create label helper function
        col_idx = 0  # Track current column index

        def add_column(text, width, wraplength=0, expand=False, use_text_widget=False):
            """Add a column to the timeline row using Label or Text widget

            Args:
                text: Text to display
                width: Width in characters
                wraplength: Pixel width for text wrapping (0 = no wrap) - only for Label
                expand: Whether to expand to fill remaining space
                use_text_widget: Use Text widget instead of Label (for better wrapping)
            """
            nonlocal col_idx

            if use_text_widget:
                # Use Text widget for better text wrapping with TRUE dynamic height
                txt = tk.Text(
                    row_frame,
                    width=width,
                    height=1,  # Temporary height - will be updated after measuring wrapped content
                    wrap=tk.WORD,
                    bg=bg_color,
                    font=FONT_EXTRA_SMALL,
                    relief=tk.FLAT,
                    state=tk.NORMAL,
                    cursor="arrow",  # Use arrow cursor instead of text cursor for read-only widget
                )
                txt.insert("1.0", text)

                # Grid the widget FIRST so it knows its actual width for wrapping
                if expand:
                    txt.grid(row=0, column=col_idx, sticky=(tk.W, tk.E))
                else:
                    txt.grid(row=0, column=col_idx, sticky=tk.W)

                # Update to force wrap calculation
                txt.update_idletasks()

                # TRUE dynamic height: Use count("displaylines") to get ACTUAL wrapped line count
                # (not an estimation formula - this is exact!)
                display_lines_tuple = txt.count("1.0", "end", "displaylines")
                actual_lines = display_lines_tuple[0] if display_lines_tuple else 1

                # Set height to exact wrapped line count (cap at 15 for extremely long text)
                txt.config(height=min(15, max(1, actual_lines)))

                txt.config(state=tk.DISABLED)  # Make read-only

                # NOTE: ScrollableFrame's bind_all handles mousewheel - no widget-specific binding needed
                col_idx += 1
            else:
                lbl = tk.Label(
                    row_frame,
                    text=text,
                    width=width,
                    anchor="w",
                    padx=3,
                    bg=bg_color,
                    font=FONT_EXTRA_SMALL,
                    wraplength=wraplength,
                    justify="left",
                )
                if expand:
                    lbl.grid(row=0, column=col_idx, sticky=(tk.W, tk.E))
                else:
                    lbl.grid(row=0, column=col_idx, sticky=tk.W)
                # NOTE: Removed mousewheel binding - ScrollableFrame handles it
                col_idx += 1

        # Render all columns with proper widths using grid layout
        add_column(period["date"], 10)
        add_column(self.format_time_12hr(period["period_start"]), 9)
        add_column(self.format_duration(period["duration"]), 8)
        add_column(period.get("sphere", ""), 12)
        add_column("✓" if period.get("sphere_active", True) else "", 5)
        add_column("✓" if period.get("project_active", True) else "", 5)
        add_column(period["type"], 7)
        add_column(period["primary_project"], 15)
        add_column(period["primary_comment"], 21, use_text_widget=True)
        add_column(period["secondary_project"], 15)
        add_column(period["secondary_comment"], 21, use_text_widget=True)
        add_column(period["session_active_comments"], 21, use_text_widget=True)
        add_column(period["session_break_idle_comments"], 21, use_text_widget=True)
        add_column(period["session_notes"], 21, use_text_widget=True, expand=True)

    def update_timeline(self):
        """Refresh the entire timeline display with pagination and sorting.

        Main orchestrator for timeline updates. This method:
        1. Clears existing timeline widgets (preserves frame for ScrollableFrame)
        2. Gets all timeline data for selected date range using get_timeline_data()
        3. Sorts periods by current sort column and direction
        4. Resets pagination to first page (50 periods)
        5. Loads first batch via load_more_periods()
        6. Updates frozen timeline header
        7. Forces canvas scrollregion recalculation and resets scroll position

        Called by:
        - Filter changes (sphere, project, status, date range)
        - Card selection changes
        - Sort column clicks
        - Initial timeline creation

        Side effects:
            - Destroys all child widgets in timeline_frame
            - Stores full sorted dataset in self.timeline_data_all
            - Resets self.periods_loaded to 0
            - Calls load_more_periods() to render first 50 rows
            - Updates timeline header with sort indicators
            - Reconfigures canvas scrollregion based on content
            - Resets scroll position to top (yview_moveto(0))

        CRITICAL: This method clears children, not the frame itself, to avoid
        breaking ScrollableFrame's canvas reference. After clearing, forces
        geometry updates and scrollregion recalculation for proper rendering.
        """
        if not hasattr(self, "timeline_frame") or self.timeline_frame is None:
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
        for column_index in range(14):  # 14 columns total
            if column_index == 13:  # Session Notes (last column) expands
                self.timeline_header_frame.columnconfigure(column_index, weight=1)
            else:
                self.timeline_header_frame.columnconfigure(column_index, weight=0)

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
                font=FONT_EXTRA_SMALL,
                width=width,
                anchor="w",
                padx=3,
                pady=6,  # Vertical padding to center with two-row headers
                bg=COLOR_GRAY_BACKGROUND,
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
            container = tk.Frame(self.timeline_header_frame, bg=COLOR_GRAY_BACKGROUND)
            container.grid(row=0, column=col_idx, sticky=tk.W)

            # Top row label
            tk.Label(
                container,
                text=top_text,
                font=FONT_EXTRA_SMALL,
                width=width,
                anchor="w",
                padx=3,
                bg=COLOR_GRAY_BACKGROUND,
            ).pack()

            # Bottom row label (slightly smaller font)
            tk.Label(
                container,
                text=bottom_text,
                font=FONT_MICRO,
                width=width,
                anchor="w",
                padx=3,
                bg=COLOR_GRAY_BACKGROUND,
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
                    bg=COLOR_GRAY_BACKGROUND,
                    font=FONT_EXTRA_SMALL,
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
                    font=FONT_EXTRA_SMALL,
                    width=width,
                    anchor="w",
                    padx=3,
                    pady=6,  # Vertical padding to center with two-row headers
                    bg=COLOR_GRAY_BACKGROUND,
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
        """Export timeline data to CSV.

        Note: This method is intentionally longer than typical (280 lines)
        due to sequential processing of three period types (active, break, idle)
        with similar but not identical logic. The linear structure maintains
        clarity for the export workflow.
        """
        # Get data for selected card's range
        range_name = self.card_ranges[self.selected_card]
        start_date, end_date = self.get_date_range(range_name)
        all_data = self.tracker.load_data()

        sphere_filter = self.sphere_var.get()
        project_filter = self.project_var.get()
        status_filter = (
            self.status_filter.get()
        )  # Get the radio button filter (active/all/archived)

        # Collect all periods
        periods = []

        for _, session_data in all_data.items():
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
                # Get project name - handle both single project and projects array
                project_name = period.get("project", "")
                if not project_name and period.get("projects"):
                    # If using projects array, get the primary project name
                    for project_dict in period.get("projects", []):
                        if project_dict.get("project_primary", True):
                            project_name = project_dict.get("name", "")
                            break

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
                session_active_comments = session_comments_dict.get("active_notes", "")
                session_notes = session_comments_dict.get("session_notes", "")

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
                break_notes = session_comments_dict.get("break_notes", "")
                session_notes = session_comments_dict.get("session_notes", "")

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

            # Export idle periods
            for period in session_data.get("idle_periods", []):
                # Apply status filter for idle periods
                # Since idle actions don't have active status, filter based on sphere only
                if status_filter == "active":
                    if not sphere_active:
                        continue  # Skip if sphere is inactive
                elif status_filter == "archived":
                    if sphere_active:
                        continue  # Archived filter only shows inactive spheres for idles
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
                        if action_item.get("idle_primary", True):
                            primary_action = action_item.get("name", "")
                            primary_comment = action_item.get("comment", "")
                        else:
                            secondary_action = action_item.get("name", "")
                            secondary_comment = action_item.get("comment", "")

                # Get session-level comments
                session_comments_dict = session_data.get("session_comments", {})
                idle_notes = session_comments_dict.get("idle_notes", "")
                session_notes = session_comments_dict.get("session_notes", "")

                periods.append(
                    {
                        "Date": session_data.get("date"),
                        "Start": period.get("start", ""),
                        "Duration": self.format_duration(period.get("duration", 0)),
                        "Sphere": session_sphere,
                        "Sphere Active": "Yes" if sphere_active else "No",
                        "Project Active": "N/A",
                        "Type": "Idle",
                        "Primary Action": primary_action,
                        "Primary Comment": primary_comment,
                        "Secondary Action": secondary_action,
                        "Secondary Comment": secondary_comment,
                        "Active Comments": "",
                        "Break Comments": idle_notes,
                        "Session Notes": session_notes,
                    }
                )

        if not periods:
            messagebox.showinfo("No Data", "No data to export for selected filters")
            return

        # Ask user for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"Time_Aligned_{range_name.replace(' ', '_')}.csv",
        )

        if not filename:
            return

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

            messagebox.showinfo(
                "Success", f"Exported {len(periods)} entries to {filename}"
            )

        except Exception as error:
            messagebox.showerror("Error", f"Failed to export CSV: {error}")

    def open_latest_session(self):
        """Open session view from analysis frame"""
        # Open session view with flag indicating we came from analysis
        self.tracker.open_session_view(from_analysis=True)
