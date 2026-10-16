# Google Sheets Integration Setup Guide

This guide will help you set up Google Sheets API integration to automatically upload your session data to a Google Spreadsheet.

## Prerequisites

- A Google account
- Access to Google Cloud Console

## Step 1: Install Required Dependencies

Skip this step if you use the downloaded `TimeAligned.exe`: the Google libraries are already included.

When running from source, install the Google API libraries:

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
   - Save the file as `credentials.json` next to `TimeAligned.exe` (or in the project folder when running from source)

## Step 5: Create a Google Spreadsheet

1. Go to [Google Sheets](https://sheets.google.com/)
2. Create a new spreadsheet or use an existing one
3. Copy the **Spreadsheet ID** from the URL:
   - URL format: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
   - Copy the `SPREADSHEET_ID` part, or copy the whole URL: the app extracts the ID when you paste it

## Step 6: Configure Time Tracker

1. Open the Time Tracker application
2. Go to **Settings**
3. Scroll down to the **Google Sheets Integration** section
4. Configure the following:
   - **Enable automatic upload to Google Sheets**: Check this box
   - **Spreadsheet ID**: Paste the spreadsheet ID you copied
   - **Sheet Name (Tab)**: Enter the name of the sheet tab (default: "Sessions"). If the tab doesn't exist yet, the app creates it at the first upload. Don't use any of `< > " ' \ / | ? *`: a name with them, or longer than 100 characters, is replaced by "Sessions"
   - **Credentials File**: Browse to select your `credentials.json` file
5. Click **Test Connection** to verify your setup. The first time, this opens the Google sign-in described in Step 7
6. Click **Save Google Sheets Settings**. Test Connection alone doesn't save your settings or turn uploads on

## Step 7: Sign In to Google

You sign in from **Test Connection**, never during an upload:

1. Click **Test Connection**. A browser window opens and asks you to sign in to your Google account
2. Grant the requested permissions (read/write access to Google Sheets)
3. The app saves your sign-in in `token.pickle`, next to `TimeAligned.exe`
4. Uploads reuse this saved sign-in

Finish the sign-in in the browser instead of closing the tab. Until you do, the app window doesn't respond; after 3 minutes it stops waiting and shows an error.

If the saved sign-in stops working, uploads still don't open the browser. Instead, the app warns you that Google Sheets needs you to sign in again; click **Test Connection** to sign in.

## When Sessions Upload

- When you click **Save & Complete** or **Skip** on the completion screen, the app uploads that session, along with any earlier session that hasn't been uploaded yet or has changed since its last upload
- The first upload therefore sends every session you recorded before turning uploads on, not just the newest one
- The app also checks shortly after it starts. A session that didn't upload (you were offline, needed to sign in again, or closed the app on the completion screen) is sent then
- A session is uploaded once it has ended, never while you're still tracking it
- Saving a session again (for example after editing it) replaces its rows instead of adding new ones. The app finds a session's rows by the Session ID in column A, so leave that column as it is
- After you switch to another spreadsheet or tab, the next upload sends every session to the new one
- Deleting a session in the app doesn't remove its rows from the sheet. Delete them by hand: search the sheet for the Session ID
- The app records what it has uploaded in `sheets_upload_log.json`. If you delete rows by hand, those sessions aren't sent again on their own. To send every session again, quit the app, delete `sheets_upload_log.json`, and start the app. Each session is sent once, replacing any rows it already has

## What Gets Uploaded

Each session uploads **one row per period**: every active period, break and idle period gets its own row. A 4-hour session with 3 active periods and 2 breaks produces 5 rows. A session with no periods uploads a single summary row.

The app writes the header row itself. The columns, in order:

| #   | Column                        | Contents                                                            |
| --- | ----------------------------- | ------------------------------------------------------------------- |
| 1   | Session ID                    | Identifies the session; the app uses it to find the session's rows  |
| 2   | Date                          | The session's date                                                  |
| 3   | Sphere                        | The session's sphere                                                |
| 4   | Session Start Time            | When the session started                                            |
| 5   | Session End Time              | When the session ended                                              |
| 6   | Session Total Duration (min)  | Same on every row of the session                                    |
| 7   | Session Active Duration (min) | Same on every row of the session                                    |
| 8   | Session Break Duration (min)  | Same on every row of the session                                    |
| 9   | Type                          | `active`, `break`, `idle`, or `session_summary`                     |
| 10  | Primary Action                | The project (active rows) or the break action (break and idle rows) |
| 11  | Primary Percentage            | The primary's share of the period: 100 unless the period is split   |
| 12  | Primary Duration (min)        | The primary's part of the period                                    |
| 13  | Primary Comment               | The comment on the primary project or action                        |
| 14  | Secondary Action              | The secondary project or action, if the period has one              |
| 15  | Secondary Percentage          | The secondary's share of the period                                 |
| 16  | Secondary Duration (min)      | The secondary's part of the period                                  |
| 17  | Secondary Comment             | The comment on the secondary project or action                      |
| 18  | Activity Start                | When the period started                                             |
| 19  | Activity End                  | When the period ended (blank on break rows)                         |
| 20  | Active Notes                  | Same on every row of the session                                    |
| 21  | Break Notes                   | Same on every row of the session                                    |
| 22  | Idle Notes                    | Same on every row of the session                                    |
| 23  | Session Notes                 | Same on every row of the session                                    |

Don't change row 1: before each upload the app checks the header row. If it has changed, the app shows a "Google Sheets Column Order Error" and uploads nothing until you restore it.

## Troubleshooting

### "Credentials file not found"

- Make sure `credentials.json` is next to `TimeAligned.exe` (or in the project folder when running from source)
- Check that the path in settings is correct

### "Authentication failed"

- Delete `token.pickle`, then click **Test Connection** to sign in again
- Make sure you've added yourself as a test user in the OAuth consent screen

### "Google Sheets needs you to sign in again"

- In **Settings**, go to **Google Sheets Integration** and click **Test Connection** to sign in
- Sessions saved in the meantime upload at your next Save or Skip, or the next time the app starts
- If this happens every week, your Google Cloud app's publishing status is probably **Testing**: Google ends sign-ins for apps in testing after 7 days. To stop this, open the OAuth consent screen (or Audience page) in Google Cloud Console and click **Publish app**; you'll then see an "unverified app" warning when you sign in. Otherwise, sign in again each week

### Offline

- Uploads wait until you're back online. You may see "Google Sheets upload is waiting for an internet connection", or no message at all
- Once you're back online, the sessions upload at your next Save or Skip, or the next time the app starts

### "Google Sheets upload failed"

- Your sessions are saved on this computer and are sent again at your next Save or Skip, or the next time the app starts
- If it keeps happening, click **Test Connection** to check your settings

### "Google Sheets Column Order Error"

- Row 1 of the tab no longer matches the columns listed above. Undo the change, or point the app at a new, empty tab

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
- Uploaded rows include your sphere, project and action names, comments and notes. Screenshots are never uploaded
