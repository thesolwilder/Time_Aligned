"""
Generate the Time Aligned application icon.

Creates assets/icon.ico using Pillow (already a project dependency).
The icon is a coloured circle matching the app's tray icon style.

Run this script to regenerate the icon:
    python assets/generate_icon.py
"""

import os
import sys

from PIL import Image, ImageDraw

# Resolve output path relative to project root regardless of cwd
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "icon.ico")

# Icon appearance
BACKGROUND_COLOR = (255, 255, 255, 0)  # Transparent background
CIRCLE_COLOR = (46, 125, 50)  # #2E7D32 — matches COLOR_ACTIVE_GREEN
OUTLINE_COLOR = (255, 255, 255)
OUTLINE_WIDTH = 4

# ICO format requires multiple sizes for best rendering across Windows contexts
ICO_SIZES = [16, 32, 48, 64, 128, 256]


def create_icon_image(size):
    """Create a single circular icon image at the given pixel size.

    Args:
        size: Width and height in pixels.

    Returns:
        PIL Image in RGBA mode.
    """
    image = Image.new("RGBA", (size, size), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)
    margin = max(2, size // 16)
    bounding_box = [margin, margin, size - margin - 1, size - margin - 1]
    draw.ellipse(
        bounding_box,
        fill=CIRCLE_COLOR,
        outline=OUTLINE_COLOR,
        width=max(1, OUTLINE_WIDTH * size // 64),
    )
    return image


def generate_ico():
    """Generate icon.ico with all required sizes for Windows."""
    images = [create_icon_image(size) for size in ICO_SIZES]
    # Save as ICO — PIL writes all sizes into the single .ico container
    images[0].save(
        OUTPUT_PATH,
        format="ICO",
        sizes=[(s, s) for s in ICO_SIZES],
        append_images=images[1:],
    )
    print(f"Icon saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_ico()
