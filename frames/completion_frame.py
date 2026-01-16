"""
Completion Frame - Displayed when a session ends.
Allows user to tag actions for active time, breaks, and idle periods.
"""

import json
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
        self.session_start_timestamp = session_data.get("session_start_timestamp", 0)
        self.session_end_timestamp = session_data.get("session_end_timestamp", 0)
        self.session_duration = session_data.get("total_duration", 0)
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

    # title and sphere selection method
    def _title_and_sphere(self):
        # Create a frame to hold all time labels in a single row
        time_frame = ttk.Frame(self)
        time_frame.grid(
            row=self.current_row, column=0, columnspan=2, sticky=tk.W, pady=5
        )
        self.current_row += 1
        active_spheres, default_sphere = self._get_active_spheres()

        # Add "Add New Sphere..." option to the list
        sphere_options = list(active_spheres) + ["Add New Sphere..."]

        # Set initial value
        initial_value = (
            default_sphere
            if default_sphere in active_spheres
            else active_spheres[0] if active_spheres else ""
        )
        self.selected_sphere = initial_value

        self.sphere_menu = ttk.Combobox(
            time_frame,
            values=sphere_options,
            justify="center",
            state="readonly",
            width=10,
            font=("Arial", 16, "bold"),
        )
        self.sphere_menu.set(initial_value)
        self.sphere_menu.grid(row=0, column=0, sticky=tk.W, padx=5, pady=10)

        # Bind event to handle selection
        self.sphere_menu.bind("<<ComboboxSelected>>", self._on_sphere_selected)

        # Title
        ttk.Label(time_frame, text="Session Complete", font=("Arial", 16, "bold")).grid(
            row=0, column=1, pady=10, sticky=tk.W, padx=5
        )

    def change_defaults_for_session(self):
        """Change default project and break/idle actions for the session"""
        active_projects, default_project = self._get_sphere_projects()
        active_projects = active_projects + ["Add New Project..."]

        # For non-active periods (break and idle), project dropdown with break actions
        break_actions, default_break_action = self._get_break_actions()
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
        self.default_project_menu.set(default_project)
        ttk.Label(default_container, text="Default Break/Idle Action:").grid(
            row=0, column=2, sticky=tk.W, padx=5
        )
        self.default_action_menu = ttk.Combobox(
            default_container, values=break_actions, state="readonly", width=20
        )
        self.default_action_menu.grid(row=0, column=3, sticky=tk.W, padx=5)
        self.default_action_menu.set(default_break_action)

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

    def _save_new_sphere(self, event):
        """Save the new sphere to settings"""
        new_sphere = self.sphere_menu.get().strip()

        if new_sphere and new_sphere != "Add New Sphere...":
            spheres = self.tracker.settings["spheres"]

            if new_sphere not in spheres:
                # Add new sphere
                spheres[new_sphere] = {"is_default": False, "active": True}
                self.selected_sphere = new_sphere

                # Save to file
                with open(self.tracker.settings_file, "w") as f:
                    json.dump(self.tracker.settings, f, indent=2)

                # Update sphere combobox
                active_spheres, _ = self._get_active_spheres()
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
        """Cancel adding new sphere and revert to previous state"""
        active_spheres, default_sphere = self._get_active_spheres()

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
        session_date = datetime.fromtimestamp(self.session_start_timestamp).strftime(
            "%B %d, %Y"
        )
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

        col = 0
        ttk.Label(time_frame, text=f"{session_date}:", font=("Arial", 12, "bold")).grid(
            row=0, column=col, sticky=tk.W, padx=(0, 5)
        )
        col += 1
        ttk.Label(time_frame, text=f"{start_time}", font=("Arial", 12)).grid(
            row=0, column=col, sticky=tk.W
        )
        col += 1

        ttk.Label(
            time_frame,
            text=" - ",
            font=(
                "Arial",
                12,
            ),
        ).grid(row=0, column=col, sticky=tk.W)
        col += 1
        ttk.Label(
            time_frame,
            text=f"{end_time}",
            font=(
                "Arial",
                12,
            ),
        ).grid(row=0, column=col, sticky=tk.W, padx=(0, 5))
        col += 1

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

        col = 0
        # Total time
        ttk.Label(time_frame, text="Total Time:", font=("Arial", 12, "bold")).grid(
            row=0, column=col, sticky=tk.W, padx=(0, 5)
        )
        col += 1
        ttk.Label(
            time_frame, text=self.tracker.format_time(total_elapsed), font=("Arial", 12)
        ).grid(row=0, column=col, sticky=tk.W, padx=(0, 20))
        col += 1

        # Active time
        ttk.Label(
            time_frame,
            text=f"Active Time",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=col, sticky=tk.W, padx=(0, 5))
        col += 1

        # minus idle time italics and smaller font
        ttk.Label(
            time_frame,
            text="(minus Idle Time):",
            font=("Arial", 10, "italic"),
        ).grid(row=0, column=col, sticky=tk.W)

        col += 1
        ttk.Label(
            time_frame, text=self.tracker.format_time(active_time), font=("Arial", 12)
        ).grid(row=0, column=col, sticky=tk.W, padx=(0, 20))
        col += 1

        # Break time
        ttk.Label(time_frame, text="Break Time:", font=("Arial", 12, "bold")).grid(
            row=0, column=col, sticky=tk.W, padx=(0, 5)
        )
        col += 1
        ttk.Label(
            time_frame, text=self.tracker.format_time(break_time), font=("Arial", 12)
        ).grid(row=0, column=col, sticky=tk.W, padx=(0, 20))
        col += 1

        # Idle time
        ttk.Label(time_frame, text="Idle Time:", font=("Arial", 12, "bold")).grid(
            row=0, column=col, sticky=tk.W, padx=(0, 5)
        )
        col += 1
        ttk.Label(
            time_frame, text=self.tracker.format_time(total_idle), font=("Arial", 12)
        ).grid(row=0, column=col, sticky=tk.W)

    def _calculate_total_idle(self):
        """Calculate total idle time from session data"""
        total_idle = 0
        all_data = self.tracker.load_data()

        if self.session_name in all_data:
            for idle_period in all_data[self.session_name]["idle_periods"]:
                if "duration" in idle_period:
                    total_idle += idle_period["duration"]

        return total_idle

    def _get_active_spheres(self):
        """Get active spheres and default sphere"""
        active_spheres = [
            sphere
            for sphere, data in self.tracker.settings["spheres"].items()
            if data.get("active", True)
        ]

        default_sphere = next(
            (
                sphere
                for sphere, data in self.tracker.settings["spheres"].items()
                if data.get("is_default", False)
            ),
            None,
        )

        return active_spheres, default_sphere

    def _get_sphere_projects(self):
        """Get active projects and default project for the currently selected sphere"""
        active_projects = [
            proj
            for proj, data in self.tracker.settings["projects"].items()
            if data.get("active", True) and data.get("sphere") == self.selected_sphere
        ]

        default_project = next(
            (
                proj
                for proj, data in self.tracker.settings["projects"].items()
                if data.get("is_default", True)
                and data.get("sphere") == self.selected_sphere
            ),
            None,
        )

        return active_projects, default_project

    def _get_break_actions(self):
        """Get break actions for the currently selected sphere"""
        break_actions = [
            action
            for action, data in self.tracker.settings["break_actions"].items()
            if data.get("active", True)
        ]

        default_action = next(
            (
                action
                for action, data in self.tracker.settings["break_actions"].items()
                if data.get("is_default", True)
            ),
            None,
        )
        return break_actions, default_action

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
        ttk.Label(
            timeline_container, text="Session Timeline", font=("Arial", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        # Build master list of all periods
        self.all_periods = []
        all_data = self.tracker.load_data()

        if self.session_name in all_data:
            session = all_data[self.session_name]

            # Add active periods
            for period in session.get("active", []):

                self.all_periods.append(
                    {
                        "type": "Active",
                        "start": period.get("start", ""),
                        "start_timestamp": period.get("start_timestamp", 0),
                        "end": period.get("end", ""),
                        "end_timestamp": period.get("end_timestamp", 0),
                        "duration": period.get("duration", 0),
                    }
                )

            # Add breaks
            for period in session.get("breaks", []):
                self.all_periods.append(
                    {
                        "type": "Break",
                        "start": period.get("start", ""),
                        "start_timestamp": period.get("start_timestamp", 0),
                        "end": period.get("end", ""),
                        "end_timestamp": period.get("end_timestamp", 0),
                        "duration": period.get("duration", 0),
                    }
                )

            # Add idle periods
            for period in session.get("idle_periods", []):
                self.all_periods.append(
                    {
                        "type": "Idle",
                        "start": period.get("start", ""),
                        "start_timestamp": period.get("start_timestamp", 0),
                        "end": period.get("end", ""),
                        "end_timestamp": period.get("end_timestamp", 0),
                        "duration": period.get("duration", 0),
                    }
                )

        # Sort by start timestamp
        self.all_periods.sort(key=lambda x: x["start_timestamp"])

        # Display timeline directly in frame
        periods_frame = ttk.Frame(timeline_container)
        periods_frame.pack(fill="both", expand=True)

        for idx, period in enumerate(self.all_periods):
            col = 0

            # Period type with color coding
            type_label = ttk.Label(
                periods_frame,
                text=period["type"],
                font=("Arial", 10, "bold"),
                width=10,
            )
            type_label.grid(row=idx, column=col, sticky=tk.W, padx=5, pady=2)
            col += 1

            # Start time (from timestamp)
            start_time = (
                datetime.fromtimestamp(period["start_timestamp"])
                .strftime("%I:%M:%S %p")
                .lstrip("0")
                if period["start_timestamp"]
                else ""
            )
            ttk.Label(periods_frame, text=start_time, font=("Arial", 10)).grid(
                row=idx, column=col, sticky=tk.W, padx=1, pady=2
            )
            col += 1

            # insert dash between start and end time
            ttk.Label(periods_frame, text="-", font=("Arial", 10)).grid(
                row=idx, column=col, sticky=tk.W, padx=1, pady=2
            )
            col += 1

            # End time (from timestamp)
            end_time = (
                datetime.fromtimestamp(period["end_timestamp"])
                .strftime("%I:%M:%S %p")
                .lstrip("0")
                if period["end_timestamp"]
                else ""
            )
            ttk.Label(periods_frame, text=end_time, font=("Arial", 10)).grid(
                row=idx, column=col, sticky=tk.W, padx=1, pady=2
            )
            col += 1

            # Duration
            ttk.Label(
                periods_frame,
                text=self.tracker.format_time(period["duration"]),
                font=("Arial", 10),
            ).grid(row=idx, column=col, sticky=tk.W, padx=5, pady=2)
            col += 1

            # dropdown menu for project selection
            if period["type"] == "Active":
                # Get projects for the selected sphere
                active_projects, default_project = self._get_sphere_projects()

                # Add "Add New Project..." option
                project_options = list(active_projects) + ["Add New Project..."]

                # Set initial value for project dropdown
                initial_value = (
                    default_project
                    if default_project and default_project in active_projects
                    else "Select Project"
                )

                project_menu = ttk.Combobox(
                    periods_frame,
                    values=project_options,
                    state="readonly",
                    width=15,
                )
                project_menu.set(initial_value)
                project_menu.grid(row=idx, column=col, sticky=tk.W, padx=5, pady=2)

                # Bind selection event to handle "Add New Project..."
                project_menu.bind(
                    "<<ComboboxSelected>>",
                    lambda e, menu=project_menu: self._on_project_selected(e, menu),
                )

                # Store reference to update later when sphere changes
                self.project_menus.append(project_menu)
                col += 1

            else:
                # For non-active periods (break and idle), project dropdown with break actions
                break_actions, default_break_action = self._get_break_actions()

                # Add "Add New Break Action..." option
                break_action_options = list(break_actions) + ["Add New Break Action..."]

                initial_value = (
                    default_break_action
                    if default_break_action in break_actions
                    else "Select Break Action"
                )

                break_action_menu = ttk.Combobox(
                    periods_frame,
                    values=break_action_options,
                    state="readonly",
                    width=15,
                )
                break_action_menu.set(initial_value)
                break_action_menu.grid(row=idx, column=col, sticky=tk.W, padx=5, pady=2)

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
                col += 1

            # First text box (always visible)
            text_box = ttk.Entry(periods_frame, width=20)
            text_box.grid(row=idx, column=col, sticky=tk.W, padx=5, pady=2)
            self.text_boxes.append(text_box)
            col += 1

            # Add toggle button (starts as +, stays in same position)
            toggle_btn = ttk.Button(
                periods_frame,
                text="+",
                width=3,
                command=lambda i=idx: self._toggle_secondary(i),
            )
            toggle_btn.grid(row=idx, column=col, sticky=tk.W, padx=2, pady=2)
            self.toggle_buttons.append(toggle_btn)
            col += 1

            # Secondary dropdown (hidden initially, appears after toggle button)
            if period["type"] == "Active":
                # Secondary project dropdown
                secondary_project_menu = ttk.Combobox(
                    periods_frame,
                    values=project_options,
                    state="readonly",
                    width=15,
                )
                secondary_project_menu.set("Select A Project")
                secondary_project_menu.grid(
                    row=idx, column=col, sticky=tk.W, padx=5, pady=2
                )
                secondary_project_menu.grid_remove()  # Hide initially

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
                secondary_action_menu.set("Select An Action")
                secondary_action_menu.grid(
                    row=idx, column=col, sticky=tk.W, padx=5, pady=2
                )
                secondary_action_menu.grid_remove()  # Hide initially

                # Bind selection event
                secondary_action_menu.bind(
                    "<<ComboboxSelected>>",
                    lambda e, menu=secondary_action_menu: self._on_break_action_selected(
                        e, menu
                    ),
                )

                self.secondary_menus.append(secondary_action_menu)
            col += 1

            # Secondary text box (hidden initially, appears after secondary dropdown)
            text_box_secondary = ttk.Entry(periods_frame, width=20)
            text_box_secondary.grid(row=idx, column=col, sticky=tk.W, padx=5, pady=2)
            text_box_secondary.grid_remove()  # Hide initially
            self.secondary_text_boxes.append(text_box_secondary)

            # Percentage spinbox for secondary (hidden initially)
            percentage_spinbox = ttk.Spinbox(
                periods_frame,
                values=(1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99),
                width=3,
                state="readonly",
                takefocus=0,
            )
            col += 1

            percentage_spinbox.set(50)  # Default 50%

            # Prevent text selection highlighting - clear selection after any change
            def clear_selection(event):
                event.widget.after(1, lambda: event.widget.selection_clear())

            percentage_spinbox.bind("<<Increment>>", clear_selection)
            percentage_spinbox.bind("<<Decrement>>", clear_selection)
            percentage_spinbox.bind("<FocusIn>", clear_selection)
            percentage_spinbox.grid(row=idx, column=col, sticky=tk.W, padx=2, pady=2)
            percentage_spinbox.grid_remove()  # Hide initially
            self.percentage_spinboxes.append(percentage_spinbox)

            col += 1

            # label
            label_secondary_percentage = ttk.Label(
                periods_frame, text="% of this period"
            )
            label_secondary_percentage.grid(row=idx, column=col, sticky=tk.W, pady=2)
            label_secondary_percentage.grid_remove()  # Hide initially
            self.secondary_percentage_labels.append(label_secondary_percentage)

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
        """Handle project selection - enable editing if 'Add New Project...' is selected"""
        selected = combobox.get()

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
        """Save the new project to settings"""
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
                with open(self.tracker.settings_file, "w") as f:
                    json.dump(self.tracker.settings, f, indent=2)

                # Update combobox
                active_projects, _ = self._get_sphere_projects()
                project_options = list(active_projects) + ["Add New Project..."]
                combobox.config(values=project_options, state="readonly")
                combobox.set(new_project)

                if combobox == self.default_project_menu:
                    self._update_project_dropdowns(True)
                else:
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
        """Cancel adding new project and revert to previous state"""
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
        """Save the new break action to settings"""
        new_action = combobox.get().strip()

        if new_action and new_action != "Add New Break Action...":
            if new_action not in self.tracker.settings["break_actions"]:
                # Add new break action
                self.tracker.settings["break_actions"][new_action] = {
                    "active": True,
                    "is_default": False,
                }

                # Save to file
                with open(self.tracker.settings_file, "w") as f:
                    json.dump(self.tracker.settings, f, indent=2)

                # Update combobox
                break_actions, _ = self._get_break_actions()
                action_options = list(break_actions) + ["Add New Break Action..."]
                combobox.config(values=action_options, state="readonly")
                combobox.set(new_action)

                if combobox == self.default_action_menu:
                    self._update_break_action_dropdowns(True)
                else:
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
        """Cancel adding new break action and revert to previous state"""
        break_actions, default_break_action = self._get_break_actions()

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
        """Update all project dropdown menus when sphere selection changes"""

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
        # Only update the ones that correspond to Active periods
        project_count = len(self.project_menus)
        for i in range(project_count):
            if i < len(self.secondary_menus):
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
        """Update all break action dropdown menus when break action selection changes"""
        break_actions, default_break_action = self._get_break_actions()
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

        # Update default action menu (once, outside loop)
        current_default = self.default_action_menu.get()
        self.default_action_menu.config(values=action_options)

        if current_default in action_options:
            self.default_action_menu.set(current_default)
        elif default_break_action and default_break_action in action_options:
            self.default_action_menu.set(default_break_action)
        else:
            self.default_action_menu.set("Select Break Action")

        # Update secondary break/idle action dropdowns' options (but not their selection)
        # Only update the ones that correspond to Break/Idle periods
        project_count = len(self.project_menus)
        for i in range(project_count, len(self.secondary_menus)):
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
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=0, columnspan=2, pady=10)

        # Active notes
        ttk.Label(
            session_comments_container, text="Active Notes:", font=("Arial", 10)
        ).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.active_notes = ttk.Entry(session_comments_container, width=30)
        self.active_notes.grid(row=1, column=1, sticky=tk.W, pady=5)
        # Break notes
        ttk.Label(
            session_comments_container, text="Break Notes:", font=("Arial", 10)
        ).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.break_notes = ttk.Entry(session_comments_container, width=30)
        self.break_notes.grid(row=2, column=1, sticky=tk.W, pady=5)

        # Idle notes
        ttk.Label(
            session_comments_container, text="Idle Notes:", font=("Arial", 10)
        ).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.idle_notes = ttk.Entry(session_comments_container, width=30)
        self.idle_notes.grid(row=3, column=1, sticky=tk.W, pady=5)

        # Session notes
        ttk.Label(
            session_comments_container, text="Session Notes:", font=("Arial", 10)
        ).grid(row=12, column=0, sticky=(tk.W, tk.N), pady=5)
        self.session_notes_text = tk.Text(
            session_comments_container, width=30, height=4, font=("Arial", 10)
        )
        self.session_notes_text.grid(row=12, column=1, sticky=tk.W, pady=5)

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

    def save_and_close(self):
        """Save action tags and return to main frame"""
        all_data = self.tracker.load_data()

        if self.session_name not in all_data:
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
            comment = (
                self.text_boxes[idx].get().strip() if idx < len(self.text_boxes) else ""
            )

            # Get secondary dropdown value if exists
            secondary_value = ""
            if idx < len(self.secondary_menus):
                secondary_value = self.secondary_menus[idx].get().strip()

            # Get percentage value for secondary (default 50 if not set)
            secondary_percentage = 50
            if idx < len(self.percentage_spinboxes):
                try:
                    secondary_percentage = int(self.percentage_spinboxes[idx].get())
                except (ValueError, tk.TclError):
                    secondary_percentage = 50

            # get the secondary text box value for this period
            comment_secondary = (
                self.secondary_text_boxes[idx].get().strip()
                if idx < len(self.secondary_text_boxes)
                else ""
            )

            # Find and update the corresponding period in the session data
            if period_type == "Active":
                project = (
                    self.project_menus[project_idx].get()
                    if project_idx < len(self.project_menus)
                    else ""
                )
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
                            # Remove old fields to avoid duplication
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
                            # Remove projects array if it exists
                            active_period.pop("projects", None)
                            active_period.pop("comment_secondary", None)
                        break

            elif period_type == "Break":
                break_action = (
                    self.break_action_menus[break_action_idx].get()
                    if break_action_idx < len(self.break_action_menus)
                    else ""
                )
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
                            # Remove old fields to avoid duplication
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
                            # Remove actions array if it exists
                            break_period.pop("actions", None)
                            break_period.pop("comment_secondary", None)
                        break

            elif period_type == "Idle":
                idle_action = (
                    self.idle_action_menus[idle_action_idx].get()
                    if idle_action_idx < len(self.idle_action_menus)
                    else ""
                )
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
                            # Remove old fields to avoid duplication
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
                            # Remove actions array if it exists
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
        self.tracker.show_main_frame()

    def skip_and_close(self):
        """Return to main frame without saving"""
        self.tracker.show_main_frame()
