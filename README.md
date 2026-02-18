# Time Aligned - Time Tracker

A comprehensive time tracking application with advanced features for tracking work sessions, breaks, and productivity.

## Features

### Core Tracking

- **Session Tracking**: Start, pause, and end work sessions
- **Break Management**: Track breaks separately from active work time
- **Idle Detection**: Automatically detect when you're away from your computer
- **Multiple Spheres & Projects**: Organize your work into categories and projects

### Screenshot Capture

- Optional screenshot capture during sessions
- Captures on window focus changes
- Helps you remember what you were working on
- Configurable capture intervals

### Google Sheets Integration ✨ NEW

- Automatically upload session data to Google Sheets
- All sessions append to the same spreadsheet
- Track your productivity over time
- Easy to analyze with Google Sheets tools

### Analysis Tools

- View session history and statistics
- Analyze time spent across different projects
- Review screenshots from past sessions
- Export data for further analysis
- **Dynamic text wrapping** - All comments display with proper word wrapping
- **Paginated loading** - Loads 50 periods at a time for optimal performance

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python time_tracker.py
   ```

## Google Sheets Setup

To enable automatic upload to Google Sheets:

1. Follow the detailed setup guide in [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)
2. Download credentials from Google Cloud Console
3. Configure settings in the app
4. Start tracking and your data will automatically upload!

## Usage

### Starting a Session

1. Select a sphere (category) and project
2. Click "Start Session"
3. Work on your task

### Taking Breaks

- Click "Start Break" when you need a break
- The app will track break time separately
- Idle detection can automatically start breaks

### Ending a Session

1. Click "End Session"
2. Review and label your activities
3. Add notes about what you accomplished
4. Data automatically saves and uploads (if Google Sheets is enabled)

### Settings

Access settings to configure:

- Idle detection thresholds
- Screenshot capture options
- Google Sheets integration
- Spheres and projects
- Break actions

## Data Storage

- **Local**: All data is stored in `data.json`
- **Google Sheets**: Optional automatic upload to your Google Spreadsheet
- **Screenshots**: Stored in the `screenshots/` folder (organized by date and session)

## Performance Characteristics

### Timeline Loading

The analysis timeline uses **dynamic text height calculation** to ensure all comment text is visible with proper word wrapping:

- **Initial Load**: ~3.5-4 seconds for 50 periods (first page)
- **Load More**: ~1-2 seconds per additional 50 periods
- **Trade-off**: Prioritizes **accurate text display** over faster loading

**Why this design?**

Users click "Show Timeline" specifically to **review data** - this is an intentional action where they expect to spend time analyzing information. The 3-4 second load ensures:

✅ All comment text is fully visible (no truncation)  
✅ Proper word wrapping for readability  
✅ Consistent layout across all text fields  
✅ Accurate height calculation (not estimation)

This is a deliberate engineering decision prioritizing **data quality and usability** over arbitrary speed targets.

### Code Design Philosophy

This codebase prioritizes **working, tested code** over dogmatic adherence to arbitrary metrics:

- **Function length**: Some methods (like `export_to_csv()` at 280 lines) are intentionally longer when they handle sequential workflows with similar-but-different logic. Linear structure can be clearer than jumping between many small helper methods.
- **Pragmatic refactoring**: Code with full test coverage and clear logic is left as-is rather than refactored for the sake of refactoring. Development effort focuses on improvements with meaningful ROI.
- **"Do better next time"**: Rather than gold-plating existing working code, write smaller functions going forward.

This approach values **readability, maintainability, and test coverage** over rigid adherence to style guide maximums.

## Privacy & Security

- All data is stored locally by default
- Google Sheets integration is opt-in
- Screenshots are stored locally only (not uploaded)
- Your credentials files are protected (see `.gitignore`)

## Files Overview

- `time_tracker.py` - Main application
- `settings_frame.py` - Settings UI
- `analysis_frame.py` - Analysis and reporting
- `frames/completion_frame.py` - Session completion interface
- `google_sheets_integration.py` - Google Sheets upload handler
- `screenshot_capture.py` - Screenshot functionality
- `settings.json` - User settings
- `data.json` - Session data database

## Documentation

- [Google Sheets Setup Guide](GOOGLE_SHEETS_SETUP.md) - Complete setup instructions
- [Screenshot Feature Guide](SCREENSHOT_FEATURE.md) - Screenshot feature details
- [System Tray Guide](SYSTEM_TRAY_GUIDE.md) - Using the system tray icon
- [Testing Guide](TESTING_GUIDE.md) - Running tests
- [Debugging Guide](DEBUGGING_GUIDE.md) - Troubleshooting

## Requirements

- Python 3.7+
- Windows (for system tray and some features)
- See `requirements.txt` for Python package dependencies

## Contributing

Contributions are welcome! Please see:

- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development standards and testing procedures
- **[docs/AGENT_STANDING_ORDERS.md](docs/AGENT_STANDING_ORDERS.md)** - Guide for AI-assisted development

This project follows **Test-Driven Development (TDD)**:

1. Import test → 2. Unit tests → 3. Integration tests → 4. E2E tests

All contributions must include appropriate tests. See DEVELOPMENT.md for details.

## License

[Add your license information here]

## Changelog

### Latest Updates

- ✨ Added Google Sheets integration for automatic session upload
- 📊 Sessions automatically append to the same spreadsheet
- 🔐 Secure OAuth 2.0 authentication with Google
- 📝 Comprehensive setup documentation
