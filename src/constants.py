"""
Constants for the Time Aligned application.

This module contains all hardcoded numeric values, time conversions,
UI colors, and configuration defaults to eliminate magic numbers
throughout the codebase.
"""

# =============================================================================
# Time Conversion Constants
# =============================================================================

SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
MINUTES_PER_HOUR = 60
MILLISECONDS_PER_SECOND = 1000

# Derived time constants
ONE_MINUTE_MS = SECONDS_PER_MINUTE * MILLISECONDS_PER_SECOND
ONE_MINUTE_SECONDS = SECONDS_PER_MINUTE

# =============================================================================
# Timer and Update Intervals
# =============================================================================

UPDATE_TIMER_INTERVAL_MS = 100  # milliseconds between UI updates
IDLE_CHECK_INTERVAL_SECONDS = 0.5  # seconds between idle checks

# =============================================================================
# Default Idle Settings
# =============================================================================

DEFAULT_IDLE_THRESHOLD_SECONDS = 60  # seconds before considering idle
DEFAULT_IDLE_BREAK_THRESHOLD_SECONDS = 300  # seconds of idle before auto-break

# =============================================================================
# UI Color Palette
# =============================================================================

# Status colors for timeline (used in analysis_frame.py)
COLOR_ACTIVE_LIGHT_GREEN = "#e8f5e9"  # Light green for active sessions
COLOR_BREAK_LIGHT_ORANGE = "#fff3e0"  # Light orange for break sessions

# UI accent colors
COLOR_LINK_BLUE = "#0066CC"  # Hyperlink blue
COLOR_GRAY_TEXT = "#666666"  # Secondary text gray
COLOR_GRAY_BACKGROUND = "#d0d0d0"  # Background gray for containers
COLOR_ACTIVE_GREEN = "#2E7D32"  # Active time display
COLOR_BREAK_ORANGE = "#F57C00"  # Break time display
COLOR_ERROR_RED = "red"  # Error messages
COLOR_SUCCESS_GREEN = "green"  # Success messages
COLOR_INFO_BLUE = "blue"  # Info messages

# System tray icon colors
COLOR_TRAY_IDLE = "#607D8B"  # Blue-gray for idle state
COLOR_TRAY_ACTIVE = "#4CAF50"  # Green for active session
COLOR_TRAY_BREAK = "#FFC107"  # Amber/Yellow for break
COLOR_TRAY_SESSION_IDLE = "#FFEB3B"  # Yellow for idle during session

# =============================================================================
# UI Fonts
# =============================================================================

FONT_FAMILY = "Arial"
FONT_LINK = (FONT_FAMILY, 10, "underline")
FONT_EXTRA_SMALL = (FONT_FAMILY, 8)  # Very small text (help text, footnotes)
FONT_SMALL = (FONT_FAMILY, 9)
FONT_SMALL_ITALIC = (FONT_FAMILY, 9, "italic")
FONT_NORMAL = (FONT_FAMILY, 10)
FONT_NORMAL_BOLD = (FONT_FAMILY, 10, "bold")
FONT_NORMAL_ITALIC = (FONT_FAMILY, 10, "italic")
FONT_MONOSPACE = ("Consolas", 10, "bold")  # Monospace font for shortcuts/code
FONT_HEADING = (FONT_FAMILY, 12, "bold")
FONT_BODY = (FONT_FAMILY, 12)
FONT_TITLE = (FONT_FAMILY, 16, "bold")
FONT_TIMER_LARGE = (FONT_FAMILY, 48, "bold")
FONT_TIMER_MEDIUM = (FONT_FAMILY, 28, "bold")
FONT_TIMER_SMALL = (FONT_FAMILY, 14, "bold")

# =============================================================================
# UI Dimensions and Layout
# =============================================================================

DEFAULT_WINDOW_WIDTH = 800
DEFAULT_WINDOW_HEIGHT = 600

# Mousewheel scrolling sensitivity
MOUSEWHEEL_DELTA_DIVISOR = 120  # Windows standard for mouse wheel delta

# Tray icon dimensions
TRAY_ICON_SIZE = 64  # Icon size in pixels
TRAY_ICON_MARGIN = 8  # Margin around circle
TRAY_ICON_OUTLINE_WIDTH = 2  # Circle outline thickness

# Pie chart dimensions (analysis frame cards)
PIE_CHART_SIZE = 120  # Canvas width and height in pixels
PIE_CHART_MARGIN = 6  # Gap between canvas edge and arc bounding box
PIE_TEXT_MIN_PERCENT = 10  # Minimum slice size (%) to render percentage text inside

# =============================================================================
# Default File Paths
# =============================================================================

DEFAULT_SETTINGS_FILE = "settings.json"
DEFAULT_DATA_FILE = "data.json"
DEFAULT_SCREENSHOT_FOLDER = "screenshots"
DEFAULT_BACKUP_FOLDER = "backups"
DEFAULT_GOOGLE_CREDENTIALS_FILE = "credentials.json"
