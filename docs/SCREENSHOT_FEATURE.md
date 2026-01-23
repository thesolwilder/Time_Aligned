# Screenshot Capture Feature - User Guide

## Overview

The Time Aligned time tracker now automatically captures screenshots when you switch between windows. Screenshots are organized by date, session, and period, with links stored in your session data for easy review.

## How It Works

### Automatic Capture

- **Trigger**: Screenshots are captured when window focus changes (you click between different applications)
- **Debouncing**: Minimum 10 seconds between captures (configurable) to avoid excessive screenshots
- **Organization**: Organized in nested folders by date → session → period

### Folder Structure

```
screenshots/
└── YYYY-MM-DD/              # Date of session
    └── session_<timestamp>/  # Unique session ID
        ├── period_active_0/  # First active period
        │   ├── 20260120_143022_chrome_Google.png
        │   ├── 20260120_143045_Code_VSCode.png
        │   └── ...
        ├── period_break_0/   # First break period
        │   └── ...
        └── period_active_1/  # Second active period
            └── ...
```

### Data Model Integration

Each period in your `data.json` now includes:

```json
{
  "start": "14:30:22",
  "end": "14:45:18",
  "duration": 896,
  "screenshot_folder": "screenshots/2026-01-20/session_1737383422/period_active_0",
  "screenshots": [
    {
      "filepath": "screenshots/.../20260120_143022_chrome_Google.png",
      "relative_path": "screenshots/.../20260120_143022_chrome_Google.png",
      "timestamp": "20260120_143022",
      "window_title": "Google - Chrome",
      "process_name": "chrome.exe"
    }
  ]
}
```

## Configuration

Settings are in [settings.json](settings.json) under `"screenshot_settings"`:

```json
{
  "screenshot_settings": {
    "enabled": true, // Enable/disable screenshot capture
    "capture_on_focus_change": true, // Capture when window focus changes
    "min_seconds_between_captures": 10, // Minimum seconds between captures
    "screenshot_path": "screenshots" // Base folder for screenshots
  }
}
```

### Configuration Options

| Setting                        | Type    | Default         | Description                                   |
| ------------------------------ | ------- | --------------- | --------------------------------------------- |
| `enabled`                      | boolean | `true`          | Enable or disable screenshot capture entirely |
| `capture_on_focus_change`      | boolean | `true`          | Capture screenshots when you switch windows   |
| `min_seconds_between_captures` | integer | `10`            | Prevents too many screenshots (debounce time) |
| `screenshot_path`              | string  | `"screenshots"` | Base folder where screenshots are stored      |

## Usage

### Starting a Session

1. Start a session as usual with the "Start Session" button
2. Screenshot monitoring starts automatically (if enabled)
3. Switch between windows/applications during your work
4. Screenshots are captured automatically in the background

### During a Session

- **Active Periods**: Screenshots saved to `period_active_<index>` folder
- **Break Periods**: Screenshots saved to `period_break_<index>` folder
- Each period gets its own folder for organization

### Reviewing Screenshots

After a session ends, you can:

1. Check the `screenshot_folder` path in your session data
2. Navigate to that folder to view all screenshots from that period
3. Images are named with timestamp, process, and window title for easy identification

## Testing

Run the test script to verify screenshot capture:

```bash
python test_screenshot.py
```

This will:

1. Create a test session
2. Monitor for 30 seconds
3. Capture screenshots when you switch windows
4. Display results showing what was captured

## Storage Considerations

### Typical Storage Usage

- Screenshot size: 100-500 KB per image (depending on screen resolution)
- 8-hour workday with focus change every 2 minutes: ~240 screenshots = 24-120 MB/day
- Higher resolution displays produce larger files

### Managing Storage

1. **Adjust capture frequency**: Increase `min_seconds_between_captures` to 30-60 seconds
2. **Disable for routine work**: Set `enabled: false` when not needed
3. **Manual cleanup**: Periodically delete old screenshot folders
4. **Selective capture**: (Future enhancement) Only enable for specific projects

## Privacy Notes

⚠️ **Important Privacy Considerations:**

- Screenshots capture EVERYTHING visible on your screen
- May include sensitive information (passwords, private messages, banking, etc.)
- Be cautious when reviewing/sharing screenshots
- Consider disabling during sensitive tasks
- Screenshot files are stored locally in your project folder

### Recommended Practices

- Review screenshot settings before important sessions
- Don't commit screenshot folders to version control (add to `.gitignore`)
- Clean up screenshots containing sensitive information
- Be aware of what's on your screen when working

## Troubleshooting

### Harmless "Unhandled exception in listener callback" Messages

If you see console messages like:

```
Unhandled exception in listener callback
```

These are harmless compatibility messages from the `pynput` library when running on Python 3.13. They do NOT affect functionality - the app works correctly and all features (time tracking, idle detection, screenshot capture) function normally. These messages can be safely ignored.

### Screenshots Not Capturing

1. Check `settings.json` - ensure `"enabled": true`
2. Verify dependencies are installed: `pip install -r requirements.txt`
3. Check permissions - Windows may block screenshot capture for some apps
4. Look for error messages in the console

### Too Many Screenshots

- Increase `min_seconds_between_captures` to 30 or 60 seconds
- This creates larger gaps between captures

### Missing Screenshots for a Period

- If you stay in one window the entire period, only 1-2 screenshots will be captured
- This is normal - focus must change to trigger capture

## Future Enhancements (Potential)

- [ ] Screenshot viewer UI in Analysis Frame
- [ ] Slideshow mode for period review
- [ ] Automatic cleanup of old screenshots
- [ ] Compression/optimization options
- [ ] Blacklist/whitelist for specific applications
- [ ] Selective capture by project/sphere
- [ ] Screenshot thumbnails in data view
