# Google Sheets Integration Setup Guide

This guide will help you set up Google Sheets API integration to automatically upload your session data to a Google Spreadsheet.

## Prerequisites

- A Google account
- Access to Google Cloud Console

## Step 1: Install Required Dependencies

Run the following command to install the Google API libraries:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## Step 2: Set Up Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Give it a name like "Time Tracker"

## Step 3: Enable Google Sheets API

1. In the Google Cloud Console, navigate to **APIs & Services > Library**
2. Search for "Google Sheets API"
3. Click on it and press **Enable**

## Step 4: Create OAuth 2.0 Credentials

1. Go to **APIs & Services > Credentials**
2. Click **+ CREATE CREDENTIALS**
3. Select **OAuth client ID**
4. If prompted, configure the OAuth consent screen:
   - User Type: **External** (or Internal if using Google Workspace)
   - Fill in the required fields (App name, User support email, Developer contact)
   - Add your email to **Test users** if using External
   - Save and Continue
5. Back to creating OAuth client ID:
   - Application type: **Desktop app**
   - Name: "Time Tracker Desktop"
   - Click **CREATE**
6. Download the credentials:
   - Click the **Download** button (download icon) next to your newly created OAuth client
   - Save the file as `credentials.json` in your Time Tracker project folder

## Step 5: Create a Google Spreadsheet

1. Go to [Google Sheets](https://sheets.google.com/)
2. Create a new spreadsheet or use an existing one
3. Copy the **Spreadsheet ID** from the URL:
   - URL format: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
   - Copy the `SPREADSHEET_ID` part

## Step 6: Configure Time Tracker

1. Open the Time Tracker application
2. Go to **Settings**
3. Scroll down to the **Google Sheets Integration** section
4. Configure the following:
   - **Enable automatic upload to Google Sheets**: Check this box
   - **Spreadsheet ID**: Paste the spreadsheet ID you copied
   - **Sheet Name (Tab)**: Enter the name of the sheet tab (default: "Sessions")
   - **Credentials File**: Browse to select your `credentials.json` file
5. Click **Test Connection** to verify your setup
6. Click **Save Google Sheets Settings**

## Step 7: First-Time Authentication

The first time a session is uploaded:

1. A browser window will open asking you to sign in to your Google account
2. Grant the requested permissions (read/write access to Google Sheets)
3. The app will save your authentication token in `token.pickle`
4. Future uploads will use this saved token automatically

## What Gets Uploaded

Each session uploads **one row per period** (active, break, or idle). All periods share the same session-level fields.

**Session-level fields** (same on every row for the session):

- Session ID
- Date
- Sphere
- Start Time / End Time
- Total Duration, Active Duration, Break Duration (minutes)
- Active Notes, Break Notes, Idle Notes, Session Notes

**Period-level fields** (unique per row):

- Period Type (`active`, `break`, or `idle`)
- Period Start / End time
- Period Duration (minutes)
- Primary Project (active periods) or Primary Action (break/idle periods)
- Primary Comment
- Secondary Project or Action (if tagged)
- Secondary Comment
- Secondary Percentage

## Data Format

The spreadsheet columns are:

| Session ID | Date | Sphere | Start Time | End Time | Total Duration (min) | Active Duration (min) | Break Duration (min) | Type | Primary Project/Action | Primary Comment | Secondary Project/Action | Secondary Comment | Secondary % | Period Start | Period End | Period Duration (min) | Break Action | Secondary Action | Active Notes | Break Notes | Idle Notes | Session Notes |

Each row represents one period. A 4-hour session with 3 active periods and 2 breaks will produce 5 rows.

### "Credentials file not found"

- Make sure `credentials.json` is in the project folder
- Check that the path in settings is correct

### "Authentication failed"

- Delete `token.pickle` and try again
- Make sure you've added yourself as a test user in the OAuth consent screen

### "Spreadsheet not found"

- Verify the Spreadsheet ID is correct
- Make sure the Google account you authenticated with has access to the spreadsheet

### "Permission denied"

- The authenticated account doesn't have edit access to the spreadsheet
- Share the spreadsheet with your Google account with Editor permissions

## Privacy & Security

- Your `credentials.json` and `token.pickle` files contain sensitive authentication data
- Keep these files secure and don't share them
- Add them to `.gitignore` if using version control
- The Time Tracker only uploads session metadata, not screenshots or detailed activity
