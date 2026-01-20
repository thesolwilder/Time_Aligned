# Quick Start: Google Sheets Integration

Get your Time Tracker uploading to Google Sheets in 5 minutes!

## Step 1: Install Dependencies (1 min)

```bash
pip install -r requirements.txt
```

Verify installation:

```bash
python verify_google_deps.py
```

## Step 2: Get Google Credentials (2 min)

### Fast Track:

1. Go to: https://console.cloud.google.com/
2. Create new project
3. Enable "Google Sheets API" (use search)
4. Go to "Credentials" → "Create Credentials" → "OAuth client ID"
5. Choose "Desktop app"
6. Download JSON → Save as `credentials.json` in project folder

> **Note**: First time? You'll need to configure OAuth consent screen with your email.

## Step 3: Create Your Spreadsheet (30 sec)

1. Go to: https://sheets.google.com/
2. Create new spreadsheet
3. Copy the ID from URL: `docs.google.com/spreadsheets/d/COPY_THIS_PART/edit`

## Step 4: Configure in App (1 min)

1. Run Time Tracker: `python time_tracker.py`
2. Click "Settings"
3. Scroll to "Google Sheets Integration"
4. Fill in:
   - ✓ Enable automatic upload
   - Paste Spreadsheet ID
   - Sheet name: "Sessions" (or your choice)
   - Browse to `credentials.json`
5. Click "Test Connection" → Should say "Connected"
6. Click "Save Google Sheets Settings"

## Step 5: First Session (30 sec)

1. Go back to main screen
2. Start a session
3. End the session
4. Complete and save
5. **Check your Google Sheet** → New row added! 🎉

## Authentication (First Time Only)

- Browser will open automatically
- Sign in to Google
- Grant permissions
- Done! Token saved for future sessions

## Troubleshooting

### "Credentials file not found"

→ Make sure `credentials.json` is in the project root folder

### "Spreadsheet not found"

→ Double-check the Spreadsheet ID (no spaces, correct copy)

### Test Connection fails

→ Make sure you enabled Google Sheets API in Cloud Console

### Authentication window doesn't open

→ Check if popup was blocked, or manually go to the URL shown in terminal

## What Gets Uploaded?

Each session creates a new row with:

- Session info (date, times, duration)
- Your sphere and project
- Active vs break time breakdown
- Action counts
- Any notes you added

## Tips

- ✓ Same spreadsheet for all sessions (keeps growing)
- ✓ Headers auto-created on first upload
- ✓ Works offline (uploads when back online)
- ✓ Can disable anytime in settings
- ✓ Analyze with Google Sheets charts/pivot tables

## Need More Help?

See the full guide: [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)

---

_Estimated total setup time: ~5 minutes_
