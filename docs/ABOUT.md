# About Time Aligned

**Time Aligned** is a comprehensive desktop time tracker for Windows — built to help you understand where your time actually goes. Track work sessions, breaks, and idle time with automatic detection, then analyze your productivity across projects and spheres.

All data is stored locally. Google Sheets upload is opt-in. No account required.

---

## ✨ Features

### Core Tracking

- Start, pause, and end work sessions with a single click
- Separate break and idle time from active work
- Auto idle detection — configurable threshold, optional auto-break
- Tag any period with a secondary project and time split for more accurate records
- Editable history — go back and update past sessions at any time
- Note taking on individual periods and overall sessions

### Headless Operation

- Global hotkeys (`Ctrl+Shift+S` / `B` / `E` / `W`) — run fully in the background from the system tray
- Tray icon changes colour with your current state (active / break / idle)

### Analysis

- Session history with sortable columns and date / sphere / project filters
- Active vs break efficiency pie chart per session card
- Timeline view with paginated loading (50 periods at a time)
- Export filtered data to CSV at any time

### Integrations

- **Google Sheets** — sessions auto-upload on save (opt-in, OAuth 2.0)
- **Screenshot capture** — captures on focus change or at timed intervals (opt-in)
- **Auto backup** — continuous saves during a session; timestamped backup created on deletion

### Security

- All sphere, project, and action names are sanitized to strip dangerous characters
- Folder paths validated to block directory traversal attempts
- Data escaped before Google Sheets upload to prevent formula injection
- Credential and settings files are gitignored and never committed

---

## 🚀 Installation

1. Download `TimeAligned-vX.Y.Z.zip` from the [latest release](https://github.com/thesolwilder/Time_Aligned-/releases/latest)
2. Extract the folder anywhere — e.g. `C:\Program Files\TimeAligned`
3. Run **TimeAligned.exe**
4. No installer needed — fully portable

---

### ⚠️ Chrome Download Warning

Chrome's Enhanced Safe Browsing blocks unsigned executables and may cancel the download entirely. To fix this temporarily:

1. In Chrome, go to `chrome://settings/security` in the address bar
2. Under **Safe Browsing**, select **Standard protection**
3. Go back to the release page and download again
4. When Chrome warns you, click the **downloads arrow** → **flag icon** → **Keep anyway**
5. After downloading, you can switch back to **Enhanced protection** in the same settings page

> **Alternatively**, use **Microsoft Edge** — it handles GitHub release zips without blocking the download.

---

### ⚠️ Windows SmartScreen Warning

On first run Windows may show _"Windows protected your PC"_:

1. Click **More info**
2. Click **Run anyway**

This appears because the exe is not yet code-signed. The app contains no malware —
you can verify by scanning the zip at [VirusTotal](https://www.virustotal.com) before running.

---

## 📋 System Requirements

- Windows 10 or later
- No Python installation needed — everything is bundled in the zip

---

## 📖 Documentation

| Guide                                         | Description                                   |
| --------------------------------------------- | --------------------------------------------- |
| [Google Sheets Setup](GOOGLE_SHEETS_SETUP.md) | Connect to Google Sheets for automatic upload |
| [Screenshot Feature](SCREENSHOT_FEATURE.md)   | Configure and use screenshot capture          |
| [System Tray Guide](SYSTEM_TRAY_GUIDE.md)     | Use the app headlessly from the system tray   |
| [Testing Guide](TESTING_GUIDE.md)             | Run the test suite (developers)               |

---

## 📄 License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — Free for personal, non-commercial use.

- ✅ Free to use for personal purposes
- ✅ Free to modify and share with attribution
- ❌ Commercial use requires explicit written permission
