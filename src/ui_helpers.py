"""UI helper utilities for creating common widgets"""

import tkinter as tk
from tkinter import ttk
import re


def get_taskbar_color():
    """
    Detect the Windows OS taskbar background colour.

    Reads the SystemUsesLightTheme registry value to choose between a
    light and dark taskbar colour.  Falls back to a fully-transparent
    RGBA tuple when the registry key is unavailable (non-Windows, or
    permission error) so the icon still blends naturally.

    Returns:
        tuple: RGBA colour tuple (R, G, B, A).  Transparent (0, 0, 0, 0)
               is returned on failure so PIL can composite correctly.
    """
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        use_light_theme = winreg.QueryValueEx(key, "SystemUsesLightTheme")[0]
        winreg.CloseKey(key)
        if use_light_theme:
            return (242, 242, 242, 255)  # Light Windows taskbar
        else:
            return (32, 32, 32, 255)  # Dark Windows taskbar
    except Exception:
        return (0, 0, 0, 0)  # Transparent fallback for non-Windows / errors


def get_frame_background():
    """
    Get the background color for ttk frames based on current theme.

    Returns:
        str: Hex color code for frame background (e.g., "#d9d9d9")

    Note:
        Must be called after tkinter root window is initialized.
    """
    style = ttk.Style()
    return style.lookup("TFrame", "background")


def sanitize_name(name, max_length=50):
    """
    Sanitize user input for names (spheres, projects, break actions).
    Removes dangerous characters that could cause path traversal or injection attacks.

    Args:
        name: The name to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized name string
    """
    if not name:
        return ""

    # Convert to string and strip whitespace first
    sanitized = str(name).strip()

    if not sanitized:
        return ""

    # Remove dangerous characters for file paths and data structures
    dangerous_chars = [
        "/",
        "\\",
        "..",
        "~",
        ":",
        "*",
        "?",
        '"',
        "<",
        ">",
        "|",
        "{",
        "}",
    ]

    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "_")

    # Replace control characters (newlines, tabs, etc.) with underscores
    sanitized = re.sub(r"[\n\r\t]", "_", sanitized)

    # Limit length
    sanitized = sanitized[:max_length]

    return sanitized


def escape_for_sheets(text):
    """
    Escape text for safe upload to Google Sheets.
    Prevents formula injection and XSS attacks.

    Args:
        text: The text to escape

    Returns:
        Escaped text string safe for Google Sheets
    """
    if not text:
        return ""

    text = str(text)

    # Prevent formula injection - formulas start with =, +, -, @, or |
    if text and text[0] in ("=", "+", "-", "@", "|"):
        text = "'" + text  # Prefix with single quote to treat as text

    # Escape HTML/XML special characters to prevent XSS
    text = text.replace("<", "&lt;").replace(">", "&gt;")

    return text


def validate_folder_path(path):
    """
    Validate a folder path to prevent directory traversal attacks.

    Args:
        path: The path to validate

    Returns:
        bool: True if path is safe, False otherwise
    """
    if not path:
        return False

    # Disallow path traversal patterns
    dangerous_patterns = [
        "..",
        "~",
        "/etc/",
        "C:\\Windows\\",
        "%",
        "${",
        "$env:",
        "/root/",
    ]
    path_lower = path.lower()

    for pattern in dangerous_patterns:
        if pattern.lower() in path_lower:
            return False

    return True


class ScrollableFrame(ttk.Frame):
    """A scrollable frame that can contain other widgets"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent)

        # Get frame background color to match theme
        frame_bg = get_frame_background()

        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self, bg=frame_bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )

        # Create content frame
        self.content_frame = ttk.Frame(self.canvas, **kwargs)

        # Configure canvas
        self.content_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.content_frame, anchor="nw"
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Update canvas window width when canvas resizes
        def on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)

        self.canvas.bind("<Configure>", on_canvas_configure)

        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Flag to track if this instance is destroyed
        self._is_alive = True

        # Counter to avoid noisy scroll logging
        self._mousewheel_event_count = 0

        # Setup mousewheel scrolling
        self._setup_mousewheel()

    def destroy(self):
        """Clean up frame lifecycle by marking dead and calling parent destroy."""
        # Mark as no longer alive so handlers can ignore it
        self._is_alive = False
        # Call parent destroy
        super().destroy()

    def _setup_mousewheel(self):
        """Setup mousewheel scrolling"""

        def on_mousewheel(event):
            try:
                if not self._is_alive or not hasattr(self, "canvas"):
                    return

                try:
                    if not self.canvas.winfo_exists():
                        return
                except (tk.TclError, AttributeError):
                    return

                x, y = self.winfo_pointerxy()
                widget = self.winfo_containing(x, y)

                if widget and isinstance(widget, ttk.Combobox):
                    return

                if widget:
                    parent = widget
                    depth = 0
                    max_depth = 20
                    while parent and depth < max_depth:
                        if parent == self:
                            self.canvas.yview_scroll(
                                int(-1 * (event.delta / 120)), "units"
                            )
                            self._mousewheel_event_count += 1
                            return
                        try:
                            parent = parent.master
                            depth += 1
                        except (AttributeError, tk.TclError):
                            break

            except (tk.TclError, AttributeError, RuntimeError, Exception):
                return

        def setup_root_binding(event=None):
            try:
                root = self.winfo_toplevel()
                root.bind_all("<MouseWheel>", on_mousewheel, add="+")
            except Exception:
                pass

        self.bind("<Map>", setup_root_binding, add="+")
        self.bind("<MouseWheel>", on_mousewheel, add="+")
        self.canvas.bind("<MouseWheel>", on_mousewheel, add="+")
        self.content_frame.bind("<MouseWheel>", on_mousewheel, add="+")

        # Disable scrolling on all comboboxes
        self._disable_combobox_scrolling()

    def _disable_combobox_scrolling(self):
        """Find and disable mousewheel on all comboboxes and spinboxes in the content frame"""

        def disable_recursive(widget):
            try:
                if isinstance(widget, (ttk.Combobox, ttk.Spinbox)):
                    widget.bind("<MouseWheel>", lambda e: "break")

                for child in widget.winfo_children():
                    disable_recursive(child)
            except:
                pass

        try:
            disable_recursive(self.content_frame)
        except:
            pass

    def rebind_mousewheel(self):
        """Rebind mousewheel to all widgets (call after adding new widgets)"""
        self._disable_combobox_scrolling()

    def get_content_frame(self):
        """Get the scrollable content frame for adding child widgets."""
        return self.content_frame
