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

        # Store references to project dropdowns for updating when sphere changes
        self.project_menus = []

        self.create_widgets()

    def create_widgets(self):
        """Create all UI elements for the completion frame"""

        # Title and sphere selection
        self._title_and_sphere()

        # display date, start time, end time and duration
        self._session_info_display()

        # separator
        ttk.Separator(self, orient="horizontal").grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15
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

    # title and sphere selection method
    def _title_and_sphere(self):
        # Create a frame to hold all time labels in a single row
        time_frame = ttk.Frame(self)
        time_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        default_sphere = self.tracker.settings["spheres"].get("default_sphere", "")
        active_spheres = self.tracker.settings["spheres"].get("active_spheres", [])

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

    def _on_sphere_selected(self, _):
        """Handle sphere selection - enable editing if 'Add New Sphere...' is selected"""
        selected = self.sphere_menu.get()
        self.selected_sphere = selected

        # Update all project dropdowns with projects from the selected sphere
        self._update_project_dropdowns()

        if selected == "Add New Sphere...":
            self._handle_add_new(
                combobox=self.sphere_menu,
                add_new_text="Add New Sphere...",
                save_func=self._get_save_sphere_func(),
                get_fallback_func=self._get_sphere_fallback,
                post_save_callback=None,
            )

    def _get_save_sphere_func(self):
        """Return a function that saves a new sphere"""

        def save_sphere(sphere_name):
            active_spheres = self.tracker.settings["spheres"].get("active_spheres", [])
            if sphere_name not in active_spheres:
                active_spheres.append(sphere_name)
                self.selected_sphere = sphere_name
                return list(active_spheres) + ["Add New Sphere..."]
            return None

        return save_sphere

    def _get_sphere_fallback(self):
        """Get fallback value for sphere combobox"""
        default_sphere = self.tracker.settings["spheres"].get("default_sphere", "")
        active_spheres = self.tracker.settings["spheres"].get("active_spheres", [])
        return (
            default_sphere
            if default_sphere in active_spheres
            else active_spheres[0] if active_spheres else ""
        )

    def _handle_add_new(
        self,
        combobox,
        add_new_text,
        save_func,
        get_fallback_func,
        post_save_callback=None,
    ):
        """Generic handler for 'Add New...' workflow

        Args:
            combobox: The combobox widget
            add_new_text: The 'Add New...' text (e.g., 'Add New Sphere...')
            save_func: Function that saves the item and returns updated list (or None if already exists)
            get_fallback_func: Function that returns the fallback value if cancelled
            post_save_callback: Optional callback to run after successful save
        """

        def save_callback(event):
            new_item = combobox.get().strip()
            if new_item and new_item != add_new_text:
                updated_values = save_func(new_item)
                if updated_values is not None:
                    with open(self.tracker.settings_file, "w") as f:
                        json.dump(self.tracker.settings, f, indent=2)
                    combobox.config(values=updated_values, state="readonly")
                    combobox.set(new_item)
                    if post_save_callback:
                        post_save_callback()
                else:
                    combobox.config(state="readonly")
                    combobox.set(new_item)
            else:
                cancel_callback(None)
            combobox.unbind("<Return>")
            combobox.unbind("<FocusOut>")

        def cancel_callback(event):
            combobox.config(state="readonly")
            combobox.set(get_fallback_func())
            combobox.unbind("<Return>")
            combobox.unbind("<FocusOut>")

        # Enable editing
        combobox.config(state="normal")
        combobox.set("")
        combobox.focus()
        combobox.bind("<Return>", save_callback)
        combobox.bind("<FocusOut>", cancel_callback)

    def _enable_combobox_add_new(self, combobox, save_callback, cancel_callback):
        """Generic method to enable adding a new item to a combobox"""
        # Change to normal state and clear the field
        combobox.config(state="normal")
        combobox.set("")
        combobox.focus()

        # Bind Return key to save the new item
        combobox.bind("<Return>", save_callback)
        # Bind FocusOut to handle if user clicks away
        combobox.bind("<FocusOut>", cancel_callback)

    def _save_new_item(
        self, combobox, new_item, add_new_text, save_func, cancel_callback
    ):
        """Generic method to save a new item to a combobox

        Args:
            combobox: The combobox widget
            new_item: The new item name entered by user
            add_new_text: The 'Add New...' text to filter out
            save_func: Function that saves the item and returns updated list (or None if already exists)
            cancel_callback: Function to call if save is cancelled
        """
        if new_item and new_item != add_new_text:
            updated_values = save_func(new_item)

            if updated_values is not None:
                # Save settings to file
                with open(self.tracker.settings_file, "w") as f:
                    json.dump(self.tracker.settings, f, indent=2)

                # Update the combobox values
                combobox.config(values=updated_values, state="readonly")
                combobox.set(new_item)
            else:
                # Already exists, just set it
                combobox.config(state="readonly")
                combobox.set(new_item)
        else:
            # Cancel if empty
            cancel_callback(None)

        # Unbind the events
        combobox.unbind("<Return>")
        combobox.unbind("<FocusOut>")

    def _cancel_new_item(self, combobox, fallback_value):
        """Generic method to cancel adding a new item to a combobox

        Args:
            combobox: The combobox widget
            fallback_value: The value to revert to
        """
        combobox.config(state="readonly")
        combobox.set(fallback_value)

        # Unbind the events if they exist
        combobox.unbind("<Return>")
        combobox.unbind("<FocusOut>")

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
        time_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)

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
        time_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)

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
                        "end": period.get("end", ""),
                        "end_timestamp": period.get("end_timestamp", 0),
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
                        "end": period.get("end", ""),
                        "end_timestamp": period.get("end_timestamp", 0),
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
                        "end": period.get("end", ""),
                        "end_timestamp": period.get("end_timestamp", 0),
                        "duration": period.get("duration", 0),
                    }
                )

        # Sort by start timestamp
        all_periods.sort(key=lambda x: x["start_timestamp"])

        # Display timeline directly in frame
        periods_frame = ttk.Frame(timeline_container)
        periods_frame.pack(fill="both", expand=True)

        for idx, period in enumerate(all_periods):
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

            # dropdown menu for project selection (optional)
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

                # Store reference to update later when sphere changes
                self.project_menus.append(break_action_menu)

                col += 1

    def _on_project_selected(self, event, combobox):
        """Handle project selection - enable editing if 'Add New Project...' is selected"""
        selected = combobox.get()

        if selected == "Add New Project...":
            self._handle_add_new(
                combobox=combobox,
                add_new_text="Add New Project...",
                save_func=self._get_save_project_func(),
                get_fallback_func=self._get_project_fallback,
                post_save_callback=self._update_project_dropdowns,
            )

    def _get_save_project_func(self):
        """Return a function that saves a new project"""

        def save_project(project_name):
            if project_name not in self.tracker.settings["projects"]:
                self.tracker.settings["projects"][project_name] = {
                    "active": True,
                    "sphere": self.selected_sphere,
                    "is_default": False,
                }
                active_projects, _ = self._get_sphere_projects()
                return list(active_projects) + ["Add New Project..."]
            return None

        return save_project

    def _get_project_fallback(self):
        """Get fallback value for project combobox"""
        active_projects, default_project = self._get_sphere_projects()
        return (
            default_project
            if default_project and default_project in active_projects
            else "Select Project"
        )

    def _on_break_action_selected(self, event, combobox):
        """Handle break action selection - enable editing if 'Add New Break Action...' is selected"""
        selected = combobox.get()

        if selected == "Add New Break Action...":
            self._handle_add_new(
                combobox=combobox,
                add_new_text="Add New Break Action...",
                save_func=self._get_save_break_action_func(),
                get_fallback_func=self._get_break_action_fallback,
                post_save_callback=None,
            )

    def _get_save_break_action_func(self):
        """Return a function that saves a new break action"""

        def save_break_action(action_name):
            if action_name not in self.tracker.settings["break_actions"]:
                self.tracker.settings["break_actions"][action_name] = {
                    "active": True,
                    "is_default": False,
                }
                break_actions, _ = self._get_break_actions()
                return list(break_actions) + ["Add New Break Action..."]
            return None

        return save_break_action

    def _get_break_action_fallback(self):
        """Get fallback value for break action combobox"""
        break_actions, default_break_action = self._get_break_actions()
        return (
            default_break_action
            if default_break_action in break_actions
            else "Select Break Action"
        )

    def _update_project_dropdowns(self):
        """Update all project dropdown menus when sphere selection changes"""
        # Get projects for the currently selected sphere
        active_projects, default_project = self._get_sphere_projects()

        # Update each project dropdown
        for menu in self.project_menus:
            current_selection = menu.get()
            menu["values"] = active_projects

            # Keep current selection if it's still in the new list, otherwise use default
            if current_selection in active_projects:
                menu.set(current_selection)
            elif default_project and default_project in active_projects:
                menu.set(default_project)
            else:
                menu.set("Select Project")

    def _create_action_tags(self):
        """Create the action tags input section"""
        ttk.Label(self, text="Session Actions", font=("Arial", 12, "bold")).grid(
            row=8, column=0, columnspan=2, pady=10
        )

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
