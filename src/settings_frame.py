import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import csv
import subprocess
import platform

from src.ui_helpers import ScrollableFrame, sanitize_name


class SettingsFrame(ttk.Frame):
    def __init__(self, parent, tracker, root):
        """
        Initialize the settings frame

        Args:
            parent: Parent window/frame
            tracker: TimeTracker instance to access methods and settings
            root: Main root window
        """
        super().__init__(parent)
        self.tracker = tracker
        self.root = root
        self.current_sphere = None
        self.sphere_filter = tk.StringVar(value="active")
        self.project_filter = tk.StringVar(value="active")
        self.break_action_filter = tk.StringVar(value="active")

        # Track editing states
        self.editing_projects = {}  # {project_name: {widgets}}

        # Row counter as instance variable
        self.row = 0

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
        scrollable_container = ScrollableFrame(self, padding="10")
        scrollable_container.pack(fill="both", expand=True)

        content_frame = scrollable_container.get_content_frame()

        # Store update function for manual calls (for dynamic content updates)
        self.update_scrollregion = lambda: scrollable_container.canvas.configure(
            scrollregion=scrollable_container.canvas.bbox("all")
        )

        # Store rebind function for when widgets are added dynamically
        self.bind_mousewheel_func = scrollable_container.rebind_mousewheel

        self.row = 0

        # Back button at top
        ttk.Button(
            content_frame, text="Back to Tracker", command=self.tracker.close_settings
        ).grid(row=self.row, column=0, columnspan=3, pady=10)
        self.row += 1

        ttk.Separator(content_frame, orient="horizontal").grid(
            row=self.row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10
        )
        self.row += 1

        # Sphere management section
        self.create_sphere_section(content_frame)
        self.row += 10  # Reserve space for sphere section

        # Project details section
        self.project_section_row = self.row
        self.project_content_frame = content_frame
        self.create_project_section(content_frame)
        self.row += 20  # Reserve space for project section

        # Separator
        ttk.Separator(content_frame, orient="horizontal").grid(
            row=self.row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20
        )
        self.row += 1

        # Break actions and idle settings
        self.create_break_idle_section(content_frame)

        # Separator
        ttk.Separator(content_frame, orient="horizontal").grid(
            row=self.row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20
        )
        self.row += 1

        # Google Sheets integration section
        self.create_google_sheets_section(content_frame)

        # Separator
        ttk.Separator(content_frame, orient="horizontal").grid(
            row=self.row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20
        )
        self.row += 1

        # Keyboard shortcuts reference section
        self.create_keyboard_shortcuts_section(content_frame)

        # Separator
        ttk.Separator(content_frame, orient="horizontal").grid(
            row=self.row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20
        )
        self.row += 1

        # CSV Export section
        self.create_csv_export_section(content_frame)

        # Back button
        self.row += 1
        ttk.Separator(content_frame, orient="horizontal").grid(
            row=self.row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20
        )
        self.row += 1

        ttk.Button(
            content_frame, text="Back to Tracker", command=self.tracker.close_settings
        ).grid(row=self.row, column=0, columnspan=3, pady=10)

        # Store references
        self.content_frame = content_frame

        # Force final scroll region update after all widgets are created
        content_frame.update_idletasks()
        scrollable_container.canvas.configure(
            scrollregion=scrollable_container.canvas.bbox("all")
        )

    def create_sphere_section(self, parent):
        """Create sphere management section"""

        # Spheres label and filter buttons on same row
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=self.row, column=0, columnspan=3, pady=10, sticky=tk.W)

        ttk.Label(header_frame, text="Spheres", font=("Arial", 16, "bold")).pack(
            side=tk.LEFT, padx=(0, 10)
        )

        # Sphere filter buttons
        filter_frame = ttk.Frame(header_frame)
        filter_frame.pack(side=tk.LEFT)

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

        self.row += 1

        # Dropdown and sphere management frame on the same row
        self.sphere_var = tk.StringVar()
        self.sphere_dropdown = ttk.Combobox(
            parent,
            textvariable=self.sphere_var,
            width=15,
            font=("Arial", 20),
            state="readonly",
            exportselection=False,
        )
        self.sphere_dropdown.grid(row=self.row, column=0, pady=5, sticky=(tk.W))
        self.sphere_dropdown.bind(
            "<<ComboboxSelected>>", lambda e: self.on_sphere_selected()
        )
        # Remove selection highlight
        self.sphere_dropdown.bind(
            "<FocusIn>", lambda e: self.sphere_dropdown.selection_clear()
        )

        # Sphere management frame (shown when sphere is selected)
        self.sphere_mgmt_frame = ttk.Frame(parent)
        self.sphere_mgmt_frame.grid(
            row=self.row, column=1, columnspan=2, pady=5, sticky=(tk.W)
        )
        self.row += 1

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

        # Add "Create New Sphere..." option
        sphere_options = filtered_spheres + ["Create New Sphere..."]
        self.sphere_dropdown["values"] = sphere_options

        # Set default sphere if available
        if filtered_spheres:
            default_sphere = self.tracker._get_default_sphere()
            if default_sphere in filtered_spheres:
                self.sphere_var.set(default_sphere)
            else:
                self.sphere_var.set(filtered_spheres[0])
            self.load_selected_sphere()

    def on_sphere_selected(self):
        """Handle sphere selection or create new sphere"""
        selected = self.sphere_var.get()

        if selected == "Create New Sphere...":
            # Call create new sphere method
            self.create_new_sphere()
        else:
            # Load the selected sphere
            self.load_selected_sphere()
            # Refresh project list to show only projects for selected sphere
            self.refresh_project_section()

    def create_new_sphere(self):
        """Create a new sphere"""
        name = simpledialog.askstring("New Sphere", "Enter sphere name:")
        if name and name.strip():
            name = sanitize_name(name.strip())
            if not name:
                messagebox.showerror("Error", "Invalid sphere name")
                return
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
            self.refresh_project_section()

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
            new_name = sanitize_name(new_name.strip())
            if not new_name:
                messagebox.showerror("Error", "Invalid sphere name")
                return

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

    def create_project_section(self, parent):
        """Create project management section"""

        # Projects frame with border
        projects_frame = ttk.LabelFrame(parent, padding=10)
        projects_frame.grid(
            row=self.row,
            column=0,
            columnspan=3,
            padx=5,
            pady=5,
            sticky=(tk.W, tk.E),
        )
        self.row += 1

        # Section title and filter buttons on same row (inside the frame)
        header_frame = ttk.Frame(projects_frame)
        header_frame.grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky=tk.W)

        ttk.Label(header_frame, text="Projects", font=("Arial", 14, "bold")).pack(
            side=tk.LEFT, padx=(0, 10)
        )

        # Project filter buttons
        filter_frame = ttk.Frame(header_frame)
        filter_frame.pack(side=tk.LEFT)

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

        # Create new project button inside frame
        ttk.Button(
            projects_frame, text="Create New Project", command=self.create_new_project
        ).grid(row=1, column=0, pady=5, sticky=tk.W)

        # Projects list frame
        self.projects_list_frame = ttk.Frame(projects_frame)
        self.projects_list_frame.grid(
            row=2, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E)
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
            current_sphere = self.sphere_var.get()

            # Only show projects that belong to the currently selected sphere
            if data.get("sphere") == current_sphere:
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

        # Rebind mousewheel to new widgets
        if hasattr(self, "bind_mousewheel_func"):
            self.bind_mousewheel_func()

        # Force scroll region update
        if hasattr(self, "update_scrollregion"):
            self.update_scrollregion()

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
        sphere_var = tk.StringVar(value=project_data.get("sphere", ""))
        # Get all active spheres
        active_spheres = [
            name
            for name, data in self.tracker.settings.get("spheres", {}).items()
            if data.get("active", True)
        ]
        sphere_combo = ttk.Combobox(
            frame,
            textvariable=sphere_var,
            values=active_spheres,
            state="disabled",
            width=15,
        )
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
        # Create custom dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("New Project")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Variables
        name_var = tk.StringVar()
        sphere_var = tk.StringVar()
        note_var = tk.StringVar()
        goal_var = tk.StringVar()
        result = {"confirmed": False}

        # Get selected sphere (or default if none selected)
        selected_sphere = self.sphere_var.get()
        if not selected_sphere or selected_sphere == "Create New Sphere...":
            selected_sphere = self.tracker._get_default_sphere()
        sphere_var.set(selected_sphere)

        # Get all active spheres for dropdown
        active_spheres = [
            name
            for name, data in self.tracker.settings.get("spheres", {}).items()
            if data.get("active", True)
        ]

        # Form fields
        ttk.Label(dialog, text="Project Name:").grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=5
        )
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=40)
        name_entry.grid(row=0, column=1, padx=10, pady=5)
        name_entry.focus()

        ttk.Label(dialog, text="Sphere:").grid(
            row=1, column=0, sticky=tk.W, padx=10, pady=5
        )
        sphere_combo = ttk.Combobox(
            dialog,
            textvariable=sphere_var,
            values=active_spheres,
            state="readonly",
            width=37,
        )
        sphere_combo.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Note:").grid(
            row=2, column=0, sticky=tk.W, padx=10, pady=5
        )
        note_entry = ttk.Entry(dialog, textvariable=note_var, width=40)
        note_entry.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Goal:").grid(
            row=3, column=0, sticky=tk.W, padx=10, pady=5
        )
        goal_entry = ttk.Entry(dialog, textvariable=goal_var, width=40)
        goal_entry.grid(row=3, column=1, padx=10, pady=5)

        def on_ok():
            name = sanitize_name(name_var.get().strip())
            if not name:
                messagebox.showerror(
                    "Error",
                    "Project name cannot be empty or contains invalid characters",
                    parent=dialog,
                )
                return
            if name in self.tracker.settings.get("projects", {}):
                messagebox.showerror(
                    "Error", "A project with this name already exists", parent=dialog
                )
                return
            result["confirmed"] = True
            name_var.set(name)  # Update with sanitized name
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="OK", command=on_ok, width=10).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Cancel", command=on_cancel, width=10).pack(
            side=tk.LEFT, padx=5
        )

        # Bind Enter key to OK
        dialog.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_cancel())

        # Wait for dialog to close
        dialog.wait_window()

        if result["confirmed"]:
            # Add new project
            if "projects" not in self.tracker.settings:
                self.tracker.settings["projects"] = {}

            self.tracker.settings["projects"][name_var.get().strip()] = {
                "sphere": sphere_var.get(),
                "is_default": False,
                "active": True,
                "note": note_var.get(),
                "goal": goal_var.get(),
            }

            self.save_settings()
            self.refresh_project_section()

    def set_default_project(self, project_name):
        """Set a project as default"""
        # Get the sphere of the project being set as default
        project_sphere = self.tracker.settings["projects"][project_name].get("sphere")

        # Remove default from all projects in the SAME sphere only
        for name, data in self.tracker.settings.get("projects", {}).items():
            if data.get("sphere") == project_sphere:
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

    def create_break_idle_section(self, parent):
        """Create break actions and idle settings section"""
        # BREAK ACTIONS SECTION (First)

        break_frame = ttk.LabelFrame(parent, padding=10)
        break_frame.grid(
            row=self.row,
            column=0,
            columnspan=3,
            padx=5,
            pady=5,
            sticky=(tk.W, tk.E),
        )
        self.row += 1

        # Store reference for refresh operations
        self.break_actions_frame = break_frame

        self.create_break_actions_list(break_frame)

        # SEPARATOR
        ttk.Separator(parent, orient="horizontal").grid(
            row=self.row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20
        )
        self.row += 1

        # IDLE SETTINGS SECTION (Second)
        idle_frame = ttk.LabelFrame(parent, padding=10)
        idle_frame.grid(
            row=self.row,
            column=0,
            columnspan=3,
            padx=5,
            pady=5,
            sticky=(tk.W, tk.E),
        )
        self.row += 1

        # Header inside the frame
        header_row = 0
        ttk.Label(idle_frame, text="Idle Settings", font=("Arial", 14, "bold")).grid(
            row=header_row, column=0, columnspan=3, pady=(0, 10), sticky=tk.W
        )
        header_row += 1

        # IDLE SETTINGS
        idle_settings = self.tracker.settings.get("idle_settings", {})

        idle_row = header_row

        # Idle tracking enabled toggle
        idle_enabled_var = tk.BooleanVar(
            value=idle_settings.get("idle_tracking_enabled", True)
        )
        ttk.Checkbutton(
            idle_frame,
            text="Enable Idle Tracking",
            variable=idle_enabled_var,
        ).grid(row=idle_row, column=0, columnspan=2, sticky=tk.W, pady=5)
        idle_row += 1

        # Idle threshold
        ttk.Label(idle_frame, text="Idle Threshold (seconds):").grid(
            row=idle_row, column=0, sticky=tk.W, pady=5
        )
        idle_threshold_var = tk.IntVar(value=idle_settings.get("idle_threshold", 60))
        idle_threshold_spin = ttk.Spinbox(
            idle_frame, from_=1, to=600, textvariable=idle_threshold_var, width=10
        )
        idle_threshold_spin.grid(row=idle_row, column=1, pady=5, padx=5)
        idle_row += 1

        # Idle break threshold
        ttk.Label(idle_frame, text="Auto-break after idle (seconds):").grid(
            row=idle_row, column=0, sticky=tk.W, pady=5
        )

        idle_break_frame = ttk.Frame(idle_frame)
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
                "idle_tracking_enabled"
            ] = idle_enabled_var.get()
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
            idle_frame, text="Save Idle Settings", command=save_idle_settings
        ).grid(row=idle_row, column=0, columnspan=2, pady=10)

        # SEPARATOR
        ttk.Separator(parent, orient="horizontal").grid(
            row=self.row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20
        )
        self.row += 1

        # SCREENSHOT SETTINGS SECTION (Third)
        screenshot_frame = ttk.LabelFrame(parent, padding=10)
        screenshot_frame.grid(
            row=self.row,
            column=0,
            columnspan=3,
            padx=5,
            pady=5,
            sticky=(tk.W, tk.E),
        )
        self.row += 1

        # Header inside the frame
        screenshot_header_row = 0
        ttk.Label(
            screenshot_frame, text="Screenshot Settings", font=("Arial", 14, "bold")
        ).grid(
            row=screenshot_header_row, column=0, columnspan=3, pady=(0, 10), sticky=tk.W
        )
        screenshot_header_row += 1

        # SCREENSHOT SETTINGS
        screenshot_settings = self.tracker.settings.get("screenshot_settings", {})

        screenshot_row = screenshot_header_row

        # Screenshot capture enabled toggle
        screenshot_enabled_var = tk.BooleanVar(
            value=screenshot_settings.get("enabled", False)
        )

        # Warning label (initially hidden)
        warning_label = ttk.Label(
            screenshot_frame,
            text="⚠️ Warning: Screenshots may capture sensitive information (passwords, private messages, etc.).\nSoftware creator is not liable for any data captured. Use at your own risk.",
            foreground="red",
            wraplength=500,
            justify=tk.LEFT,
        )

        def toggle_warning():
            if screenshot_enabled_var.get():
                warning_label.grid(
                    row=screenshot_row + 1, column=0, columnspan=3, sticky=tk.W, pady=5
                )
            else:
                warning_label.grid_remove()

        ttk.Checkbutton(
            screenshot_frame,
            text="Enable Screenshot Capture",
            variable=screenshot_enabled_var,
            command=toggle_warning,
        ).grid(row=screenshot_row, column=0, columnspan=2, sticky=tk.W, pady=5)
        screenshot_row += 1

        # Show warning if already enabled
        if screenshot_enabled_var.get():
            warning_label.grid(
                row=screenshot_row, column=0, columnspan=3, sticky=tk.W, pady=5
            )
        screenshot_row += 1

        # Capture on focus change
        capture_on_focus_var = tk.BooleanVar(
            value=screenshot_settings.get("capture_on_focus_change", True)
        )
        ttk.Checkbutton(
            screenshot_frame,
            text="Capture on window focus change",
            variable=capture_on_focus_var,
        ).grid(row=screenshot_row, column=0, columnspan=2, sticky=tk.W, pady=5)
        screenshot_row += 1

        # Min seconds between captures
        ttk.Label(screenshot_frame, text="Min seconds between captures:").grid(
            row=screenshot_row, column=0, sticky=tk.W, pady=5
        )
        min_seconds_var = tk.IntVar(
            value=screenshot_settings.get("min_seconds_between_captures", 10)
        )
        min_seconds_spin = ttk.Spinbox(
            screenshot_frame, from_=1, to=300, textvariable=min_seconds_var, width=10
        )
        min_seconds_spin.grid(row=screenshot_row, column=1, pady=5, padx=5)
        screenshot_row += 1

        # Save screenshot settings button
        def save_screenshot_settings():
            self.tracker.settings["screenshot_settings"] = {
                "enabled": screenshot_enabled_var.get(),
                "capture_on_focus_change": capture_on_focus_var.get(),
                "min_seconds_between_captures": min_seconds_var.get(),
                "screenshot_path": screenshot_settings.get(
                    "screenshot_path", "screenshots"
                ),
            }
            self.save_settings()
            messagebox.showinfo("Success", "Screenshot settings saved")

        ttk.Button(
            screenshot_frame,
            text="Save Screenshot Settings",
            command=save_screenshot_settings,
        ).grid(row=screenshot_row, column=0, columnspan=2, pady=10)

        # Rebind mousewheel to new widgets
        if hasattr(self, "bind_mousewheel_func"):
            self.bind_mousewheel_func()

    def create_google_sheets_section(self, parent):
        """Create Google Sheets integration settings section"""
        from tkinter import filedialog

        google_frame = ttk.LabelFrame(parent, padding=10)
        google_frame.grid(
            row=self.row,
            column=0,
            columnspan=3,
            padx=5,
            pady=5,
            sticky=(tk.W, tk.E),
        )
        self.row += 1

        # Header
        google_header_row = 0
        ttk.Label(
            google_frame, text="Google Sheets Integration", font=("Arial", 14, "bold")
        ).grid(row=google_header_row, column=0, columnspan=3, pady=(0, 10), sticky=tk.W)
        google_header_row += 1

        # Get current settings
        google_settings = self.tracker.settings.get("google_sheets", {})

        google_row = google_header_row

        # Enable toggle
        enabled_var = tk.BooleanVar(value=google_settings.get("enabled", False))
        ttk.Checkbutton(
            google_frame,
            text="Enable automatic upload to Google Sheets",
            variable=enabled_var,
        ).grid(row=google_row, column=0, columnspan=3, sticky=tk.W, pady=5)
        google_row += 1

        # Spreadsheet ID
        ttk.Label(google_frame, text="Spreadsheet ID:").grid(
            row=google_row, column=0, sticky=tk.W, pady=5
        )
        spreadsheet_id_var = tk.StringVar(
            value=google_settings.get("spreadsheet_id", "")
        )
        spreadsheet_id_entry = ttk.Entry(
            google_frame, textvariable=spreadsheet_id_var, width=50
        )
        spreadsheet_id_entry.grid(
            row=google_row, column=1, columnspan=2, pady=5, padx=5, sticky=(tk.W, tk.E)
        )
        google_row += 1

        # Help text for spreadsheet ID
        help_text = ttk.Label(
            google_frame,
            text="Get ID from URL: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit",
            font=("Arial", 8),
            foreground="gray",
        )
        help_text.grid(row=google_row, column=1, columnspan=2, sticky=tk.W, padx=5)
        google_row += 1

        # Sheet name
        ttk.Label(google_frame, text="Sheet Name (Tab):").grid(
            row=google_row, column=0, sticky=tk.W, pady=5
        )
        sheet_name_var = tk.StringVar(
            value=google_settings.get("sheet_name", "Sessions")
        )
        sheet_name_entry = ttk.Entry(
            google_frame, textvariable=sheet_name_var, width=30
        )
        sheet_name_entry.grid(row=google_row, column=1, pady=5, padx=5, sticky=tk.W)
        google_row += 1

        # Credentials file
        ttk.Label(google_frame, text="Credentials File:").grid(
            row=google_row, column=0, sticky=tk.W, pady=5
        )
        credentials_var = tk.StringVar(
            value=google_settings.get("credentials_file", "credentials.json")
        )
        credentials_entry = ttk.Entry(
            google_frame, textvariable=credentials_var, width=30
        )
        credentials_entry.grid(row=google_row, column=1, pady=5, padx=5, sticky=tk.W)

        def browse_credentials():
            filename = filedialog.askopenfilename(
                title="Select Google API Credentials File",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )
            if filename:
                credentials_var.set(filename)

        ttk.Button(google_frame, text="Browse", command=browse_credentials).grid(
            row=google_row, column=2, pady=5, padx=5, sticky=tk.W
        )
        google_row += 1

        # Setup instructions link
        instructions_label = ttk.Label(
            google_frame,
            text="Setup Guide: Download credentials.json from Google Cloud Console\n"
            "1. Go to console.cloud.google.com\n"
            "2. Create/select a project\n"
            "3. Enable Google Sheets API\n"
            "4. Create OAuth 2.0 credentials (Desktop app)\n"
            "5. Download as credentials.json",
            font=("Arial", 8),
            foreground="blue",
            justify=tk.LEFT,
        )
        instructions_label.grid(
            row=google_row, column=0, columnspan=3, sticky=tk.W, pady=10
        )
        google_row += 1

        # Test connection button
        status_label = ttk.Label(google_frame, text="", foreground="blue")
        status_label.grid(
            row=google_row + 1, column=0, columnspan=3, sticky=tk.W, pady=5
        )

        def test_connection():
            """Test the Google Sheets connection"""
            status_label.config(text="Testing connection...", foreground="blue")
            google_frame.update()

            # Save current settings temporarily
            temp_settings = {
                "enabled": True,
                "spreadsheet_id": spreadsheet_id_var.get(),
                "sheet_name": sheet_name_var.get(),
                "credentials_file": credentials_var.get(),
            }
            old_settings = self.tracker.settings.get("google_sheets", {})
            self.tracker.settings["google_sheets"] = temp_settings
            self.save_settings()

            # Test connection
            try:
                from src.google_sheets_integration import GoogleSheetsUploader

                uploader = GoogleSheetsUploader(self.tracker.settings_file)
                success, message = uploader.test_connection()

                if success:
                    status_label.config(text=f"✓ {message}", foreground="green")
                else:
                    status_label.config(text=f"✗ {message}", foreground="red")
            except Exception as e:
                status_label.config(text=f"✗ Error: {str(e)}", foreground="red")

            # Restore original settings
            self.tracker.settings["google_sheets"] = old_settings
            self.save_settings()

        ttk.Button(google_frame, text="Test Connection", command=test_connection).grid(
            row=google_row, column=0, pady=5
        )
        google_row += 1
        google_row += 1  # Space for status label

        # Save button
        def save_google_settings():
            self.tracker.settings["google_sheets"] = {
                "enabled": enabled_var.get(),
                "spreadsheet_id": spreadsheet_id_var.get().strip(),
                "sheet_name": sheet_name_var.get().strip(),
                "credentials_file": credentials_var.get().strip(),
            }
            self.save_settings()
            messagebox.showinfo("Success", "Google Sheets settings saved")

        ttk.Button(
            google_frame,
            text="Save Google Sheets Settings",
            command=save_google_settings,
        ).grid(row=google_row, column=0, columnspan=2, pady=10)

        # Rebind mousewheel to new widgets
        if hasattr(self, "bind_mousewheel_func"):
            self.bind_mousewheel_func()

    def create_keyboard_shortcuts_section(self, parent):
        """Create keyboard shortcuts reference section"""
        shortcuts_frame = ttk.LabelFrame(
            parent, padding=10, text="Global Keyboard Shortcuts"
        )
        shortcuts_frame.grid(
            row=self.row,
            column=0,
            columnspan=3,
            padx=5,
            pady=5,
            sticky=(tk.W, tk.E),
        )
        self.row += 1

        # Header
        ttk.Label(
            shortcuts_frame,
            text="Use these shortcuts anywhere to control Time Aligned:",
            font=("Arial", 10),
        ).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky=tk.W)

        # Shortcuts list
        shortcuts = [
            ("Ctrl + Shift + S", "Start a new session"),
            ("Ctrl + Shift + B", "Toggle break (start/end)"),
            ("Ctrl + Shift + E", "End current session"),
            ("Ctrl + Shift + W", "Show/hide main window"),
        ]

        row = 1
        for hotkey, description in shortcuts:
            # Hotkey in bold/monospace
            hotkey_label = ttk.Label(
                shortcuts_frame,
                text=hotkey,
                font=("Consolas", 10, "bold"),
                foreground="#0066CC",
            )
            hotkey_label.grid(row=row, column=0, sticky=tk.W, padx=(10, 20), pady=5)

            # Description
            desc_label = ttk.Label(
                shortcuts_frame, text=description, font=("Arial", 10)
            )
            desc_label.grid(row=row, column=1, sticky=tk.W, pady=5)

            row += 1

        # Note about system-wide functionality
        note_label = ttk.Label(
            shortcuts_frame,
            text="💡 Tip: These shortcuts work system-wide, even when the window is hidden!",
            font=("Arial", 9, "italic"),
            foreground="#666666",
        )
        note_label.grid(row=row, column=0, columnspan=2, pady=(10, 0), sticky=tk.W)

        # Rebind mousewheel
        if hasattr(self, "bind_mousewheel_func"):
            self.bind_mousewheel_func()

        # Force scroll region update
        if hasattr(self, "update_scrollregion"):
            self.update_scrollregion()

    def create_csv_export_section(self, parent):
        """Create CSV export section"""
        export_frame = ttk.LabelFrame(parent, padding=10, text="Data Export")
        export_frame.grid(
            row=self.row,
            column=0,
            columnspan=3,
            padx=5,
            pady=5,
            sticky=(tk.W, tk.E),
        )
        self.row += 1

        # Description
        ttk.Label(
            export_frame,
            text="Export all tracking data to CSV format for analysis in spreadsheet applications.",
            font=("Arial", 10),
            wraplength=500,
        ).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky=tk.W)

        # Export button
        ttk.Button(
            export_frame, text="Save All Data to CSV", command=self.save_all_data_to_csv
        ).grid(row=1, column=0, pady=5, sticky=tk.W, padx=10)

        # Rebind mousewheel
        if hasattr(self, "bind_mousewheel_func"):
            self.bind_mousewheel_func()

        # Force scroll region update
        if hasattr(self, "update_scrollregion"):
            self.update_scrollregion()

    def save_all_data_to_csv(self):
        """Export all tracking data to CSV file"""
        from tkinter import filedialog

        try:
            # Load data from data.json
            data_file = self.tracker.data_file

            if not os.path.exists(data_file):
                messagebox.showerror("Error", "Data file not found")
                return

            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not data:
                messagebox.showwarning("No Data", "No tracking data to export")
                return

            # Ask user where to save the CSV
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save Data as CSV",
                initialfile=f"time_aligned_data_{data.get(list(data.keys())[0], {}).get('date', 'export') if data else 'export'}.csv",
            )

            if not file_path:
                return  # User cancelled

            # Convert data to CSV format
            csv_rows = []

            for session_id, session_data in data.items():
                # Get session-level data
                sphere = session_data.get("sphere", "")
                date = session_data.get("date", "")
                start_time = session_data.get("start_time", "")
                end_time = session_data.get("end_time", "")
                total_duration = session_data.get("total_duration", 0)
                active_duration = session_data.get("active_duration", 0)
                break_duration = session_data.get("break_duration", 0)

                # Get session comments
                session_comments = session_data.get("session_comments", {})
                active_notes = session_comments.get("active_notes", "")
                break_notes = session_comments.get("break_notes", "")
                idle_notes = session_comments.get("idle_notes", "")
                session_notes = session_comments.get("session_notes", "")

                # Process active periods
                active_periods = session_data.get("active", [])
                breaks = session_data.get("breaks", [])
                idle_periods = session_data.get("idle_periods", [])

                # If there are active periods, create a row for each
                if active_periods:
                    for active in active_periods:
                        # Extract primary and secondary project information
                        primary_project = ""
                        secondary_project = ""
                        secondary_comment = ""
                        secondary_percentage = ""

                        if active.get("project"):
                            # Single project case
                            primary_project = active.get("project", "")
                        else:
                            # Multiple projects case
                            for project_item in active.get("projects", []):
                                if project_item.get("project_primary", True):
                                    primary_project = project_item.get("name", "")
                                else:
                                    secondary_project = project_item.get("name", "")
                                    secondary_comment = project_item.get("comment", "")
                                    secondary_percentage = project_item.get(
                                        "percentage", ""
                                    )

                        row = {
                            "session_id": session_id,
                            "date": date,
                            "sphere": sphere,
                            "session_start_time": start_time,
                            "session_end_time": end_time,
                            "session_total_duration": total_duration,
                            "session_active_duration": active_duration,
                            "session_break_duration": break_duration,
                            "type": "active",
                            "project": primary_project,
                            "secondary_project": secondary_project,
                            "secondary_comment": secondary_comment,
                            "secondary_percentage": secondary_percentage,
                            "activity_start": active.get("start", ""),
                            "activity_end": active.get("end", ""),
                            "activity_duration": active.get("duration", 0),
                            "activity_comment": active.get("comment", ""),
                            "break_action": "",
                            "secondary_action": "",
                            "active_notes": active_notes,
                            "break_notes": break_notes,
                            "idle_notes": idle_notes,
                            "session_notes": session_notes,
                        }
                        csv_rows.append(row)

                # Process breaks
                if breaks:
                    for brk in breaks:
                        # Extract primary and secondary action information
                        primary_action = ""
                        secondary_action = ""
                        secondary_comment = ""
                        secondary_percentage = ""

                        if brk.get("action"):
                            # Single action case
                            primary_action = brk.get("action", "")
                        else:
                            # Multiple actions case
                            for action_item in brk.get("actions", []):
                                if action_item.get("action_primary", True):
                                    primary_action = action_item.get("name", "")
                                else:
                                    secondary_action = action_item.get("name", "")
                                    secondary_comment = action_item.get("comment", "")
                                    secondary_percentage = action_item.get(
                                        "percentage", ""
                                    )

                        row = {
                            "session_id": session_id,
                            "date": date,
                            "sphere": sphere,
                            "session_start_time": start_time,
                            "session_end_time": end_time,
                            "session_total_duration": total_duration,
                            "session_active_duration": active_duration,
                            "session_break_duration": break_duration,
                            "type": "break",
                            "project": "",
                            "secondary_project": "",
                            "secondary_comment": secondary_comment,
                            "secondary_percentage": secondary_percentage,
                            "activity_start": brk.get("start", ""),
                            "activity_end": "",
                            "activity_duration": brk.get("duration", 0),
                            "activity_comment": brk.get("comment", ""),
                            "break_action": primary_action,
                            "secondary_action": secondary_action,
                            "active_notes": active_notes,
                            "break_notes": break_notes,
                            "idle_notes": idle_notes,
                            "session_notes": session_notes,
                        }
                        csv_rows.append(row)

                # Process idle periods
                if idle_periods:
                    for idle in idle_periods:
                        row = {
                            "session_id": session_id,
                            "date": date,
                            "sphere": sphere,
                            "session_start_time": start_time,
                            "session_end_time": end_time,
                            "session_total_duration": total_duration,
                            "session_active_duration": active_duration,
                            "session_break_duration": break_duration,
                            "type": "idle",
                            "project": "",
                            "secondary_project": "",
                            "secondary_comment": "",
                            "secondary_percentage": "",
                            "activity_start": idle.get("start", ""),
                            "activity_end": idle.get("end", ""),
                            "activity_duration": idle.get("duration", 0),
                            "activity_comment": "",
                            "break_action": "",
                            "secondary_action": "",
                            "active_notes": active_notes,
                            "break_notes": break_notes,
                            "idle_notes": idle_notes,
                            "session_notes": session_notes,
                        }
                        csv_rows.append(row)

                # If no active periods, breaks, or idle, create summary row
                if not active_periods and not breaks and not idle_periods:
                    row = {
                        "session_id": session_id,
                        "date": date,
                        "sphere": sphere,
                        "session_start_time": start_time,
                        "session_end_time": end_time,
                        "session_total_duration": total_duration,
                        "session_active_duration": active_duration,
                        "session_break_duration": break_duration,
                        "type": "session_summary",
                        "project": "",
                        "secondary_project": "",
                        "secondary_comment": "",
                        "secondary_percentage": "",
                        "activity_start": "",
                        "activity_end": "",
                        "activity_duration": 0,
                        "activity_comment": "",
                        "break_action": "",
                        "secondary_action": "",
                        "active_notes": active_notes,
                        "break_notes": break_notes,
                        "idle_notes": idle_notes,
                        "session_notes": session_notes,
                    }
                    csv_rows.append(row)

            # Write to CSV file
            if csv_rows:
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    fieldnames = [
                        "session_id",
                        "date",
                        "sphere",
                        "session_start_time",
                        "session_end_time",
                        "session_total_duration",
                        "session_active_duration",
                        "session_break_duration",
                        "type",
                        "project",
                        "secondary_project",
                        "secondary_comment",
                        "secondary_percentage",
                        "activity_start",
                        "activity_end",
                        "activity_duration",
                        "activity_comment",
                        "break_action",
                        "secondary_action",
                        "active_notes",
                        "break_notes",
                        "idle_notes",
                        "session_notes",
                    ]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(csv_rows)

                messagebox.showinfo(
                    "Export Successful",
                    f"Data exported successfully to:\n{file_path}\n\n{len(csv_rows)} rows exported",
                )

                # Open file location
                try:
                    directory = os.path.dirname(file_path)
                    if platform.system() == "Windows":
                        os.startfile(directory)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.Popen(["open", directory])
                    else:  # Linux
                        subprocess.Popen(["xdg-open", directory])
                except Exception as e:
                    # Silently fail if can't open directory
                    pass

            else:
                messagebox.showwarning("No Data", "No data rows to export")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data:\n{str(e)}")

    def create_break_actions_list(self, parent):
        """Create break actions management list"""
        row = 0

        # Header with label and filter buttons on same row
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=row, column=0, columnspan=3, pady=5, sticky=tk.W)

        ttk.Label(header_frame, text="Break Actions", font=("Arial", 14, "bold")).pack(
            side=tk.LEFT, padx=(0, 10)
        )

        # Filter buttons
        filter_frame = ttk.Frame(header_frame)
        filter_frame.pack(side=tk.LEFT)

        ttk.Radiobutton(
            filter_frame,
            text="Active",
            variable=self.break_action_filter,
            value="active",
            command=self.refresh_break_actions,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            filter_frame,
            text="All",
            variable=self.break_action_filter,
            value="all",
            command=self.refresh_break_actions,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            filter_frame,
            text="Archived",
            variable=self.break_action_filter,
            value="inactive",
            command=self.refresh_break_actions,
        ).pack(side=tk.LEFT, padx=5)
        row += 1

        # Create new break action button
        ttk.Button(
            parent, text="Create New Break Action", command=self.create_new_break_action
        ).grid(row=row, column=0, columnspan=3, pady=5, sticky=tk.W)
        row += 1

        # Store the starting row for break actions list
        self.break_actions_list_row = row

        # Break actions list
        break_actions = self.tracker.settings.get("break_actions", {})
        filter_val = self.break_action_filter.get()

        # Filter and sort: default first, then alphabetically
        filtered_actions = []
        default_action = None

        for name, data in break_actions.items():
            include = False
            if filter_val == "active" and data.get("active", True):
                include = True
            elif filter_val == "inactive" and not data.get("active", True):
                include = True
            elif filter_val == "all":
                include = True

            if include:
                if data.get("is_default", False):
                    default_action = (name, data)
                else:
                    filtered_actions.append((name, data))

        filtered_actions.sort(key=lambda x: x[0])

        if default_action:
            filtered_actions.insert(0, default_action)

        # Display break actions
        for idx, (action_name, action_data) in enumerate(filtered_actions):
            self.create_break_action_row(
                parent, self.break_actions_list_row + idx, action_name, action_data
            )

        # Rebind mousewheel to new widgets
        if hasattr(self, "bind_mousewheel_func"):
            self.bind_mousewheel_func()

        # Force scroll region update
        if hasattr(self, "update_scrollregion"):
            self.update_scrollregion()

    def toggle_break_action_edit(self, action_name, notes_text, edit_btn):
        """Toggle break action edit mode"""
        if edit_btn["text"] == "Edit":
            # Enable editing
            notes_text.config(state="normal")
            edit_btn.config(text="Save")
        else:
            # Save changes (use .get() for Entry widget, not .get("1.0", "end-1c"))
            notes_content = notes_text.get()
            self.tracker.settings["break_actions"][action_name]["notes"] = notes_content
            self.save_settings()

            # Disable editing
            notes_text.config(state="disabled")
            edit_btn.config(text="Edit")

    def refresh_break_actions(self):
        """Refresh break actions display"""
        if hasattr(self, "break_actions_frame"):
            for child in self.break_actions_frame.winfo_children():
                child.destroy()
            self.create_break_actions_list(self.break_actions_frame)

    def create_break_action_row(self, parent, row, action_name, action_data):
        """Create a row for a break action"""
        frame = ttk.Frame(parent, relief=tk.RIDGE, borderwidth=1, padding=5)
        frame.grid(row=row, column=0, columnspan=3, pady=5, sticky=(tk.W, tk.E))

        # Action name
        ttk.Label(frame, text=action_name, font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, padx=5
        )

        # Notes text box
        ttk.Label(frame, text="Notes:").grid(row=1, column=0, sticky=tk.W, pady=5)
        notes_text = tk.Entry(frame, width=20, state="disabled")
        notes_text.grid(row=1, column=1, columnspan=2, pady=5, sticky=(tk.W, tk.E))

        # Load existing notes
        existing_notes = action_data.get("notes", "")
        notes_text.config(state="normal")
        notes_text.insert(0, existing_notes)
        notes_text.config(state="disabled")

        # Edit/Save button for notes
        edit_btn = ttk.Button(
            frame,
            text="Edit",
            command=lambda: self.toggle_break_action_edit(
                action_name, notes_text, edit_btn
            ),
        )
        edit_btn.grid(row=1, column=3, padx=5, pady=5)

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
            name = sanitize_name(name.strip())
            if not name:
                messagebox.showerror("Error", "Invalid break action name")
                return
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
            self.refresh_break_actions()

    def set_default_break_action(self, action_name):
        """Set a break action as default"""
        # Remove default from all break actions
        for name in self.tracker.settings.get("break_actions", {}):
            self.tracker.settings["break_actions"][name]["is_default"] = False

        # Set new default
        self.tracker.settings["break_actions"][action_name]["is_default"] = True
        self.save_settings()
        self.refresh_break_actions()

    def toggle_break_action_active(self, action_name):
        """Toggle break action active/inactive status"""
        current_status = self.tracker.settings["break_actions"][action_name].get(
            "active", True
        )
        self.tracker.settings["break_actions"][action_name][
            "active"
        ] = not current_status
        self.save_settings()
        self.refresh_break_actions()

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
        self.refresh_break_actions()
