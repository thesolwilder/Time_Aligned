# Quick Start: Google Sheets Integration

Get your Time Tracker uploading to Google Sheets in 5 minutes!

## What Gets Uploaded?

The tracker uploads **detailed session data** matching the **Save All Data to CSV** export in Settings:

- **One row per activity**: Each active period, break, and idle period gets its own row
- **Full project details**: Primary and secondary projects with comments and percentages
- **Full action details**: Primary and secondary break actions
- **Comprehensive notes**: Active, break, idle, and session-level notes
- **Activity timing**: Start and end times (break rows show only the start) and durations for each activity

This gives you powerful analysis capabilities in Google Sheets!

## Step 1: Install Dependencies (1 min)

Skip this step if you use the downloaded `TimeAligned.exe`: the Google libraries are already included. When running from source:

```bash
pip install -r requirements.txt
```

## Step 2: Get Google Credentials (2 min)

### Fast Track:

1. Go to: https://console.cloud.google.com/
2. Create new project
3. Enable "Google Sheets API" (use search)
4. Go to "Credentials" → "Create Credentials" → "OAuth client ID"
5. Choose "Desktop app"
6. Download JSON → Save as `credentials.json` next to `TimeAligned.exe` (or in the project folder when running from source)

> **Note**: First time? You'll need to configure the OAuth consent screen and add your Google account under **Test users**.

## Step 3: Create Your Spreadsheet (30 sec)

1. Go to: https://sheets.google.com/
2. Create new spreadsheet
3. Copy the ID from URL: `docs.google.com/spreadsheets/d/COPY_THIS_PART/edit` (or copy the whole URL; the app extracts the ID)

## Step 4: Configure in App (1 min)

1. Open Time Aligned (`TimeAligned.exe`, or `python time_tracker.py` from source)
2. Click "Settings"
3. Scroll to "Google Sheets Integration"
4. Fill in:
   - Enable automatic upload
   - Paste Spreadsheet ID
   - Sheet name: "Sessions" (or your choice, without any of `< > " ' \ / | ? *`; a name with them is replaced by "Sessions")
   - Browse to `credentials.json`
5. Click "Test Connection". The first time, a browser opens: sign in to Google and grant permissions. The app should then say "Connected"
6. Click "Save Google Sheets Settings"

## Step 5: First Session (30 sec)

1. Go back to main screen
2. Start a session
3. End the session
4. Click **Save & Complete** (**Skip** uploads too)
5. **Check your Google Sheet** → a header row, plus one row for each period of the session. The first upload also sends any sessions you recorded before turning uploads on

## Signing In

- Happens when you click Test Connection, never during an upload
- Sign in to Google
- Grant permissions
- Done! The sign-in is saved in `token.pickle` and reused for every upload
- If Google later needs you to sign in again, the app warns you: click Test Connection again

## Troubleshooting

### "Credentials file not found"

→ Make sure `credentials.json` is next to `TimeAligned.exe` (or in the project root folder when running from source)

### "Spreadsheet not found"

→ Double-check the Spreadsheet ID (no spaces, correct copy)

### Test Connection fails

→ Make sure you enabled Google Sheets API in Cloud Console

### Authentication window doesn't open

→ Check that Windows has a default web browser. While Test Connection waits for the sign-in, the app window doesn't respond; after 3 minutes it shows an error, and you can try again. When running from source, the sign-in URL is also printed in the terminal

## When Do Sessions Upload?

- When you click **Save & Complete** or **Skip**, together with any earlier session that hasn't uploaded yet or has changed
- Shortly after the app starts, so anything missed is retried
- Saving a session again replaces its rows instead of adding new ones
- A session uploads once it ends, not while you're still tracking it

## Tips

- Same spreadsheet for all sessions (keeps growing)
- Tab and headers auto-created on first upload
- Offline? Sessions wait. Once you're back online, they upload at your next Save or Skip, or the next time the app starts
- Can disable anytime in settings
- Analyze with Google Sheets charts/pivot tables

## Need More Help?

See the full guide: [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)

---

_Estimated total setup time: ~5 minutes_
