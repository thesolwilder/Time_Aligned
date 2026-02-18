"""
Completion Frame - Displayed when a session ends.
Allows user to tag actions for active time, breaks, and idle periods.
"""

import json
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from tkinter import messagebox
import os
import subprocess
import shutil
import datetime as dt

from src.ui_helpers import get_frame_background

from src.constants import (
    DEFAULT_BACKUP_FOLDER,
    FONT_TITLE,
    FONT_HEADING,
    FONT_BODY,
    FONT_NORMAL,
    FONT_NORMAL_BOLD,
    FONT_NORMAL_ITALIC,
    COLOR_LINK_BLUE,
    FONT_LINK,
)


def disable_combobox_scroll(combobox):
    """Disable mousewheel scrolling on a combobox to prevent accidental value changes"""
    combobox.bind("<MouseWheel>", lambda e: "break")


class CompletionFrame(ttk.Frame):
    def __init__(self, parent, tracker, session_name):
        """
        Initialize the completion frame.

        Args:
            parent: The parent widget (root window)
            tracker: Reference to TimeTracker instance
            session_name: Name of the session to load
        """
        super().__init__(parent, padding="10")
        self.tracker = tracker

        # If no session_name provided, get the most recent session
        if session_name is None:
            all_data = self.tracker.load_data()
            if all_data:
                # Get most recent session (sessions are named with timestamps)
                session_name = max(all_data.keys())
            else:
                # No sessions available
                session_name = None

        self.session_name = session_name

        # Load session data from JSON
        all_data = self.tracker.load_data()
        if session_name and session_name in all_data:
            loaded_data = all_data[session_name]
            self.session_start_timestamp = loaded_data.get("start_timestamp", 0)
            self.session_end_timestamp = loaded_data.get("end_timestamp", 0)
            self.session_duration = loaded_data.get("total_duration", 0)
            # Store session sphere from saved data
            self.session_sphere = loaded_data.get("sphere", None)

            # Build session_data dict for compatibility with existing code
            self.session_data = {
                "session_name": session_name,
                "total_elapsed": loaded_data.get("total_duration", 0),
                "active_time": loaded_data.get("active_duration", 0),
                "break_time": loaded_data.get("break_duration", 0),
            }

            # Load session comments if they exist
            self.session_comments = loaded_data.get("session_comments", {})
        else:
            # Fallback for missing session
            self.session_start_timestamp = 0
            self.session_end_timestamp = 0
            self.session_duration = 0
            self.session_sphere = None
            self.session_data = {
                "session_name": session_name,
                "total_elapsed": 0,
                "active_time": 0,
                "break_time": 0,
            }
            self.session_comments = {}
        self.text_boxes = []  # Store references to text boxes for each period
        # Store references to project/break action dropdowns for updating when sphere changes
        self.project_menus = []
        self.break_action_menus = []  # Store references to break action dropdowns
        self.idle_action_menus = []  # Store references to idle action dropdowns

        # Secondary dropdowns and toggle buttons
        self.secondary_menus = (
            []
        )  # Store all secondary dropdown references (projects and breaks)
        self.toggle_buttons = []  # Store toggle button references (+ / -)
        self.secondary_text_boxes = []
        self.percentage_spinboxes = []  # Store percentage spinbox references
        self.secondary_percentage_labels = (
            []
        )  # Store secondary percentage label references

        self.create_widgets()

    def create_widgets(self):
        """Create all UI elements for the completion frame"""
        self.current_row = 0

        # Navigation links at top
        self._create_navigation_links()

        # Title and sphere selection
        self._title_and_sphere()

        # display date, start time, end time and duration
        self._session_info_display()

        # change project and break/idle actions
        self.change_defaults_for_session()

        # separator
        self._add_separator()

        # Display durations
        self._create_duration_display()

        # Separator
        self._add_separator()

        # Timeline of all periods
        self._create_timeline()

        # Separator
        self._add_separator()

        # Action tags section
        self._create_session_notes()

        # Buttons
        self._create_buttons()

    def _add_separator(self):
        """Add a horizontal separator and increment row counter"""
        ttk.Separator(self, orient="horizontal").grid(
            row=self.current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15
        )
        self.current_row += 1

    def _create_navigation_links(self):
        """Create navigation links at top of frame"""
        nav_frame = ttk.Frame(self)
        nav_frame.grid(
            row=self.current_row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        self.current_row += 1

        # Get background color to match frame
        frame_bg = get_frame_background()

        # Back to Tracker link
        back_link = tk.Label(
            nav_frame,
            text="← Back to Tracker",
            fg=COLOR_LINK_BLUE,
            bg=frame_bg,
            cursor="hand2",
            font=FONT_LINK,
        )
        back_link.pack(side=tk.LEFT, padx=(0, 15))
        back_link.bind("<Button-1>", lambda e: self.tracker.show_main_frame())

        # Analysis link
        analysis_link = tk.Label(
            nav_frame,
            text="Analysis",
            fg=COLOR_LINK_BLUE,
            bg=frame_bg,
            cursor="hand2",
            font=FONT_LINK,
        )
        analysis_link.pack(side=tk.LEFT, padx=(0, 15))
        analysis_link.bind("<Button-1>", lambda e: self.tracker.open_analysis())

    # title and sphere selection method
    def _title_and_sphere(self):
        # Create a frame to hold all time labels in a single row
        time_frame = ttk.Frame(self)
        time_frame.grid(
            row=self.current_row, column=0, columnspan=2, sticky=tk.W, pady=5
        )
        self.current_row += 1
        active_spheres, default_sphere = self.tracker.get_active_spheres()

        # If session has a sphere (even if inactive), include it in options
        sphere_options = list(active_spheres)
        if self.session_sphere and self.session_sphere not in sphere_options:
            # Add inactive session sphere to options so historical sessions display correctly
            sphere_options.append(self.session_sphere)
        sphere_options.append("Add New Sphere...")

        # Set initial value - prioritize session sphere (even if inactive) over default
        if self.session_sphere:
            initial_value = self.session_sphere
        elif default_sphere and default_sphere in active_spheres:
            initial_value = default_sphere
        else:
            initial_value = active_spheres[0] if active_spheres else ""
        self.selected_sphere = initial_value

        self.sphere_menu = ttk.Combobox(
            time_frame,
            values=sphere_options,
            justify="center",
            state="readonly",
            width=10,
            font=FONT_TITLE,
        )
        self.sphere_menu.set(initial_value)
        disable_combobox_scroll(self.sphere_menu)
        self.sphere_menu.grid(row=0, column=0, sticky=tk.W, padx=5, pady=10)

        # Bind event to handle selection
        self.sphere_menu.bind("<<ComboboxSelected>>", self._on_sphere_selected)

        # Title
        ttk.Label(time_frame, text="Session Complete", font=FONT_TITLE).grid(
            row=0, column=1, pady=10, sticky=tk.W, padx=5
        )

    def change_defaults_for_session(self):
        """Create default project and break/idle action dropdown selectors.

        Displays two dropdown menus allowing user to set defaults for the session:
        - Default Project: Used for active periods (pre-filled with first project from session)
        - Default Break/Idle Action: Used for break/idle periods

        Both dropdowns support inline creation via "Add New..." option that enables
        editing mode with Enter/FocusOut binding for save/cancel.

        Smart initialization:
        - Prioritizes first project actually used in session over settings default
        - Scans session active periods to find first project assignment
        - Falls back to settings default if no project used yet

        Side effects:
            - Creates default_container frame at current_row
            - Creates default_project_menu combobox with inline creation support
            - Creates default_action_menu combobox with inline creation support
            - Binds <<ComboboxSelected>> to _on_project_selected and _on_break_action_selected
            - Disables mousewheel scroll on both dropdowns
            - Increments current_row for next section

        Note:
            Inline creation handlers (_save_new_project, _save_new_break_action) update
            all dependent dropdowns to maintain consistency across UI.
        """
        active_projects, default_project = self._get_sphere_projects()
        active_projects = active_projects + ["Add New Project..."]

        # For non-active periods (break and idle), project dropdown with break actions
        break_actions, default_break_action = self.tracker.get_active_break_actions()
        break_actions = break_actions + ["Add New Break Action..."]

        default_container = ttk.Frame(self)
        default_container.grid(
            row=self.current_row, column=0, columnspan=2, sticky=tk.W, pady=5
        )
        self.current_row += 1

        ttk.Label(default_container, text="Default Project:").grid(
            row=0, column=0, sticky=tk.W, padx=5
        )
        self.default_project_menu = ttk.Combobox(
            default_container, values=active_projects, state="readonly", width=20
        )
        self.default_project_menu.grid(row=0, column=1, sticky=tk.W, padx=5)

        # Determine initial value - prioritize first project used in session over default
        initial_project = default_project
        all_data = self.tracker.load_data()
        if self.session_name in all_data:
            session = all_data[self.session_name]
            # Get first project used in this session
            for period in session.get("active", []):
                if period.get("project"):
                    initial_project = period.get("project")
                    break
                # Check projects array
                for project_item in period.get("projects", []):
                    if project_item.get("project_primary", True):
                        initial_project = project_item.get("name", "")
                        break
                if initial_project != default_project:
                    break

        if initial_project:
            self.default_project_menu.set(initial_project)
        disable_combobox_scroll(self.default_project_menu)
        ttk.Label(default_container, text="Default Break/Idle Action:").grid(
            row=0, column=2, sticky=tk.W, padx=5
        )
        self.default_action_menu = ttk.Combobox(
            default_container, values=break_actions, state="readonly", width=20
        )
        self.default_action_menu.grid(row=0, column=3, sticky=tk.W, padx=5)
        if default_break_action and default_break_action in break_actions:
            self.default_action_menu.set(default_break_action)
        disable_combobox_scroll(self.default_action_menu)

        self.default_project_menu.bind(
            "<<ComboboxSelected>>",
            lambda e, menu=self.default_project_menu: self._on_project_selected(
                e, menu
            ),
        )
        self.default_action_menu.bind(
            "<<ComboboxSelected>>",
            lambda e, menu=self.default_action_menu: self._on_break_action_selected(
                e, menu
            ),
        )

    def _on_sphere_selected(self, _):
        """Handle sphere selection - enable editing if 'Add New Sphere...' is selected"""
        selected = self.sphere_menu.get()

        if selected == "Add New Sphere...":
            # Enable editing mode
            self.sphere_menu.config(state="normal")
            self.sphere_menu.set("")
            self.sphere_menu.focus()
            self.sphere_menu.bind("<Return>", self._save_new_sphere)
            self.sphere_menu.bind("<FocusOut>", self._cancel_new_sphere)
        else:
            # Only update selected_sphere for actual sphere names
            self.selected_sphere = selected

            # Update all project dropdowns with projects from the selected sphere
            self._update_project_dropdowns()

    def _on_date_selected(self, _):
        """Handle date selection - update session dropdown with sessions for that date"""
        selected_date = self.date_selector.get()

        if selected_date:
            # Load all sessions for the selected date
            all_data = self.tracker.load_data()
            self.sessions_for_date = [
                session_name
                for session_name in all_data.keys()
                if session_name.startswith(selected_date + "_")
            ]
            # Sort chronologically: Session 1 = oldest, highest number = most recent
            self.sessions_for_date.sort()

            # Create readable session names
            self.session_name_readable = []
            for i in range(len(self.sessions_for_date)):
                self.session_name_readable.append("Session " + str(i + 1))

            # Update session dropdown with readable names
            self.session_selector.config(values=self.session_name_readable)

            # Auto-select the most recent session for this date (highest number)
            if self.sessions_for_date:
                most_recent = "Session " + str(len(self.sessions_for_date))
                self.session_selector.set(most_recent)
                # Trigger session reload
                self._on_session_selected(None)
            else:
                self.session_selector.set("")

    def _on_session_selected(self, _):
        """Handle session selection - reload the frame with the selected session"""
        selected_readable = self.session_selector.get()

        # Map readable name ("Session 1") to actual session name
        if selected_readable and selected_readable in self.session_name_readable:
            selected_index = self.session_name_readable.index(selected_readable)
            selected_session = self.sessions_for_date[selected_index]
        else:
            return

        if selected_session != self.session_name:
            # Destroy current widgets
            for widget in self.winfo_children():
                widget.destroy()

            # Clear all widget lists
            self.text_boxes = []
            self.project_menus = []
            self.break_action_menus = []
            self.idle_action_menus = []
            self.secondary_menus = []
            self.toggle_buttons = []
            self.secondary_text_boxes = []
            self.percentage_spinboxes = []
            self.secondary_percentage_labels = []

            # Reload with new session (data will be loaded in __init__ logic)
            self.session_name = selected_session

            # Load session data from JSON
            all_data = self.tracker.load_data()
            if selected_session in all_data:
                loaded_data = all_data[selected_session]
                self.session_start_timestamp = loaded_data.get("start_timestamp", 0)
                self.session_end_timestamp = loaded_data.get("end_timestamp", 0)
                self.session_duration = loaded_data.get("total_duration", 0)
                # Store session sphere from saved data (CRITICAL for correct sphere display)
                self.session_sphere = loaded_data.get("sphere", None)

                # Load session comments if they exist (CRITICAL for populating comment fields)
                self.session_comments = loaded_data.get("session_comments", {})

                # Build session_data dict for compatibility
                self.session_data = {
                    "session_name": selected_session,
                    "total_elapsed": loaded_data.get("total_duration", 0),
                    "active_time": loaded_data.get("active_duration", 0),
                    "break_time": loaded_data.get("break_duration", 0),
                }

            # Recreate all widgets
            self.create_widgets()

    def _save_new_sphere(self, event):
        """Save inline-created sphere to settings and update UI.

        Called when user types new sphere name and presses Enter or loses focus.
        Creates new sphere in settings.json with default configuration (not default,
        active=True).

        Validation:
        - Strips whitespace from input
        - Rejects empty strings
        - Rejects "Add New Sphere..." placeholder
        - Checks for duplicate sphere names

        On success:
        - Adds sphere to settings["spheres"] with {is_default: False, active: True}
        - Saves settings.json to disk
        - Updates sphere_menu dropdown with new option
        - Sets selected_sphere to new value
        - Calls _update_project_dropdowns() to refresh project lists for new sphere
        - Returns combobox to readonly state

        On duplicate or empty:
        - Calls _cancel_new_sphere() to revert

        Side effects:
            - Modifies tracker.settings["spheres"] dict
            - Writes to settings.json file
            - Unbinds <Return> and <FocusOut> events from sphere_menu
            - Updates all project dropdowns throughout UI

        Note:
            New spheres start with no projects. User must create projects separately.
        """
        new_sphere = self.sphere_menu.get().strip()

        if new_sphere and new_sphere != "Add New Sphere...":
            spheres = self.tracker.settings["spheres"]

            if new_sphere not in spheres:
                # Add new sphere
                spheres[new_sphere] = {"is_default": False, "active": True}
                self.selected_sphere = new_sphere

                # Save to file
                try:
                    with open(self.tracker.settings_file, "w") as f:
                        json.dump(self.tracker.settings, f, indent=2)
                except Exception as error:
                    messagebox.showerror(
                        "Error", f"Failed to save sphere settings: {error}"
                    )
                    return

                # Update sphere combobox
                active_spheres, _ = self.tracker.get_active_spheres()
                sphere_options = list(active_spheres) + ["Add New Sphere..."]
                self.sphere_menu.config(values=sphere_options, state="readonly")
                self.sphere_menu.set(new_sphere)

                # Update all project dropdowns with projects from the selected sphere
                self._update_project_dropdowns()
            else:
                # Already exists
                self.sphere_menu.config(state="readonly")
                self.sphere_menu.set(new_sphere)
        else:
            # Empty input, cancel
            self._cancel_new_sphere(event)

        # Cleanup bindings
        self.sphere_menu.unbind("<Return>")
        self.sphere_menu.unbind("<FocusOut>")

    def _cancel_new_sphere(self, event):
        """Cancel inline sphere creation and restore dropdown to previous state.

        Reverts sphere_menu combobox to readonly state with sensible fallback value.
        Called when user cancels inline creation (empty input, FocusOut without save).

        Fallback priority:
        1. Default sphere (if exists and is active)
        2. First active sphere (if any exist)
        3. Empty string (if no active spheres)

        Side effects:
            - Sets sphere_menu to readonly state
            - Updates sphere_menu value to fallback
            - Unbinds <Return> and <FocusOut> events

        Note:
            Does NOT modify settings or create any data. Pure UI reversion.
        """
        active_spheres, default_sphere = self.tracker.get_active_spheres()

        fallback = (
            default_sphere
            if default_sphere in active_spheres
            else active_spheres[0] if active_spheres else ""
        )

        self.sphere_menu.config(state="readonly")
        self.sphere_menu.set(fallback)
        self.sphere_menu.unbind("<Return>")
        self.sphere_menu.unbind("<FocusOut>")

    # session data display date, start time, end time and duration
    def _session_info_display(self):
        """Create the session info display section"""

        start_time = (
            datetime.fromtimestamp(self.session_start_timestamp)
            .strftime("%I:%M %p")
            .lstrip("0")
        )
        end_time = (
            datetime.fromtimestamp(self.session_end_timestamp)
            .strftime("%I:%M %p")
            .lstrip("0")
        )

        # Create a frame to hold all time labels in a single row
        time_frame = ttk.Frame(self)
        time_frame.grid(
            row=self.current_row, column=0, columnspan=2, sticky=tk.W, pady=5
        )
        self.current_row += 1

        grid_column = 0
        # Create dropdown for selecting date first
        all_data = self.tracker.load_data()

        # Extract unique dates from session names
        dates_set = set()
        for session_name in all_data.keys():
            if "_" in session_name:
                date_part = session_name.split("_")[0]
                dates_set.add(date_part)

        date_options = sorted(list(dates_set), reverse=True)  # Most recent first
        current_date = ""
        if self.session_name and "_" in self.session_name:
            current_date = self.session_name.split("_")[0]

        ttk.Label(time_frame, text="Date:", font=FONT_HEADING).grid(
            row=0, column=grid_column, sticky=tk.W, padx=(0, 5)
        )
        grid_column += 1

        self.date_selector = ttk.Combobox(
            time_frame, values=date_options, state="readonly", width=12
        )
        self.date_selector.set(current_date)
        disable_combobox_scroll(self.date_selector)
        self.date_selector.grid(row=0, column=grid_column, sticky=tk.W, padx=(0, 10))
        self.date_selector.bind("<<ComboboxSelected>>", self._on_date_selected)
        grid_column += 1

        # Create dropdown for selecting session within the date
        self.sessions_for_date = [
            session_name
            for session_name in all_data.keys()
            if session_name.startswith(current_date + "_")
        ]

        # Sort chronologically: Session 1 = oldest, highest number = most recent
        self.sessions_for_date.sort()

        # Create readable session names (Session 1, Session 2, etc.)
        self.session_name_readable = []
        for i in range(len(self.sessions_for_date)):
            self.session_name_readable.append("Session " + str(i + 1))

        # Find current session's readable name
        current_session_readable = "Session 1"  # Default
        if self.session_name in self.sessions_for_date:
            current_index = self.sessions_for_date.index(self.session_name)
            current_session_readable = "Session " + str(current_index + 1)

        ttk.Label(time_frame, text="Session:", font=FONT_HEADING).grid(
            row=0, column=grid_column, sticky=tk.W, padx=(0, 5)
        )
        grid_column += 1

        self.session_selector = ttk.Combobox(
            time_frame, values=self.session_name_readable, state="readonly", width=20
        )
        self.session_selector.set(current_session_readable)
        disable_combobox_scroll(self.session_selector)
        self.session_selector.grid(row=0, column=grid_column, sticky=tk.W, padx=(0, 10))
        self.session_selector.bind("<<ComboboxSelected>>", self._on_session_selected)
        grid_column += 1

        # Populate start and end time based on selected session
        ttk.Label(time_frame, text=f"{start_time}", font=FONT_BODY).grid(
            row=0, column=grid_column, sticky=tk.W
        )
        grid_column += 1

        ttk.Label(
            time_frame,
            text=" - ",
            font=FONT_BODY,
        ).grid(row=0, column=grid_column, sticky=tk.W)
        grid_column += 1
        ttk.Label(
            time_frame,
            text=f"{end_time}",
            font=FONT_BODY,
        ).grid(row=0, column=grid_column, sticky=tk.W, padx=(0, 5))
        grid_column += 1

    def _create_duration_display(self):
        """Create the duration display section"""
        total_elapsed = self.session_data["total_elapsed"]
        break_time = self.session_data["break_time"]
        total_idle = self._calculate_total_idle()
        active_time = self.session_data["active_time"] - total_idle

        # Create a frame to hold all time labels in a single row
        time_frame = ttk.Frame(self)
        time_frame.grid(
            row=self.current_row, column=0, columnspan=2, sticky=tk.W, pady=5
        )
        self.current_row += 1

        grid_column = 0
        # Total time
        ttk.Label(time_frame, text="Total Time:", font=FONT_HEADING).grid(
            row=0, column=grid_column, sticky=tk.W, padx=(0, 5)
        )
        grid_column += 1
        ttk.Label(
            time_frame, text=self.tracker.format_time(total_elapsed), font=FONT_BODY
        ).grid(row=0, column=grid_column, sticky=tk.W, padx=(0, 20))
        grid_column += 1

        # Active time
        ttk.Label(
            time_frame,
            text=f"Active Time",
            font=FONT_HEADING,
        ).grid(row=0, column=grid_column, sticky=tk.W, padx=(0, 5))
        grid_column += 1

        # minus idle time italics and smaller font
        ttk.Label(
            time_frame,
            text="(minus Idle Time):",
            font=FONT_NORMAL_ITALIC,
        ).grid(row=0, column=grid_column, sticky=tk.W)

        grid_column += 1
        ttk.Label(
            time_frame, text=self.tracker.format_time(active_time), font=FONT_BODY
        ).grid(row=0, column=grid_column, sticky=tk.W, padx=(0, 20))
        grid_column += 1

        # Break time
        ttk.Label(time_frame, text="Break Time:", font=FONT_HEADING).grid(
            row=0, column=grid_column, sticky=tk.W, padx=(0, 5)
        )
        grid_column += 1
        ttk.Label(
            time_frame, text=self.tracker.format_time(break_time), font=FONT_BODY
        ).grid(row=0, column=grid_column, sticky=tk.W, padx=(0, 20))
        grid_column += 1

        # Idle time
        ttk.Label(time_frame, text="Idle Time:", font=FONT_HEADING).grid(
            row=0, column=grid_column, sticky=tk.W, padx=(0, 5)
        )
        grid_column += 1
        ttk.Label(
            time_frame, text=self.tracker.format_time(total_idle), font=FONT_BODY
        ).grid(row=0, column=grid_column, sticky=tk.W)

    def _calculate_total_idle(self):
        """Calculate total idle time from session data"""
        total_idle = 0
        all_data = self.tracker.load_data()

        if self.session_name in all_data:
            for idle_period in all_data[self.session_name]["idle_periods"]:
                if "duration" in idle_period:
                    total_idle += idle_period["duration"]

        return total_idle

    def _get_sphere_projects(self):
        """Get active projects and default project for the currently selected sphere

        Also includes projects from the current session even if they're now inactive,
        so historical sessions display correctly.
        """
        active_projects = self.tracker.get_active_projects(self.selected_sphere)
        default_project = self.tracker.get_default_project(self.selected_sphere)

        # Collect all projects used in this session (even if now inactive)
        all_data = self.tracker.load_data()
        if self.session_name in all_data:
            session = all_data[self.session_name]
            session_projects = set()

            # Collect from active periods
            for period in session.get("active", []):
                # Single project case
                if period.get("project"):
                    project_name = period.get("project", "")
                    if project_name:
                        session_projects.add(project_name)
                # Multiple projects case
                for project_item in period.get("projects", []):
                    project_name = project_item.get("name", "")
                    if project_name:
                        session_projects.add(project_name)

            # Add session projects to active_projects if they belong to this sphere and aren't already there
            for project_name in session_projects:
                if project_name not in active_projects:
                    # Check if project belongs to this sphere
                    project_data = self.tracker.settings.get("projects", {}).get(
                        project_name, {}
                    )
                    if project_data.get("sphere") == self.selected_sphere:
                        active_projects.append(project_name)

        return active_projects, default_project

    def _create_timeline(self):
        """Create chronological timeline of all active/break/idle periods"""
        # Container for timeline section
        timeline_container = ttk.Frame(self)
        timeline_container.grid(
            row=self.current_row,
            column=0,
            columnspan=2,
            pady=(5, 0),
            sticky=(tk.W, tk.E),
        )
        self.current_row += 1

        # Title
        ttk.Label(timeline_container, text="Session Timeline", font=FONT_HEADING).pack(
            anchor=tk.W, pady=(0, 5)
        )

        # Build master list of all periods
        self.all_periods = []
        all_data = self.tracker.load_data()

        if self.session_name in all_data:
            session = all_data[self.session_name]

            # Add active periods
            for period in session.get("active", []):
                # Determine primary and secondary projects
                primary_project = ""
                secondary_project = ""
                comment = ""
                secondary_comment = ""
                secondary_percentage = 50  # Default percentage

                if period.get("project"):
                    # Single project case - key is "project"
                    primary_project = period.get("project", "")
                    comment = period.get("comment", "")
                else:
                    # Multiple projects case - key is "projects" (list)
                    for project_item in period.get("projects", []):
                        if project_item.get("project_primary", True):
                            primary_project = project_item.get("name", "")
                            comment = project_item.get("comment", "")
                        else:
                            secondary_project = project_item.get("name", "")
                            secondary_comment = project_item.get("comment", "")
                            secondary_percentage = project_item.get("percentage", 50)

                self.all_periods.append(
                    {
                        "type": "Active",
                        "start": period.get("start", ""),
                        "start_timestamp": period.get("start_timestamp", 0),
                        "end": period.get("end", ""),
                        "end_timestamp": period.get("end_timestamp", 0),
                        "duration": period.get("duration", 0),
                        "project": primary_project,
                        "comment": comment,
                        "secondary_project": secondary_project,
                        "secondary_comment": secondary_comment,
                        "secondary_percentage": secondary_percentage,
                        "screenshot_folder": period.get("screenshot_folder", ""),
                    }
                )

            # Add breaks
            for period in session.get("breaks", []):
                # Determine primary and secondary actions
                primary_action = ""
                secondary_action = ""
                comment = ""
                secondary_comment = ""
                secondary_percentage = 50  # Default percentage

                if period.get("action"):
                    # Single action case - key is "action"
                    primary_action = period.get("action", "")
                    comment = period.get("comment", "")
                else:
                    # Multiple actions case - key is "actions" (list)
                    for action_item in period.get("actions", []):
                        if action_item.get("break_primary", True):
                            primary_action = action_item.get("name", "")
                            comment = action_item.get("comment", "")
                        else:
                            secondary_action = action_item.get("name", "")
                            secondary_comment = action_item.get("comment", "")
                            secondary_percentage = action_item.get("percentage", 50)

                self.all_periods.append(
                    {
                        "type": "Break",
                        "start": period.get("start", ""),
                        "start_timestamp": period.get("start_timestamp", 0),
                        "end": period.get("end", ""),
                        "end_timestamp": period.get("end_timestamp", 0),
                        "duration": period.get("duration", 0),
                        "action": primary_action,
                        "comment": comment,
                        "secondary_action": secondary_action,
                        "secondary_comment": secondary_comment,
                        "secondary_percentage": secondary_percentage,
                        "screenshot_folder": period.get("screenshot_folder", ""),
                    }
                )

            # Add idle periods
            for period in session.get("idle_periods", []):
                # Determine primary and secondary actions
                primary_action = ""
                secondary_action = ""
                comment = ""
                secondary_comment = ""
                secondary_percentage = 50  # Default percentage

                if period.get("action"):
                    # Single action case - key is "action"
                    primary_action = period.get("action", "")
                    comment = period.get("comment", "")
                else:
                    # Multiple actions case - key is "actions" (list)
                    for action_item in period.get("actions", []):
                        if action_item.get("idle_primary", True):
                            primary_action = action_item.get("name", "")
                            comment = action_item.get("comment", "")
                        else:
                            secondary_action = action_item.get("name", "")
                            secondary_comment = action_item.get("comment", "")
                            secondary_percentage = action_item.get("percentage", 50)

                self.all_periods.append(
                    {
                        "type": "Idle",
                        "start": period.get("start", ""),
                        "start_timestamp": period.get("start_timestamp", 0),
                        "end": period.get("end", ""),
                        "end_timestamp": period.get("end_timestamp", 0),
                        "duration": period.get("duration", 0),
                        "action": primary_action,
                        "comment": comment,
                        "secondary_action": secondary_action,
                        "secondary_comment": secondary_comment,
                        "secondary_percentage": secondary_percentage,
                        "screenshot_folder": period.get("screenshot_folder", ""),
                    }
                )

        # Sort by start timestamp
        self.all_periods.sort(key=lambda x: x["start_timestamp"])

        # Display timeline directly in frame
        periods_frame = ttk.Frame(timeline_container)
        periods_frame.pack(fill="both", expand=True)

        for period_idx, period in enumerate(self.all_periods):
            timeline_column = 0

            # Extract saved values at the start for use throughout the loop
            saved_comment = period.get("comment", "")
            saved_secondary_comment = period.get("secondary_comment", "")
            saved_secondary_project = period.get("secondary_project", "")
            saved_secondary_action = period.get("secondary_action", "")
            saved_secondary_percentage = period.get("secondary_percentage", 50)

            # Determine if secondary fields should be visible
            has_secondary_data = False
            if period["type"] == "Active":
                has_secondary_data = bool(
                    saved_secondary_project or saved_secondary_comment
                )
            else:
                has_secondary_data = bool(
                    saved_secondary_action or saved_secondary_comment
                )

            # Period type with color coding
            type_label = ttk.Label(
                periods_frame,
                text=period["type"],
                font=FONT_NORMAL_BOLD,
                width=10,
            )
            type_label.grid(
                row=period_idx, column=timeline_column, sticky=tk.W, padx=5, pady=2
            )
            timeline_column += 1

            # Start time (from timestamp)
            start_time = (
                datetime.fromtimestamp(period["start_timestamp"])
                .strftime("%I:%M:%S %p")
                .lstrip("0")
                if period["start_timestamp"]
                else ""
            )
            ttk.Label(periods_frame, text=start_time, font=FONT_NORMAL).grid(
                row=period_idx, column=timeline_column, sticky=tk.W, padx=1, pady=2
            )
            timeline_column += 1

            # insert dash between start and end time
            ttk.Label(periods_frame, text="-", font=FONT_NORMAL).grid(
                row=period_idx, column=timeline_column, sticky=tk.W, padx=1, pady=2
            )
            timeline_column += 1

            # End time (from timestamp)
            end_time = (
                datetime.fromtimestamp(period["end_timestamp"])
                .strftime("%I:%M:%S %p")
                .lstrip("0")
                if period["end_timestamp"]
                else ""
            )
            ttk.Label(periods_frame, text=end_time, font=FONT_NORMAL).grid(
                row=period_idx, column=timeline_column, sticky=tk.W, padx=1, pady=2
            )
            timeline_column += 1

            # Duration
            ttk.Label(
                periods_frame,
                text=self.tracker.format_time(period["duration"]),
                font=FONT_NORMAL,
            ).grid(row=period_idx, column=timeline_column, sticky=tk.W, padx=5, pady=2)
            timeline_column += 1

            # dropdown menu for project selection
            if period["type"] == "Active":
                # Get projects for the selected sphere
                active_projects, default_project = self._get_sphere_projects()

                # Add "Add New Project..." option
                project_options = list(active_projects) + ["Add New Project..."]

                # Set initial value for project dropdown - use saved value if available
                saved_project = period.get("project", "")
                initial_value = (
                    saved_project
                    if saved_project and saved_project in active_projects
                    else (
                        default_project
                        if default_project and default_project in active_projects
                        else "Select Project"
                    )
                )

                project_menu = ttk.Combobox(
                    periods_frame,
                    values=project_options,
                    state="readonly",
                    width=15,
                )
                project_menu.set(initial_value)
                disable_combobox_scroll(project_menu)
                project_menu.grid(
                    row=period_idx, column=timeline_column, sticky=tk.W, padx=5, pady=2
                )

                # Bind selection event to handle "Add New Project..."
                project_menu.bind(
                    "<<ComboboxSelected>>",
                    lambda e, menu=project_menu: self._on_project_selected(e, menu),
                )

                # Store reference to update later when sphere changes
                self.project_menus.append(project_menu)
                timeline_column += 1

            else:
                # For non-active periods (break and idle), project dropdown with break actions
                break_actions, default_break_action = (
                    self.tracker.get_active_break_actions()
                )

                # Add "Add New Break Action..." option
                break_action_options = list(break_actions) + ["Add New Break Action..."]

                # Set initial value - use saved action if available
                saved_action = period.get("action", "")
                initial_value = (
                    saved_action
                    if saved_action and saved_action in break_actions
                    else (
                        default_break_action
                        if default_break_action in break_actions
                        else "Select Break Action"
                    )
                )

                break_action_menu = ttk.Combobox(
                    periods_frame,
                    values=break_action_options,
                    state="readonly",
                    width=15,
                )
                break_action_menu.set(initial_value)
                disable_combobox_scroll(break_action_menu)
                break_action_menu.grid(
                    row=period_idx, column=timeline_column, sticky=tk.W, padx=5, pady=2
                )

                # Bind selection event to handle "Add New Break Action..."
                break_action_menu.bind(
                    "<<ComboboxSelected>>",
                    lambda e, menu=break_action_menu: self._on_break_action_selected(
                        e, menu
                    ),
                )

                # Store reference based on period type
                if period["type"] == "Break":
                    self.break_action_menus.append(break_action_menu)
                else:  # Idle
                    self.idle_action_menus.append(break_action_menu)
                timeline_column += 1

            # First text box (always visible) - populate with saved comment
            text_box = ttk.Entry(periods_frame, width=20)
            text_box.grid(
                row=period_idx, column=timeline_column, sticky=tk.W, padx=5, pady=2
            )
            if saved_comment:
                text_box.insert(0, saved_comment)
            self.text_boxes.append(text_box)
            timeline_column += 1

            # Add toggle button (starts as +, stays in same position)
            toggle_btn_text = "-" if has_secondary_data else "+"
            toggle_btn = ttk.Button(
                periods_frame,
                text=toggle_btn_text,
                width=3,
                command=lambda i=period_idx: self._toggle_secondary(i),
            )
            toggle_btn.grid(
                row=period_idx, column=timeline_column, sticky=tk.W, padx=2, pady=2
            )
            self.toggle_buttons.append(toggle_btn)
            timeline_column += 1

            # Secondary dropdown (hidden initially, appears after toggle button)
            if period["type"] == "Active":
                # Secondary project dropdown
                secondary_project_menu = ttk.Combobox(
                    periods_frame,
                    values=project_options,
                    state="readonly",
                    width=15,
                )
                # Set initial value - use saved secondary project if available
                if (
                    saved_secondary_project
                    and saved_secondary_project in active_projects
                ):
                    secondary_project_menu.set(saved_secondary_project)
                else:
                    secondary_project_menu.set("Select A Project")
                disable_combobox_scroll(secondary_project_menu)
                secondary_project_menu.grid(
                    row=period_idx, column=timeline_column, sticky=tk.W, padx=5, pady=2
                )
                if not has_secondary_data:
                    secondary_project_menu.grid_remove()  # Hide initially if no data

                # Bind selection event
                secondary_project_menu.bind(
                    "<<ComboboxSelected>>",
                    lambda e, menu=secondary_project_menu: self._on_project_selected(
                        e, menu
                    ),
                )

                self.secondary_menus.append(secondary_project_menu)
            else:
                # Secondary break/idle action dropdown
                secondary_action_menu = ttk.Combobox(
                    periods_frame,
                    values=break_action_options,
                    state="readonly",
                    width=15,
                )
                # Set initial value - use saved secondary action if available
                if saved_secondary_action and saved_secondary_action in break_actions:
                    secondary_action_menu.set(saved_secondary_action)
                else:
                    secondary_action_menu.set("Select An Action")
                disable_combobox_scroll(secondary_action_menu)
                secondary_action_menu.grid(
                    row=period_idx, column=timeline_column, sticky=tk.W, padx=5, pady=2
                )
                if not has_secondary_data:
                    secondary_action_menu.grid_remove()  # Hide initially if no data

                # Bind selection event
                secondary_action_menu.bind(
                    "<<ComboboxSelected>>",
                    lambda e, menu=secondary_action_menu: self._on_break_action_selected(
                        e, menu
                    ),
                )

                self.secondary_menus.append(secondary_action_menu)
            timeline_column += 1

            # Secondary text box (hidden initially, appears after secondary dropdown)
            text_box_secondary = ttk.Entry(periods_frame, width=20)
            text_box_secondary.grid(
                row=period_idx, column=timeline_column, sticky=tk.W, padx=5, pady=2
            )
            # Populate with saved secondary comment if available
            if saved_secondary_comment:
                text_box_secondary.insert(0, saved_secondary_comment)
            if not has_secondary_data:
                text_box_secondary.grid_remove()  # Hide initially if no data
            self.secondary_text_boxes.append(text_box_secondary)

            # Percentage spinbox for secondary (hidden initially)
            percentage_spinbox = ttk.Spinbox(
                periods_frame,
                values=(1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99),
                width=3,
                state="readonly",
                takefocus=0,
            )
            timeline_column += 1

            # Use saved percentage or default 50%
            percentage_spinbox.set(saved_secondary_percentage)

            # Prevent text selection highlighting - clear selection after any change
            def clear_selection(event):
                event.widget.after(1, lambda: event.widget.selection_clear())

            percentage_spinbox.bind("<<Increment>>", clear_selection)
            percentage_spinbox.bind("<<Decrement>>", clear_selection)
            percentage_spinbox.bind("<FocusIn>", clear_selection)
            percentage_spinbox.grid(
                row=period_idx, column=timeline_column, sticky=tk.W, padx=2, pady=2
            )
            if not has_secondary_data:
                percentage_spinbox.grid_remove()  # Hide initially if no data
            self.percentage_spinboxes.append(percentage_spinbox)

            timeline_column += 1

            # label
            label_secondary_percentage = ttk.Label(
                periods_frame, text="% of this period"
            )
            label_secondary_percentage.grid(
                row=period_idx, column=timeline_column, sticky=tk.W, pady=2
            )
            if not has_secondary_data:
                label_secondary_percentage.grid_remove()  # Hide initially if no data
            self.secondary_percentage_labels.append(label_secondary_percentage)
            timeline_column += 1

            # Screenshot folder button
            screenshot_folder = period.get("screenshot_folder", "")
            if screenshot_folder and os.path.exists(screenshot_folder):
                screenshot_btn = ttk.Button(
                    periods_frame,
                    text="📸",
                    width=3,
                    command=lambda folder=screenshot_folder: self._open_screenshot_folder(
                        folder
                    ),
                )
                screenshot_btn.grid(
                    row=period_idx, column=timeline_column, sticky=tk.W, padx=2, pady=2
                )
            else:
                # Empty space to maintain alignment
                ttk.Label(periods_frame, text="", width=3).grid(
                    row=period_idx, column=timeline_column, sticky=tk.W, padx=2, pady=2
                )

    def _open_screenshot_folder(self, folder_path):
        """Open the screenshot folder in file explorer"""
        try:
            if os.path.exists(folder_path):
                # Windows
                if os.name == "nt":
                    os.startfile(folder_path)
                # macOS
                elif os.sys.platform == "darwin":
                    subprocess.run(["open", folder_path])
                # Linux
                else:
                    subprocess.run(["xdg-open", folder_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open screenshot folder: {e}")

    def _toggle_secondary(self, idx):
        """Toggle between showing and hiding secondary dropdown and text box"""
        if idx < len(self.toggle_buttons):
            button = self.toggle_buttons[idx]

            if button.cget("text") == "+":
                # Show secondary widgets and change to -
                if idx < len(self.percentage_spinboxes):
                    self.percentage_spinboxes[idx].grid()
                if idx < len(self.secondary_percentage_labels):
                    self.secondary_percentage_labels[idx].grid()

                if idx < len(self.secondary_menus):
                    self.secondary_menus[idx].grid()
                    # Set placeholder text based on period type
                    if self.all_periods[idx]["type"] == "Active":
                        self.secondary_menus[idx].set("Select A Project")
                    else:
                        self.secondary_menus[idx].set("Select An Action")
                if idx < len(self.secondary_text_boxes):
                    self.secondary_text_boxes[idx].grid()
                button.config(text="−")
            else:
                # Hide secondary widgets, clear data, and change to +
                if idx < len(self.percentage_spinboxes):
                    self.percentage_spinboxes[idx].set(50)  # Reset to default
                    self.percentage_spinboxes[idx].grid_remove()

                if idx < len(self.secondary_percentage_labels):
                    self.secondary_percentage_labels[idx].grid_remove()
                if idx < len(self.secondary_menus):
                    self.secondary_menus[idx].set("")
                    self.secondary_menus[idx].grid_remove()
                if idx < len(self.secondary_text_boxes):
                    self.secondary_text_boxes[idx].delete(0, tk.END)
                    self.secondary_text_boxes[idx].grid_remove()
                button.config(text="+")

    def _on_project_selected(self, event, combobox):
        """Handle project dropdown selection, enabling inline creation if needed.

        Called on <<ComboboxSelected>> event for any project combobox. Checks if user
        selected "Add New Project..." option and switches to inline creation mode.

        Special handling for default_project_menu:
        - Updates all project dropdowns when default changes (update_all=True)
        - Ensures consistency across all period project selectors

        Inline creation mode (when "Add New Project..." selected):
        - Switches combobox to "normal" state (editable)
        - Clears placeholder text
        - Focuses combobox for immediate typing
        - Binds <Return> to _save_new_project()
        - Binds <FocusOut> to _cancel_new_project()

        Args:
            event: Tkinter event object
            combobox: The specific project combobox that fired the event

        Side effects:
            - If default_project_menu: Calls _update_project_dropdowns(update_all=True)
            - If "Add New Project..." selected:
              - Changes combobox state to normal
              - Sets focus to combobox
              - Binds inline creation event handlers

        Note:
            Inline creation saves project with current selected_sphere.
        """
        selected = combobox.get()

        # If default project menu changed, update all period project dropdowns
        if combobox == self.default_project_menu:
            self._update_project_dropdowns(True)

        if selected == "Add New Project...":
            # Enable editing mode
            combobox.config(state="normal")
            combobox.set("")
            combobox.focus()
            combobox.bind("<Return>", lambda e: self._save_new_project(e, combobox))
            combobox.bind("<FocusOut>", lambda e: self._cancel_new_project(e, combobox))

    def _save_new_project(self, event, combobox):
        """Save inline-created project to settings with current sphere association.

        Creates new project in settings.json associated with selected_sphere.
        Handles special case where combobox is default_project_menu (updates all
        dropdowns) vs period-specific project menu (updates only non-default dropdowns).

        Validation:
        - Strips whitespace from input
        - Rejects empty strings
        - Rejects "Add New Project..." placeholder
        - Checks for duplicate project names (case-sensitive)

        On success:
        - Adds project to settings["projects"] with:
          {active: True, sphere: selected_sphere, is_default: False}
        - Saves settings.json to disk
        - Updates combobox values and selection
        - Calls _update_project_dropdowns() to refresh all dependent dropdowns
          - update_all=True if default_project_menu (affects all periods)
          - update_all=False if period-specific menu (only that period's dropdowns)
        - Returns combobox to readonly state

        On duplicate or empty:
        - Calls _cancel_new_project() to revert

        Args:
            event: Tkinter event object (Return or FocusOut)
            combobox: The specific project combobox being edited

        Side effects:
            - Modifies tracker.settings["projects"] dict
            - Writes to settings.json file
            - Unbinds <Return> and <FocusOut> events
            - Updates all project dropdowns in UI

        Note:
            New projects inherit sphere from current selection, not user-specified.
        """
        new_project = combobox.get().strip()

        if new_project and new_project != "Add New Project...":
            if new_project not in self.tracker.settings["projects"]:
                # Add new project
                self.tracker.settings["projects"][new_project] = {
                    "active": True,
                    "sphere": self.selected_sphere,
                    "is_default": False,
                }

                # Save to file
                try:
                    with open(self.tracker.settings_file, "w") as f:
                        json.dump(self.tracker.settings, f, indent=2)
                except Exception as error:
                    messagebox.showerror(
                        "Error", f"Failed to save project settings: {error}"
                    )
                    return

                # Update combobox
                active_projects, _ = self._get_sphere_projects()
                project_options = list(active_projects) + ["Add New Project..."]
                combobox.config(values=project_options, state="readonly")
                combobox.set(new_project)

                # Update all dropdowns based on which combobox was used
                if combobox == self.default_project_menu:
                    # Default menu: update all period dropdowns to show new project
                    self._update_project_dropdowns(True)
                else:
                    # Period-specific menu: update only that period's dropdowns
                    self._update_project_dropdowns()
            else:
                # Already exists
                combobox.config(state="readonly")
                combobox.set(new_project)
        else:
            # Empty input, cancel
            self._cancel_new_project(event, combobox)

        # Cleanup bindings
        combobox.unbind("<Return>")
        combobox.unbind("<FocusOut>")

    def _cancel_new_project(self, event, combobox):
        """Cancel inline project creation and restore combobox to readonly state.

        Reverts project combobox to readonly with sensible fallback. Handles both
        default_project_menu and period-specific project menus.

        Fallback priority:
        1. Default project for sphere (if exists and in active projects)
        2. "Select Project" placeholder (if no suitable default)

        Args:
            event: Tkinter event object
            combobox: The project combobox to revert

        Side effects:
            - Sets combobox to readonly state
            - Updates combobox value to fallback
            - Does NOT unbind events (handled by caller)

        Note:
            Does NOT modify settings. Pure UI reversion.
        """
        active_projects, default_project = self._get_sphere_projects()

        fallback = (
            default_project
            if default_project and default_project in active_projects
            else "Select Project"
        )

        combobox.config(state="readonly")
        combobox.set(fallback)
        combobox.unbind("<Return>")
        combobox.unbind("<FocusOut>")

    def _on_break_action_selected(self, event, combobox):
        """Handle break action selection - enable editing if 'Add New Break Action...' is selected"""
        selected = combobox.get()

        # If default action menu changed, update all period break action dropdowns
        if combobox == self.default_action_menu:
            self._update_break_action_dropdowns(True)

        if selected == "Add New Break Action...":
            # Enable editing mode
            combobox.config(state="normal")
            combobox.set("")
            combobox.focus()
            combobox.bind(
                "<Return>", lambda e: self._save_new_break_action(e, combobox)
            )
            combobox.bind(
                "<FocusOut>", lambda e: self._cancel_new_break_action(e, combobox)
            )

    def _save_new_break_action(self, event, combobox):
        """Save inline-created break action to settings and update all dropdowns.

        Creates new break action in settings.json. Unlike projects, break actions are
        not sphere-specific (they're global). Handles default vs period-specific menus.

        Validation:
        - Strips whitespace from input
        - Rejects empty strings
        - Rejects "Add New Break Action..." placeholder
        - Checks for duplicate action names

        On success:
        - Adds action to settings["break_actions"] with:
          {active: True, is_default: False}
        - Saves settings.json to disk
        - Updates combobox values and selection
        - Calls _update_break_action_dropdowns():
          - update_all=True if default_action_menu
          - update_all=False if period-specific menu
        - Returns combobox to readonly state

        On duplicate or empty:
        - Calls _cancel_new_break_action() to revert

        Args:
            event: Tkinter event object (Return or FocusOut)
            combobox: The specific break action combobox being edited

        Side effects:
            - Modifies tracker.settings["break_actions"] dict
            - Writes to settings.json file
            - Unbinds <Return> and <FocusOut> events
            - Updates all break action dropdowns in UI

        Note:
            Break actions are global, not sphere-specific like projects.
        """
        new_action = combobox.get().strip()

        if new_action and new_action != "Add New Break Action...":
            if new_action not in self.tracker.settings["break_actions"]:
                # Add new break action
                self.tracker.settings["break_actions"][new_action] = {
                    "active": True,
                    "is_default": False,
                }

                # Save to file
                try:
                    with open(self.tracker.settings_file, "w") as f:
                        json.dump(self.tracker.settings, f, indent=2)
                except Exception as error:
                    messagebox.showerror(
                        "Error", f"Failed to save break action settings: {error}"
                    )
                    return

                # Update combobox
                break_actions, _ = self.tracker.get_active_break_actions()
                action_options = list(break_actions) + ["Add New Break Action..."]
                combobox.config(values=action_options, state="readonly")
                combobox.set(new_action)

                # Update all dropdowns based on which combobox was used
                if combobox == self.default_action_menu:
                    # Default menu: update all period dropdowns to show new action
                    self._update_break_action_dropdowns(True)
                else:
                    # Period-specific menu: update only that period's dropdowns
                    self._update_break_action_dropdowns()
            else:
                # Already exists
                combobox.config(state="readonly")
                combobox.set(new_action)
        else:
            # Empty input, cancel
            self._cancel_new_break_action(event, combobox)

        # Cleanup bindings
        combobox.unbind("<Return>")
        combobox.unbind("<FocusOut>")

    def _cancel_new_break_action(self, event, combobox):
        """Cancel inline break action creation and restore combobox to readonly.

        Reverts break action combobox to readonly with sensible fallback.

        Fallback priority:
        1. Default break action (if exists in active actions)
        2. "Select Break Action" placeholder (if no suitable default)

        Args:
            event: Tkinter event object
            combobox: The break action combobox to revert

        Side effects:
            - Sets combobox to readonly state
            - Updates combobox value to fallback
            - Does NOT unbind events (handled by caller)

        Note:
            Does NOT modify settings. Pure UI reversion.
        """
        break_actions, default_break_action = self.tracker.get_active_break_actions()

        fallback = (
            default_break_action
            if default_break_action in break_actions
            else "Select Break Action"
        )

        combobox.config(state="readonly")
        combobox.set(fallback)
        combobox.unbind("<Return>")
        combobox.unbind("<FocusOut>")

    def _update_project_dropdowns(self, update_all=False):
        """Update all project dropdown menus when sphere selection changes

        Args:
            update_all: If True, sets all period dropdowns to match default_project_menu selection.
                       If False (default), only updates dropdown options while preserving individual selections.
                       Set to True when default_project_menu changes to sync all periods.
        """

        # Get projects for the currently selected sphere
        active_projects, default_project = self._get_sphere_projects()

        # Add "Add New Project..." option
        project_options = list(active_projects) + ["Add New Project..."]

        # Update each primary project dropdown
        for menu in self.project_menus:
            current_selection = menu.get()
            menu["values"] = project_options

            if update_all:
                menu.set(self.default_project_menu.get())
            elif current_selection in project_options:
                menu.set(current_selection)
            elif default_project and default_project in project_options:
                menu.set(default_project)
            else:
                menu.set("Select Project")

        # Update secondary project dropdowns' options (but not their selection)
        # Check period type to handle chronologically interleaved Active/Break/Idle periods
        for i, period in enumerate(self.all_periods):
            if i < len(self.secondary_menus) and period["type"] == "Active":
                menu = self.secondary_menus[i]
                current_val = menu.get()
                menu["values"] = project_options
                # Keep current selection if still valid, otherwise clear
                if current_val and current_val not in project_options:
                    menu.set("")

        # get current menu for default project
        current_default_project = self.default_project_menu.get()
        # update combobox for default projects  in change default method
        self.default_project_menu.config(values=project_options)
        if current_default_project in project_options:
            self.default_project_menu.config(values=project_options)
            self.default_project_menu.set(current_default_project)

        elif default_project and default_project in project_options:
            self.default_project_menu.set(default_project)
        else:
            self.default_project_menu.set("Select Project")

    def _update_break_action_dropdowns(self, update_all=False):
        """Update all break action dropdown menus when break action selection changes

        Args:
            update_all: If True, sets all period dropdowns to match default_action_menu selection.
                       If False (default), only updates dropdown options while preserving individual selections.
                       Set to True when default_action_menu changes to sync all periods.
        """
        break_actions, default_break_action = self.tracker.get_active_break_actions()
        action_options = list(break_actions) + ["Add New Break Action..."]

        # Update both break and idle action menus
        for menu in self.break_action_menus + self.idle_action_menus:
            current_selection = menu.get()
            menu["values"] = action_options

            if update_all:
                menu.set(self.default_action_menu.get())
            elif current_selection in action_options:
                menu.set(current_selection)
            elif default_break_action and default_break_action in action_options:
                menu.set(default_break_action)
            else:
                menu.set("Select Break Action")

        # Update default action menu's options and preserve valid selection
        # Handles changes to break action availability (e.g., newly added or removed actions)
        # Falls back to default action or placeholder if current selection is no longer valid
        current_default = self.default_action_menu.get()
        self.default_action_menu.config(values=action_options)

        if current_default in action_options:
            self.default_action_menu.set(current_default)
        elif default_break_action and default_break_action in action_options:
            self.default_action_menu.set(default_break_action)
        else:
            self.default_action_menu.set("Select Break Action")

        # Update secondary break/idle action dropdowns' options (but not their selection)
        # Check period type to handle chronologically interleaved Active/Break/Idle periods
        for i, period in enumerate(self.all_periods):
            if i < len(self.secondary_menus) and period["type"] != "Active":
                menu = self.secondary_menus[i]
                current_val = menu.get()
                menu["values"] = action_options
                # Keep current selection if still valid, otherwise clear
                if current_val and current_val not in action_options:
                    menu.set("")

    def _create_session_notes(self):
        """Create the notes input section"""
        session_comments_container = ttk.Frame(self)
        session_comments_container.grid(
            row=self.current_row, column=0, columnspan=2, pady=10, sticky=tk.W
        )
        self.current_row += 1

        ttk.Label(
            session_comments_container,
            text="Session Comments:",
            font=FONT_HEADING,
        ).grid(row=0, column=0, columnspan=2, pady=10)

        # Active notes
        ttk.Label(
            session_comments_container, text="Active Notes:", font=FONT_NORMAL
        ).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.active_notes = ttk.Entry(session_comments_container, width=30)
        self.active_notes.grid(row=1, column=1, sticky=tk.W, pady=5)
        # Break notes
        ttk.Label(
            session_comments_container, text="Break Notes:", font=FONT_NORMAL
        ).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.break_notes = ttk.Entry(session_comments_container, width=30)
        self.break_notes.grid(row=2, column=1, sticky=tk.W, pady=5)

        # Idle notes
        ttk.Label(
            session_comments_container, text="Idle Notes:", font=FONT_NORMAL
        ).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.idle_notes = ttk.Entry(session_comments_container, width=30)
        self.idle_notes.grid(row=3, column=1, sticky=tk.W, pady=5)

        # Session notes
        ttk.Label(
            session_comments_container, text="Session Notes:", font=FONT_NORMAL
        ).grid(row=12, column=0, sticky=(tk.W, tk.N), pady=5)
        self.session_notes_text = tk.Text(
            session_comments_container, width=30, height=4, font=FONT_NORMAL
        )
        self.session_notes_text.grid(row=12, column=1, sticky=tk.W, pady=5)

        # Populate comment fields with existing session comments
        self._populate_session_comments()

    def _populate_session_comments(self):
        """Populate the comment fields with existing session comments"""
        if hasattr(self, "session_comments") and self.session_comments:
            # Populate active notes
            active_notes = self.session_comments.get("active_notes", "")
            if active_notes:
                self.active_notes.delete(0, tk.END)
                self.active_notes.insert(0, active_notes)

            # Populate break notes
            break_notes = self.session_comments.get("break_notes", "")
            if break_notes:
                self.break_notes.delete(0, tk.END)
                self.break_notes.insert(0, break_notes)

            # Populate idle notes
            idle_notes = self.session_comments.get("idle_notes", "")
            if idle_notes:
                self.idle_notes.delete(0, tk.END)
                self.idle_notes.insert(0, idle_notes)

            # Populate session notes
            session_notes = self.session_comments.get("session_notes", "")
            if session_notes:
                self.session_notes_text.delete("1.0", tk.END)
                self.session_notes_text.insert("1.0", session_notes)

    def _create_buttons(self):
        """Create action buttons"""
        button_frame = ttk.Frame(self)
        button_frame.grid(
            row=self.current_row, column=0, columnspan=2, pady=20, sticky=tk.W
        )
        self.current_row += 1

        ttk.Button(
            button_frame, text="Save & Complete", command=self.save_and_close
        ).grid(row=0, column=0, padx=5)

        ttk.Button(button_frame, text="Skip", command=self.skip_and_close).grid(
            row=0, column=1, padx=5
        )

        ttk.Button(
            button_frame, text="Delete Session", command=self._delete_session
        ).grid(row=0, column=2, padx=5)

        ttk.Button(
            button_frame,
            text="Save & Go to Analysis Frame",
            command=lambda: (
                self.save_and_close(navigate=False),
                self.tracker.open_analysis(),
            ),
        ).grid(row=0, column=3, padx=5)

    def save_and_close(self, navigate=True):
        """Save action tags and return to main frame

        Args:
            navigate: If True, navigate back to previous frame. If False, just save.
        """
        all_data = self.tracker.load_data()

        if self.session_name not in all_data:
            if navigate:
                self.tracker.show_main_frame()
            return

        session = all_data[self.session_name]

        # Update sphere
        session["sphere"] = self.selected_sphere

        # Track indices for each dropdown type
        project_idx = 0
        break_action_idx = 0
        idle_action_idx = 0

        # Map each period in all_periods to its corresponding data.json entry
        for idx, period in enumerate(self.all_periods):
            period_type = period["type"]
            start_ts = period["start_timestamp"]

            # Get the primary text box value for this period
            comment = self.text_boxes[idx].get().strip()

            # Get secondary dropdown value if exists
            secondary_value = self.secondary_menus[idx].get().strip()

            # Get percentage value for secondary
            secondary_percentage = int(self.percentage_spinboxes[idx].get())

            # get the secondary text box value for this period
            comment_secondary = self.secondary_text_boxes[idx].get().strip()

            # Find and update the corresponding period in the session data
            if period_type == "Active":
                project = self.project_menus[project_idx].get()
                project_idx += 1

                # Find matching active period by timestamp
                for active_period in session.get("active", []):
                    if active_period.get("start_timestamp") == start_ts:
                        # Check if secondary dropdown has value
                        if secondary_value and secondary_value not in [
                            "Select Project",
                            "Add New Project...",
                            "Select A Project",
                        ]:
                            # Save as array with user-specified percentage split
                            total_duration = active_period.get("duration", 0)
                            primary_percentage = 100 - secondary_percentage
                            active_period["projects"] = [
                                {
                                    "name": project,
                                    "percentage": primary_percentage,
                                    "comment": comment,
                                    "duration": int(
                                        total_duration * primary_percentage / 100
                                    ),
                                    "project_primary": True,
                                },
                                {
                                    "name": secondary_value,
                                    "percentage": secondary_percentage,
                                    "comment": comment_secondary,
                                    "duration": int(
                                        total_duration * secondary_percentage / 100
                                    ),
                                    "project_primary": False,
                                },
                            ]
                            # Bidirectional format migration: remove single-project format keys
                            # when switching to projects array (prevents conflicting data)
                            active_period.pop("project", None)
                            active_period.pop("comment", None)
                            active_period.pop("comment_secondary", None)
                        elif project and project not in [
                            "Select Project",
                            "Add New Project...",
                            "Select A Project",
                        ]:
                            # Single project - save old way
                            active_period["project"] = project
                            if comment:
                                active_period["comment"] = comment
                            # Bidirectional format migration: remove projects array format
                            # when switching to single project (prevents conflicting data)
                            active_period.pop("projects", None)
                            active_period.pop("comment_secondary", None)
                        break

            elif period_type == "Break":
                break_action = self.break_action_menus[break_action_idx].get()
                break_action_idx += 1

                # Find matching break period by timestamp
                for break_period in session.get("breaks", []):
                    if break_period.get("start_timestamp") == start_ts:
                        # Check if secondary dropdown has value
                        if secondary_value and secondary_value not in [
                            "Select Break Action",
                            "Add New Break Action...",
                            "Select An Action",
                        ]:
                            # Save as array with user-specified percentage split
                            total_duration = break_period.get("duration", 0)
                            primary_percentage = 100 - secondary_percentage
                            break_period["actions"] = [
                                {
                                    "name": break_action,
                                    "percentage": primary_percentage,
                                    "duration": int(
                                        total_duration * primary_percentage / 100
                                    ),
                                    "comment": comment,
                                    "break_primary": True,
                                },
                                {
                                    "name": secondary_value,
                                    "percentage": secondary_percentage,
                                    "duration": int(
                                        total_duration * secondary_percentage / 100
                                    ),
                                    "comment": comment_secondary,
                                    "break_primary": False,
                                },
                            ]
                            # Bidirectional format migration: remove single-action format keys
                            # when switching to actions array (prevents conflicting data)
                            break_period.pop("action", None)
                            break_period.pop("comment", None)
                            break_period.pop("comment_secondary", None)
                        elif break_action and break_action not in [
                            "Select Break Action",
                            "Add New Break Action...",
                            "Select An Action",
                        ]:
                            # Single action - save old way
                            break_period["action"] = break_action
                            if comment:
                                break_period["comment"] = comment
                            # Bidirectional format migration: remove actions array format
                            # when switching to single action (prevents conflicting data)
                            break_period.pop("actions", None)
                            break_period.pop("comment_secondary", None)
                        break

            elif period_type == "Idle":
                idle_action = self.idle_action_menus[idle_action_idx].get()
                idle_action_idx += 1

                # Find matching idle period by timestamp
                for idle_period in session.get("idle_periods", []):
                    if idle_period.get("start_timestamp") == start_ts:
                        # Check if secondary dropdown has value
                        if secondary_value and secondary_value not in [
                            "Select Break Action",
                            "Add New Break Action...",
                            "Select An Action",
                        ]:
                            # Save as array with user-specified percentage split
                            total_duration = idle_period.get("duration", 0)
                            primary_percentage = 100 - secondary_percentage
                            idle_period["actions"] = [
                                {
                                    "name": idle_action,
                                    "percentage": primary_percentage,
                                    "duration": int(
                                        total_duration * primary_percentage / 100
                                    ),
                                    "comment": comment,
                                    "idle_primary": True,
                                },
                                {
                                    "name": secondary_value,
                                    "percentage": secondary_percentage,
                                    "duration": int(
                                        total_duration * secondary_percentage / 100
                                    ),
                                    "comment": comment_secondary,
                                    "idle_primary": False,
                                },
                            ]
                            # Bidirectional format migration: remove single-action format keys
                            # when switching to actions array (prevents conflicting data)
                            idle_period.pop("action", None)
                            idle_period.pop("comment", None)
                            idle_period.pop("comment_secondary", None)
                        elif idle_action and idle_action not in [
                            "Select Break Action",
                            "Add New Break Action...",
                            "Select An Action",
                        ]:
                            # Single action - save old way
                            idle_period["action"] = idle_action
                            if comment:
                                idle_period["comment"] = comment
                            # Bidirectional format migration: remove actions array format
                            # when switching to single action (prevents conflicting data)
                            idle_period.pop("actions", None)
                            idle_period.pop("comment_secondary", None)
                        break

        # Save session-level notes
        session["session_comments"] = {
            "active_notes": self.active_notes.get(),
            "break_notes": self.break_notes.get(),
            "idle_notes": self.idle_notes.get(),
            "session_notes": self.session_notes_text.get("1.0", tk.END).strip(),
        }

        # Single save operation - minimizes I/O and reduces corruption risk
        self.tracker.save_data(all_data)

        # Upload to Google Sheets if enabled
        self._upload_to_google_sheets(session)

        # Check if we should navigate
        if not navigate:
            return

        # Always navigate to main frame
        self.tracker.show_main_frame()

    def _upload_to_google_sheets(self, session_data):
        """
        Upload session data to Google Sheets if enabled

        Args:
            session_data: The session data dictionary to upload
        """
        try:
            from src.google_sheets_integration import GoogleSheetsUploader

            uploader = GoogleSheetsUploader(self.tracker.settings_file)

            if uploader.is_enabled():
                uploader.upload_session(session_data, self.session_name)
        except ImportError:
            pass
        except Exception:
            pass

    def skip_and_close(self):
        """Return to main frame, applying defaults to any incomplete data

        Applies default sphere/project/action to periods that lack assignments.
        This handles edge cases like old data created before end_session() fix,
        or data loaded from external sources.

        Note: Normally defaults are set in end_session(), but this provides
        a fallback for any incomplete data that reaches the completion frame.
        """
        all_data = self.tracker.load_data()

        if self.session_name not in all_data:
            self.tracker.show_main_frame()
            return

        session = all_data[self.session_name]

        # Get defaults using tracker's helper methods that parse JSON structure correctly
        default_sphere = self.tracker._get_default_sphere()
        default_project = self.tracker.get_default_project(default_sphere)
        _, default_break_action = self.tracker.get_active_break_actions()

        # Fallback if helpers return None
        if not default_sphere:
            default_sphere = "General"
        if not default_project:
            default_project = "General"
        if not default_break_action:
            default_break_action = "Break"
        if not session.get("sphere"):
            session["sphere"] = default_sphere

        # Apply default project to active periods without project
        for active_period in session.get("active", []):
            has_project = active_period.get("project") or active_period.get("projects")
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

        # Save if any defaults were applied
        self.tracker.save_data(all_data)

        # Navigate to main frame
        self.tracker.show_main_frame()

    def _delete_session(self):
        """Delete the current session after confirmation"""

        # Show confirmation dialog
        result = messagebox.askyesno(
            "Delete Session",
            f"Are you sure you want to delete session '{self.session_name}'?\n\nThis action cannot be undone.",
            icon="warning",
        )

        if result:
            all_data = self.tracker.load_data()

            # Safety check: Don't delete if data load failed
            if not all_data:
                messagebox.showerror(
                    "Error",
                    "Failed to load session data. Cannot delete session safely.",
                )
                return

            # Delete the session if it exists
            if self.session_name in all_data:
                # Ensure backups directory exists
                backup_dir = DEFAULT_BACKUP_FOLDER
                os.makedirs(backup_dir, exist_ok=True)

                backup_filename = f"{os.path.basename(self.tracker.data_file)}.backup_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                backup_file = os.path.join(backup_dir, backup_filename)
                try:
                    shutil.copy2(self.tracker.data_file, backup_file)
                except Exception as e:
                    messagebox.showerror(
                        "Backup Failed",
                        f"Could not create backup before deletion: {e}\n\nDeletion cancelled.",
                    )
                    return

                del all_data[self.session_name]
                self.tracker.save_data(all_data, merge=False)

                # Show success message
                messagebox.showinfo(
                    "Session Deleted",
                    f"Session '{self.session_name}' has been deleted successfully.",
                )

                # If we're in session view (from analysis), reload with next session
                if (
                    hasattr(self.tracker, "session_view_frame")
                    and self.tracker.session_view_frame == self
                ):
                    # Get the next most recent session
                    all_data = self.tracker.load_data()
                    if all_data:
                        # Reload session view with most recent session
                        self.session_name = max(all_data.keys())
                        self.destroy()

                        # Recreate session view with new session
                        session_view_parent = (
                            self.tracker.session_view_container.get_content_frame()
                        )
                        self.tracker.session_view_frame = CompletionFrame(
                            session_view_parent, self.tracker, None
                        )
                        self.tracker.session_view_frame.pack(fill="both", expand=True)
                    else:
                        # No more sessions, go back to main
                        self.tracker.show_main_frame()
                else:
                    # Return to main frame (called from end session flow)
                    self.tracker.show_main_frame()
