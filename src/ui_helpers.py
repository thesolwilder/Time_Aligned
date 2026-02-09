"""UI helper utilities for creating common widgets"""

import tkinter as tk
from tkinter import ttk
import re
import traceback


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

    def __init__(self, parent, debug_name=None, **kwargs):
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

        # Debug name for tracing which instance is which
        self._debug_name = debug_name or "ScrollableFrame"

        # Flag to track if this instance is destroyed
        self._is_alive = True

        # Counter to avoid noisy scroll logging
        self._mousewheel_event_count = 0

        # Setup mousewheel scrolling
        self._setup_mousewheel()

    def destroy(self):
        """Clean up before destroying"""
        # Mark as no longer alive so handlers can ignore it
        self._is_alive = False
        # Call parent destroy
        super().destroy()

    def _setup_mousewheel(self):
        """Setup mousewheel scrolling"""

        def on_mousewheel(event):
            # Check if mouse is over this scrollable frame
            try:
                # CRITICAL: Check if this specific ScrollableFrame instance is still alive
                # Don't use winfo_exists() as it may throw errors on destroyed widgets
                if not self._is_alive:
                    return  # This instance is destroyed, silently ignore

                # Validate canvas before scrolling
                if not hasattr(self, "canvas"):
                    return

                # Check canvas exists (this can fail if destroyed)
                try:
                    canvas_exists = self.canvas.winfo_exists()
                    if not canvas_exists:
                        return
                except (tk.TclError, AttributeError):
                    return

                # Get widget under mouse
                x, y = self.winfo_pointerxy()
                widget = self.winfo_containing(x, y)

                # Check if it's a combobox
                if widget and isinstance(widget, ttk.Combobox):
                    return

                # Check if the widget is a descendant of this ScrollableFrame
                if widget:
                    parent = widget
                    found_self = False
                    depth = 0
                    max_depth = 20
                    while parent and depth < max_depth:
                        if parent == self:
                            found_self = True
                            # Mouse is over this frame, scroll it
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

            except (tk.TclError, AttributeError, RuntimeError):
                # Widget destroyed or other errors, silently ignore
                return
            except Exception:
                # Any other error, silently ignore
                return

        # Bind to the root window to capture all mousewheel events
        def setup_root_binding():
            try:
                root = self.winfo_toplevel()
                # Use bind_all to ensure we capture events everywhere
                # Note: Multiple ScrollableFrames will share this binding
                # Each handler checks if its instance is alive before acting
                root.bind_all("<MouseWheel>", on_mousewheel, add="+")
            except Exception:
                pass

        # Delay binding until widget is visible
        self.after(100, setup_root_binding)

        # Also bind directly to our widgets as backup
        self.bind("<MouseWheel>", on_mousewheel, add="+")
        self.canvas.bind("<MouseWheel>", on_mousewheel, add="+")
        self.content_frame.bind("<MouseWheel>", on_mousewheel, add="+")

        # Disable scrolling on all comboboxes
        self._disable_combobox_scrolling()

    def _disable_combobox_scrolling(self):
        """Find and disable mousewheel on all comboboxes in the content frame"""

        def disable_recursive(widget):
            try:
                if isinstance(widget, ttk.Combobox):
                    # Bind to prevent scrolling, returning "break" stops event propagation
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
        # Re-disable combobox scrolling for any newly added comboboxes
        self._disable_combobox_scrolling()

    def get_content_frame(self):
        """Get the content frame to add widgets to"""
        return self.content_frame
