"""UI helper utilities for creating common widgets"""

import tkinter as tk
from tkinter import ttk
import re


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

        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self)
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

        # Setup mousewheel scrolling
        self._setup_mousewheel()

    def _setup_mousewheel(self):
        """Setup mousewheel scrolling"""

        def on_mousewheel(event):
            # Check if a combobox dropdown is open
            try:
                widget = event.widget
                # If the event came from a combobox, don't scroll
                if isinstance(widget, ttk.Combobox):
                    return "break"
            except:
                pass

            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"  # Prevent event propagation

        # Bind directly to canvas for global coverage
        self.canvas.bind("<MouseWheel>", on_mousewheel)

        def bind_mousewheel(widget):
            # Skip Combobox widgets - they handle their own mousewheel
            if isinstance(widget, ttk.Combobox):
                # Disable mousewheel on comboboxes to prevent accidental changes
                widget.bind("<MouseWheel>", lambda e: "break")
            else:
                # Bind to all other widgets
                widget.bind("<MouseWheel>", on_mousewheel)

            # Recursively bind to children
            for child in widget.winfo_children():
                bind_mousewheel(child)

        bind_mousewheel(self)
        bind_mousewheel(self.content_frame)

        # Store the binding function so it can be called after adding new widgets
        self._bind_mousewheel_func = lambda: bind_mousewheel(self.content_frame)

    def rebind_mousewheel(self):
        """Rebind mousewheel to all widgets (call after adding new widgets)"""
        if hasattr(self, "_bind_mousewheel_func"):
            self._bind_mousewheel_func()

    def get_content_frame(self):
        """Get the content frame to add widgets to"""
        return self.content_frame
