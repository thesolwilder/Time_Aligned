# System Tray Feature Guide

## Overview

Time Aligned now runs with a system tray icon, allowing you to control your time tracking from the Windows taskbar notification area without keeping the main window open.

## Pinning the Icon to Taskbar

**Windows 11:**

1. Click the up arrow (^) in the system tray to show hidden icons
2. Right-click on the Time Aligned icon
3. The icon will appear in the overflow menu
4. To keep it always visible: Go to Settings → Personalization → Taskbar → Other system tray icons
5. Toggle "Time Aligned" to ON

**Or use drag and drop:**

1. Click and hold the Time Aligned icon from the overflow area
2. Drag it to the main taskbar notification area

## Features

### Icon States

The tray icon changes color based on your current state:

- **Gray** - Idle (no active session)
- **Green** - Active session running
- **Yellow/Amber** - On break

### Quick Access Menu

Right-click the tray icon to access:

- **Show/Hide Window** (also double-click) - Toggle main window visibility
- **Start Session** - Quick start a new tracking session
- **Start Break** - Begin a break (only available during active session)
- **End Break** - End current break (only when on break)
- **End Session** - Complete and save your session (auto-shows window)
- **Settings** - Open settings configuration
- **Analysis** - View your time tracking analysis
- **Quit** - Exit the application

## Global Keyboard Shortcuts

Control Time Aligned from anywhere with these hotkeys:

- **Ctrl+Shift+S** - Start a new session
- **Ctrl+Shift+B** - Toggle break (start/end)
- **Ctrl+Shift+E** - End current session
- **Ctrl+Shift+W** - Show/hide main window

_Note: These work system-wide, even when the window is hidden!_

### Benefits

1. **Background Operation**
   - Minimize to tray instead of taskbar
   - Keep tracking without visible windows
   - Reduce desktop clutter

2. **Quick Actions**
   - Start/pause/end sessions from anywhere
   - No need to find the window
   - Perfect for rapid workflows

3. **Visual Status**
   - Icon color shows state at a glance
   - Hover tooltip shows current timer
   - Always visible in notification area

4. **Keyboard Power User**
   - Control everything with hotkeys
   - Never touch the mouse
   - Fastest possible workflow

## Usage Tips

### For Super Users

1. **Minimize on start**: Start a session, then hide the window (`Ctrl+Shift+W`)
2. **Tray-only workflow**: Use only tray menu or hotkeys for all controls
3. **Check status**: Hover over icon to see current time
4. **Quick breaks**: Press `Ctrl+Shift+B` when stepping away
5. **End sessions fast**: `Ctrl+Shift+E` → window appears for completion frame

### Window Behavior

- Closing the window (X button) still asks for confirmation if session is active
- Use "Show/Hide Window" or `Ctrl+Shift+W` to minimize without quitting
- Window automatically appears when:
  - Opening Settings or Analysis
  - Ending a session (to show completion frame)

## Technical Details

- Built with `pystray` library
- Global hotkeys via `pynput.keyboard.GlobalHotKeys`
- Runs in separate thread (non-blocking)
- Icon updates every 100ms with timer
- Cross-platform compatible (Windows, macOS, Linux)

## Troubleshooting

**Icon doesn't appear:**

- Check Windows notification area settings
- Ensure pystray is installed: `pip install pystray`

**Menu items disabled:**

- Start Session: Disabled when session already active
- Break controls: Only enabled when appropriate
- This prevents invalid state transitions

**Icon doesn't update:**

- Icon refreshes with timer loop
- Should update within 100-200ms of state changes

**Hotkeys don't work:**

- Ensure pynput is installed
- Check if another app is using the same shortcuts
- Hotkeys work globally, even when window is hidden
