import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json


class SettingsFrame(ttk.Frame):
    def __init__(self, parent, tracker):
        """
        Initialize the settings frame

        Args:
            parent: Parent window/frame
            tracker: TimeTracker instance to access methods and settings
        """
        super().__init__(parent)
        self.tracker = tracker
        self.current_sphere = None
        self.sphere_filter = tk.StringVar(value="active")
        self.project_filter = tk.StringVar(value="active")

        # Track editing states
        self.editing_projects = {}  # {project_name: {widgets}}

        self.create_widgets()

    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.tracker.settings_file, "w") as f:
                json.dump(self.tracker.settings, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def create_widgets(self):
        """Create main settings interface"""
        # Create scrollable container
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)

        # Main content frame
        content_frame = ttk.Frame(canvas, padding="10")

        # Configure canvas
        content_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Update canvas window width when canvas resizes
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel for scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        content_frame.bind("<MouseWheel>", on_mousewheel)

        row = 0

        # Title
        ttk.Label(content_frame, text="Settings", font=("Arial", 16, "bold")).grid(
            row=row, column=0, columnspan=3, pady=10, sticky=tk.W
        )
        row += 1

        # Sphere management section
        self.create_sphere_section(content_frame, row)
        row += 10  # Reserve space for sphere section

        # Project details section
        self.project_section_row = row
        self.project_content_frame = content_frame
        self.create_project_section(content_frame, row)
        row += 20  # Reserve space for project section

        # Separator
        ttk.Separator(content_frame, orient="horizontal").grid(
            row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20
        )
        row += 1

        # Break actions and idle settings
        self.create_break_idle_section(content_frame, row)

        # Store references
        self.content_frame = content_frame
        self.canvas = canvas

    def create_sphere_section(self, parent, start_row):
        """Create sphere management section"""
        row = start_row

        # Sphere filter buttons
        filter_frame = ttk.Frame(parent)
        filter_frame.grid(row=row, column=0, columnspan=3, pady=5, sticky=tk.W)

        ttk.Radiobutton(
            filter_frame,
            text="Active",
            variable=self.sphere_filter,
            value="active",
            command=self.refresh_sphere_dropdown,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            filter_frame,
            text="All",
            variable=self.sphere_filter,
            value="all",
            command=self.refresh_sphere_dropdown,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            filter_frame,
            text="Inactive",
            variable=self.sphere_filter,
            value="inactive",
            command=self.refresh_sphere_dropdown,
        ).pack(side=tk.LEFT, padx=5)

        row += 1



        self.sphere_var = tk.StringVar()
        self.sphere_dropdown = ttk.Combobox(
            parent, textvariable=self.sphere_var, width=15, font=("Arial", 20)
        )
        self.sphere_dropdown.grid(
            row=row, column=0, columnspan=2, pady=5, sticky=(tk.W)
        )
        self.sphere_dropdown.bind(
            "<<ComboboxSelected>>", lambda e: self.load_selected_sphere()
        )
        row += 1

         # Sphere management frame (shown when sphere is selected)
        self.sphere_mgmt_frame = ttk.Frame(parent)
        self.sphere_mgmt_frame.grid(
            row=row, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E)
        )
        row += 1

        # Create new sphere button
        ttk.Button(
            parent, text="Create New Sphere", command=self.create_new_sphere
        ).grid(row=row, column=0, pady=5, sticky=tk.E)
        row += 1

        # Refresh dropdown
        self.refresh_sphere_dropdown()

    def refresh_sphere_dropdown(self):
        """Refresh the sphere dropdown based on filter"""
        filter_val = self.sphere_filter.get()
        spheres = self.tracker.settings.get("spheres", {})

        filtered_spheres = []
        for name, data in spheres.items():
            if filter_val == "active" and data.get("active", True):
                filtered_spheres.append(name)
            elif filter_val == "inactive" and not data.get("active", True):
                filtered_spheres.append(name)
            elif filter_val == "all":
                filtered_spheres.append(name)

        self.sphere_dropdown["values"] = filtered_spheres

        # Set default sphere if available
        if filtered_spheres:
            default_sphere = self.tracker._get_default_sphere()
            if default_sphere in filtered_spheres:
                self.sphere_var.set(default_sphere)
            else:
                self.sphere_var.set(filtered_spheres[0])
            self.load_selected_sphere()

    def create_new_sphere(self):
        """Create a new sphere"""
        name = simpledialog.askstring("New Sphere", "Enter sphere name:")
        if name and name.strip():
            name = name.strip()
            if name in self.tracker.settings.get("spheres", {}):
                messagebox.showerror("Error", "A sphere with this name already exists")
                return

            # Add new sphere
            if "spheres" not in self.tracker.settings:
                self.tracker.settings["spheres"] = {}

            self.tracker.settings["spheres"][name] = {
                "is_default": False,
                "active": True,
            }

            self.save_settings()
            self.refresh_sphere_dropdown()
            self.sphere_var.set(name)
            self.load_selected_sphere()

    def load_selected_sphere(self):
        """Load and display selected sphere details"""
        sphere_name = self.sphere_var.get()
        if not sphere_name:
            return

        self.current_sphere = sphere_name
        sphere_data = self.tracker.settings.get("spheres", {}).get(sphere_name, {})

        # Clear existing widgets
        for widget in self.sphere_mgmt_frame.winfo_children():
            widget.destroy()

        row = 0

        # Default button
        is_default = sphere_data.get("is_default", False)
        if is_default:
            btn = ttk.Button(
                self.sphere_mgmt_frame, text="✓ Default Sphere", state=tk.DISABLED
            )
        else:
            btn = ttk.Button(
                self.sphere_mgmt_frame,
                text="Set as Default",
                command=lambda: self.set_default_sphere(sphere_name),
            )
        btn.grid(row=row, column=0, padx=5, pady=5)

        # Edit name button
        ttk.Button(
            self.sphere_mgmt_frame,
            text="Edit Name",
            command=lambda: self.edit_sphere_name(sphere_name),
        ).grid(row=row, column=1, padx=5, pady=5)

        # Archive/Activate button
        is_active = sphere_data.get("active", True)
        if is_active:
            ttk.Button(
                self.sphere_mgmt_frame,
                text="Archive Sphere",
                command=lambda: self.toggle_sphere_active(sphere_name),
            ).grid(row=row, column=2, padx=5, pady=5)
        else:
            ttk.Button(
                self.sphere_mgmt_frame,
                text="Activate Sphere",
                command=lambda: self.toggle_sphere_active(sphere_name),
            ).grid(row=row, column=2, padx=5, pady=5)

        # Delete button
        ttk.Button(
            self.sphere_mgmt_frame,
            text="Delete Sphere",
            command=lambda: self.delete_sphere(sphere_name),
        ).grid(row=row, column=3, padx=5, pady=5)

    def set_default_sphere(self, sphere_name):
        """Set a sphere as default"""
        # Remove default from all spheres
        for name in self.tracker.settings.get("spheres", {}):
            self.tracker.settings["spheres"][name]["is_default"] = False

        # Set new default
        self.tracker.settings["spheres"][sphere_name]["is_default"] = True
        self.save_settings()
        self.load_selected_sphere()

    def edit_sphere_name(self, old_name):
        """Edit sphere name"""
        new_name = simpledialog.askstring(
            "Edit Sphere Name", "Enter new name:", initialvalue=old_name
        )

        if new_name and new_name.strip() and new_name != old_name:
            new_name = new_name.strip()

            if new_name in self.tracker.settings.get("spheres", {}):
                messagebox.showerror("Error", "A sphere with this name already exists")
                return

            # Rename sphere
            sphere_data = self.tracker.settings["spheres"].pop(old_name)
            self.tracker.settings["spheres"][new_name] = sphere_data

            # Update projects that reference this sphere
            for project_name, project_data in self.tracker.settings.get(
                "projects", {}
            ).items():
                if project_data.get("sphere") == old_name:
                    project_data["sphere"] = new_name

            self.save_settings()
            self.refresh_sphere_dropdown()
            self.sphere_var.set(new_name)
            self.load_selected_sphere()

    def toggle_sphere_active(self, sphere_name):
        """Toggle sphere active/inactive status"""
        current_status = self.tracker.settings["spheres"][sphere_name].get(
            "active", True
        )
        self.tracker.settings["spheres"][sphere_name]["active"] = not current_status
        self.save_settings()
        self.refresh_sphere_dropdown()

    def delete_sphere(self, sphere_name):
        """Delete a sphere and its associated projects"""
        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{sphere_name}' and all its projects?\nThis cannot be undone.",
        )

        if not confirm:
            return

        # Delete sphere
        if sphere_name in self.tracker.settings.get("spheres", {}):
            del self.tracker.settings["spheres"][sphere_name]

        # Delete associated projects
        projects_to_delete = []
        for project_name, project_data in self.tracker.settings.get(
            "projects", {}
        ).items():
            if project_data.get("sphere") == sphere_name:
                projects_to_delete.append(project_name)

        for project_name in projects_to_delete:
            del self.tracker.settings["projects"][project_name]

        self.save_settings()
        self.refresh_sphere_dropdown()
        self.refresh_project_section()

    def create_project_section(self, parent, start_row):
        """Create project management section"""
        row = start_row

        # Section title
        ttk.Label(parent, text="Projects", font=("Arial", 14, "bold")).grid(
            row=row, column=0, columnspan=3, pady=10, sticky=tk.W
        )
        row += 1

        # Project filter buttons
        filter_frame = ttk.Frame(parent)
        filter_frame.grid(row=row, column=0, columnspan=3, pady=5, sticky=tk.W)

        ttk.Radiobutton(
            filter_frame,
            text="Active",
            variable=self.project_filter,
            value="active",
            command=self.refresh_project_section,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            filter_frame,
            text="All",
            variable=self.project_filter,
            value="all",
            command=self.refresh_project_section,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            filter_frame,
            text="Archived",
            variable=self.project_filter,
            value="inactive",
            command=self.refresh_project_section,
        ).pack(side=tk.LEFT, padx=5)

        row += 1

        # Create new project button
        ttk.Button(
            parent, text="Create New Project", command=self.create_new_project
        ).grid(row=row, column=0, pady=5, sticky=tk.W)
        row += 1

        # Projects list frame
        self.projects_list_frame = ttk.Frame(parent)
        self.projects_list_frame.grid(
            row=row, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E)
        )

        self.refresh_project_section()

    def refresh_project_section(self):
        """Refresh the project list"""
        # Clear existing widgets
        for widget in self.projects_list_frame.winfo_children():
            widget.destroy()

        self.editing_projects = {}

        filter_val = self.project_filter.get()
        projects = self.tracker.settings.get("projects", {})

        # Filter and sort projects (default first)
        filtered_projects = []
        default_project = None

        for name, data in projects.items():
            include = False
            if filter_val == "active" and data.get("active", True):
                include = True
            elif filter_val == "inactive" and not data.get("active", True):
                include = True
            elif filter_val == "all":
                include = True

            if include:
                if data.get("is_default", False):
                    default_project = (name, data)
                else:
                    filtered_projects.append((name, data))

        # Sort alphabetically
        filtered_projects.sort(key=lambda x: x[0])

        # Put default first
        if default_project:
            filtered_projects.insert(0, default_project)

        # Display projects
        for idx, (project_name, project_data) in enumerate(filtered_projects):
            self.create_project_row(
                self.projects_list_frame, idx, project_name, project_data
            )

    def create_project_row(self, parent, row, project_name, project_data):
        """Create a row for a project"""
        frame = ttk.Frame(parent, relief=tk.RIDGE, borderwidth=1, padding=5)
        frame.grid(row=row, column=0, columnspan=3, pady=5, sticky=(tk.W, tk.E))

        # Project name
        ttk.Label(frame, text="Name:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, padx=5
        )
        name_var = tk.StringVar(value=project_name)
        name_entry = ttk.Entry(frame, textvariable=name_var, state="readonly", width=30)
        name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)

        # Sphere
        ttk.Label(frame, text="Sphere:").grid(row=0, column=2, sticky=tk.W, padx=5)
        sphere_var = tk.StringVar(value=project_data.get("sphere", "General"))
        sphere_combo = ttk.Combobox(
            frame, textvariable=sphere_var, state="disabled", width=15
        )
        sphere_combo["values"] = list(self.tracker.settings.get("spheres", {}).keys())
        sphere_combo.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=5)

        # Note
        ttk.Label(frame, text="Note:").grid(row=1, column=0, sticky=tk.W, padx=5)
        note_var = tk.StringVar(value=project_data.get("note", ""))
        note_entry = ttk.Entry(frame, textvariable=note_var, state="readonly", width=50)
        note_entry.grid(
            row=1, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=2
        )

        # Goal
        ttk.Label(frame, text="Goal:").grid(row=2, column=0, sticky=tk.W, padx=5)
        goal_var = tk.StringVar(value=project_data.get("goal", ""))
        goal_entry = ttk.Entry(frame, textvariable=goal_var, state="readonly", width=50)
        goal_entry.grid(
            row=2, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=2
        )

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=5)

        # Edit/Save button
        edit_btn = ttk.Button(
            button_frame,
            text="Edit",
            command=lambda: self.toggle_project_edit(
                project_name,
                name_entry,
                sphere_combo,
                note_entry,
                goal_entry,
                edit_btn,
                name_var,
                sphere_var,
                note_var,
                goal_var,
            ),
        )
        edit_btn.pack(side=tk.LEFT, padx=5)

        # Default button
        is_default = project_data.get("is_default", False)
        if is_default:
            ttk.Button(button_frame, text="✓ Default Project", state=tk.DISABLED).pack(
                side=tk.LEFT, padx=5
            )
        else:
            ttk.Button(
                button_frame,
                text="Set as Default",
                command=lambda: self.set_default_project(project_name),
            ).pack(side=tk.LEFT, padx=5)

        # Archive/Activate button
        is_active = project_data.get("active", True)
        if is_active:
            ttk.Button(
                button_frame,
                text="Archive",
                command=lambda: self.toggle_project_active(project_name),
            ).pack(side=tk.LEFT, padx=5)
        else:
            ttk.Button(
                button_frame,
                text="Activate",
                command=lambda: self.toggle_project_active(project_name),
            ).pack(side=tk.LEFT, padx=5)

        # Delete button
        ttk.Button(
            button_frame,
            text="Delete",
            command=lambda: self.delete_project(project_name),
        ).pack(side=tk.LEFT, padx=5)

    def toggle_project_edit(
        self,
        project_name,
        name_entry,
        sphere_combo,
        note_entry,
        goal_entry,
        edit_btn,
        name_var,
        sphere_var,
        note_var,
        goal_var,
    ):
        """Toggle project edit mode"""
        if edit_btn["text"] == "Edit":
            # Enable editing
            name_entry.config(state="normal")
            sphere_combo.config(state="readonly")
            note_entry.config(state="normal")
            goal_entry.config(state="normal")
            edit_btn.config(text="Save")
        else:
            # Save changes
            new_name = name_var.get().strip()

            if not new_name:
                messagebox.showerror("Error", "Project name cannot be empty")
                return

            # Check if name changed and new name already exists
            if new_name != project_name and new_name in self.tracker.settings.get(
                "projects", {}
            ):
                messagebox.showerror("Error", "A project with this name already exists")
                return

            # Update project data
            project_data = self.tracker.settings["projects"].get(project_name, {})
            project_data["sphere"] = sphere_var.get()
            project_data["note"] = note_var.get()
            project_data["goal"] = goal_var.get()

            # If name changed, rename project
            if new_name != project_name:
                self.tracker.settings["projects"].pop(project_name)
                self.tracker.settings["projects"][new_name] = project_data

            self.save_settings()

            # Disable editing
            name_entry.config(state="readonly")
            sphere_combo.config(state="disabled")
            note_entry.config(state="readonly")
            goal_entry.config(state="readonly")
            edit_btn.config(text="Edit")

            # Refresh if name changed
            if new_name != project_name:
                self.refresh_project_section()

    def create_new_project(self):
        """Create a new project"""
        name = simpledialog.askstring("New Project", "Enter project name:")
        if name and name.strip():
            name = name.strip()
            if name in self.tracker.settings.get("projects", {}):
                messagebox.showerror("Error", "A project with this name already exists")
                return

            # Get default sphere
            default_sphere = self.tracker._get_default_sphere()

            # Add new project
            if "projects" not in self.tracker.settings:
                self.tracker.settings["projects"] = {}

            self.tracker.settings["projects"][name] = {
                "sphere": default_sphere,
                "is_default": False,
                "active": True,
                "note": "",
                "goal": "",
            }

            self.save_settings()
            self.refresh_project_section()

    def set_default_project(self, project_name):
        """Set a project as default"""
        # Remove default from all projects
        for name in self.tracker.settings.get("projects", {}):
            self.tracker.settings["projects"][name]["is_default"] = False

        # Set new default
        self.tracker.settings["projects"][project_name]["is_default"] = True
        self.save_settings()
        self.refresh_project_section()

    def toggle_project_active(self, project_name):
        """Toggle project active/inactive status"""
        current_status = self.tracker.settings["projects"][project_name].get(
            "active", True
        )
        self.tracker.settings["projects"][project_name]["active"] = not current_status
        self.save_settings()
        self.refresh_project_section()

    def delete_project(self, project_name):
        """Delete a project"""
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete project '{project_name}'?",
        )

        if not confirm:
            return

        if project_name in self.tracker.settings.get("projects", {}):
            del self.tracker.settings["projects"][project_name]

        self.save_settings()
        self.refresh_project_section()

    def create_break_idle_section(self, parent, start_row):
        """Create break actions and idle settings section"""
        row = start_row

        # Section title
        ttk.Label(
            parent, text="Break Actions & Idle Settings", font=("Arial", 14, "bold")
        ).grid(row=row, column=0, columnspan=3, pady=10, sticky=tk.W)
        row += 1

        # Create two-column layout
        left_frame = ttk.LabelFrame(parent, text="Idle Settings", padding=10)
        left_frame.grid(row=row, column=0, padx=5, pady=5, sticky=(tk.N, tk.W, tk.E))

        right_frame = ttk.LabelFrame(parent, text="Break Actions", padding=10)
        right_frame.grid(
            row=row, column=1, columnspan=2, padx=5, pady=5, sticky=(tk.N, tk.W, tk.E)
        )

        # IDLE SETTINGS (Left column)
        idle_settings = self.tracker.settings.get("idle_settings", {})

        idle_row = 0

        # Idle threshold
        ttk.Label(left_frame, text="Idle Threshold (seconds):").grid(
            row=idle_row, column=0, sticky=tk.W, pady=5
        )
        idle_threshold_var = tk.IntVar(value=idle_settings.get("idle_threshold", 60))
        idle_threshold_spin = ttk.Spinbox(
            left_frame, from_=1, to=600, textvariable=idle_threshold_var, width=10
        )
        idle_threshold_spin.grid(row=idle_row, column=1, pady=5, padx=5)
        idle_row += 1

        # Idle break threshold
        ttk.Label(left_frame, text="Auto-break after idle (seconds):").grid(
            row=idle_row, column=0, sticky=tk.W, pady=5
        )

        idle_break_frame = ttk.Frame(left_frame)
        idle_break_frame.grid(row=idle_row, column=1, pady=5, padx=5)

        idle_break_var = tk.StringVar()
        current_threshold = idle_settings.get("idle_break_threshold", 300)
        if current_threshold == -1:
            idle_break_var.set("Never")
        else:
            idle_break_var.set(str(current_threshold))

        idle_break_options = ["Never"] + [
            str(i * 60) for i in range(1, 31)
        ]  # 1-30 minutes
        idle_break_combo = ttk.Combobox(
            idle_break_frame,
            textvariable=idle_break_var,
            values=idle_break_options,
            width=10,
        )
        idle_break_combo.pack()
        idle_row += 1

        # Save idle settings button
        def save_idle_settings():
            self.tracker.settings["idle_settings"][
                "idle_threshold"
            ] = idle_threshold_var.get()

            break_val = idle_break_var.get()
            if break_val == "Never":
                self.tracker.settings["idle_settings"]["idle_break_threshold"] = -1
            else:
                self.tracker.settings["idle_settings"]["idle_break_threshold"] = int(
                    break_val
                )

            self.save_settings()
            messagebox.showinfo("Success", "Idle settings saved")

        ttk.Button(
            left_frame, text="Save Idle Settings", command=save_idle_settings
        ).grid(row=idle_row, column=0, columnspan=2, pady=10)

        # BREAK ACTIONS (Right column)
        self.create_break_actions_list(right_frame)

    def create_break_actions_list(self, parent):
        """Create break actions management list"""
        # Create new break action button
        ttk.Button(
            parent, text="Create New Break Action", command=self.create_new_break_action
        ).grid(row=0, column=0, columnspan=3, pady=5, sticky=tk.W)

        # Break actions list
        break_actions = self.tracker.settings.get("break_actions", {})

        # Sort: default first, then alphabetically
        sorted_actions = []
        default_action = None

        for name, data in break_actions.items():
            if data.get("is_default", False):
                default_action = (name, data)
            else:
                sorted_actions.append((name, data))

        sorted_actions.sort(key=lambda x: x[0])

        if default_action:
            sorted_actions.insert(0, default_action)

        # Display break actions
        for idx, (action_name, action_data) in enumerate(sorted_actions):
            self.create_break_action_row(parent, idx + 1, action_name, action_data)

    def create_break_action_row(self, parent, row, action_name, action_data):
        """Create a row for a break action"""
        frame = ttk.Frame(parent, relief=tk.RIDGE, borderwidth=1, padding=5)
        frame.grid(row=row, column=0, columnspan=3, pady=5, sticky=(tk.W, tk.E))

        # Action name
        ttk.Label(frame, text=action_name, font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, padx=5
        )

        # Buttons
        is_default = action_data.get("is_default", False)
        if is_default:
            ttk.Button(frame, text="✓ Default", state=tk.DISABLED).grid(
                row=0, column=1, padx=5
            )
        else:
            ttk.Button(
                frame,
                text="Set as Default",
                command=lambda: self.set_default_break_action(action_name),
            ).grid(row=0, column=1, padx=5)

        # Archive/Activate button
        is_active = action_data.get("active", True)
        if is_active:
            ttk.Button(
                frame,
                text="Archive",
                command=lambda: self.toggle_break_action_active(action_name),
            ).grid(row=0, column=2, padx=5)
        else:
            ttk.Button(
                frame,
                text="Activate",
                command=lambda: self.toggle_break_action_active(action_name),
            ).grid(row=0, column=2, padx=5)

        # Delete button
        ttk.Button(
            frame, text="Delete", command=lambda: self.delete_break_action(action_name)
        ).grid(row=0, column=3, padx=5)

    def create_new_break_action(self):
        """Create a new break action"""
        name = simpledialog.askstring("New Break Action", "Enter break action name:")
        if name and name.strip():
            name = name.strip()
            if name in self.tracker.settings.get("break_actions", {}):
                messagebox.showerror(
                    "Error", "A break action with this name already exists"
                )
                return

            # Add new break action
            if "break_actions" not in self.tracker.settings:
                self.tracker.settings["break_actions"] = {}

            self.tracker.settings["break_actions"][name] = {
                "is_default": False,
                "active": True,
            }

            self.save_settings()

            # Refresh break actions display
            for widget in self.content_frame.winfo_children():
                if (
                    isinstance(widget, ttk.LabelFrame)
                    and widget.cget("text") == "Break Actions"
                ):
                    for child in widget.winfo_children():
                        child.destroy()
                    self.create_break_actions_list(widget)
                    break

    def set_default_break_action(self, action_name):
        """Set a break action as default"""
        # Remove default from all break actions
        for name in self.tracker.settings.get("break_actions", {}):
            self.tracker.settings["break_actions"][name]["is_default"] = False

        # Set new default
        self.tracker.settings["break_actions"][action_name]["is_default"] = True
        self.save_settings()

        # Refresh display
        for widget in self.content_frame.winfo_children():
            if (
                isinstance(widget, ttk.LabelFrame)
                and widget.cget("text") == "Break Actions"
            ):
                for child in widget.winfo_children():
                    child.destroy()
                self.create_break_actions_list(widget)
                break

    def toggle_break_action_active(self, action_name):
        """Toggle break action active/inactive status"""
        current_status = self.tracker.settings["break_actions"][action_name].get(
            "active", True
        )
        self.tracker.settings["break_actions"][action_name][
            "active"
        ] = not current_status
        self.save_settings()

        # Refresh display
        for widget in self.content_frame.winfo_children():
            if (
                isinstance(widget, ttk.LabelFrame)
                and widget.cget("text") == "Break Actions"
            ):
                for child in widget.winfo_children():
                    child.destroy()
                self.create_break_actions_list(widget)
                break

    def delete_break_action(self, action_name):
        """Delete a break action"""
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete break action '{action_name}'?",
        )

        if not confirm:
            return

        if action_name in self.tracker.settings.get("break_actions", {}):
            del self.tracker.settings["break_actions"][action_name]

        self.save_settings()

        # Refresh display
        for widget in self.content_frame.winfo_children():
            if (
                isinstance(widget, ttk.LabelFrame)
                and widget.cget("text") == "Break Actions"
            ):
                for child in widget.winfo_children():
                    child.destroy()
                self.create_break_actions_list(widget)
                break
