# Google Sheets Detailed Format Update

## Summary

Updated Google Sheets integration to match the CSV export format, providing detailed tracking data with separate rows for each active period, break, and idle period.

## Changes Made

### 1. Updated Headers

**Old Headers:**

- Session ID, Date, Start Time, End Time, Sphere, Project, Total Duration (min), Active Duration (min), Break Duration (min), Total Actions, Break Actions, Notes

**New Headers:**

- Session ID
- Date
- Sphere
- Session Start Time
- Session End Time
- Session Total Duration (min)
- Session Active Duration (min)
- Session Break Duration (min)
- Type
- Project
- Secondary Project
- Secondary Comment
- Secondary Percentage
- Activity Start
- Activity End
- Activity Duration (min)
- Activity Comment
- Break Action
- Secondary Action
- Active Notes
- Break Notes
- Idle Notes
- Session Notes

### 2. Data Format Changes

#### Before

- One row per session with aggregated data
- Limited project/action information
- Basic notes field

#### After

- Multiple rows per session:
  - One row for each active period
  - One row for each break
  - One row for each idle period
- Detailed project information including secondary projects
- Detailed action information including secondary actions
- Comprehensive notes (active, break, idle, session)

### 3. Upload Method (`upload_session`)

The method now:

1. Processes each active period separately with:
   - Primary and secondary project information
   - Activity start/end times
   - Activity duration
   - Activity comments

2. Processes each break separately with:
   - Primary and secondary action information
   - Break start time
   - Break duration
   - Break comments

3. Processes each idle period separately with:
   - Idle start/end times
   - Idle duration

4. Includes session-level comments in all rows:
   - Active notes
   - Break notes
   - Idle notes
   - Session notes

5. Creates a summary row if no activities exist

### 4. Security Features Maintained

- Formula injection prevention (escaping =, +, -, @, |)
- HTML/XML character escaping
- All text fields properly sanitized

## Testing

Added comprehensive tests:

1. `TestGoogleSheetsDetailedFormat.test_upload_detailed_format_with_active_periods`
   - Verifies multiple rows created for active periods and breaks
   - Validates correct data in each column
   - Confirms session comments included in all rows

2. `TestGoogleSheetsDetailedFormat.test_upload_with_secondary_projects`
   - Tests secondary project handling
   - Validates secondary project, comment, and percentage fields

3. Updated existing test `test_upload_session_formats_data_correctly`
   - Modified to expect new detailed format
   - Validates active period structure

All tests passing: 41 tests OK (2 skipped integration tests)

## Benefits

1. **Consistency**: Matches CSV export format exactly
2. **Detail**: Each activity/break/idle period tracked separately
3. **Analysis**: Better data for spreadsheet analysis and reporting
4. **Flexibility**: Secondary projects and actions fully supported
5. **Documentation**: Comprehensive notes at multiple levels

## Migration Notes

- Existing spreadsheets will need new headers on next upload
- Old data format will remain in existing rows
- New uploads will use the detailed format
- No breaking changes to API or configuration

## Files Modified

1. `src/google_sheets_integration.py`
   - Updated `_ensure_sheet_headers()` method with new header structure
   - Completely rewrote `upload_session()` method for detailed format

2. `tests/test_google_sheets.py`
   - Added `TestGoogleSheetsDetailedFormat` test class
   - Updated `test_upload_session_formats_data_correctly`
   - Added 2 new comprehensive tests

## Example Output

For a session with 2 active periods and 1 break:

| Session ID  | Date       | Sphere | Type   | Project   | Activity Start | Activity End | Activity Duration | Activity Comment     | Break Action |
| ----------- | ---------- | ------ | ------ | --------- | -------------- | ------------ | ----------------- | -------------------- | ------------ |
| session_123 | 2024-01-20 | Work   | active | Project A | 10:00:00       | 10:25:00     | 25.0              | Working on feature X |              |
| session_123 | 2024-01-20 | Work   | active | Project B | 10:35:00       | 11:00:00     | 25.0              | Code review          |              |
| session_123 | 2024-01-20 | Work   | break  |           | 10:25:00       |              | 10.0              | Quick coffee break   | Coffee       |

All session-level information (sphere, start/end time, total durations) is repeated in each row for easy filtering and analysis.
