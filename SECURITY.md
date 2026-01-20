# Security Guide - Time Aligned

## Overview

This document outlines security considerations, vulnerable user inputs, and best practices for Time Aligned.

## Sensitive Data & Files

### DO NOT Commit These Files

These files contain sensitive credentials and should NEVER be committed to version control:

- `credentials.json` - Google OAuth client secrets
- `token.pickle` - Google OAuth access/refresh tokens
- `client_secret*.json` - Alternative Google credentials format
- `settings.json` - May contain spreadsheet IDs
- `data.json` - Contains user session data

✅ **Already in .gitignore** - Verify before committing!

### Local Data Security

If someone downloads and runs this app:

- They give the app access to their Google account (limited to Sheets API scope)
- All session timing data is stored locally in `data.json`
- Screenshots (if enabled) contain potentially sensitive screen content
- Settings may reveal user's work patterns and project names

## Environment Variables (Recommended)

Use environment variables for sensitive configuration instead of storing in files:

```bash
# Windows PowerShell
$env:GOOGLE_SHEETS_SPREADSHEET_ID = "your_spreadsheet_id_here"
$env:GOOGLE_SHEETS_CREDENTIALS_FILE = "C:\path\to\credentials.json"
$env:GOOGLE_SHEETS_TOKEN_FILE = "C:\path\to\token.pickle"

# Linux/Mac
export GOOGLE_SHEETS_SPREADSHEET_ID="your_spreadsheet_id_here"
export GOOGLE_SHEETS_CREDENTIALS_FILE="/path/to/credentials.json"
export GOOGLE_SHEETS_TOKEN_FILE="/path/to/token.pickle"
```

Environment variables take precedence over settings file values.

## OAuth Scope Limitations

The app uses Google OAuth with these scopes:

### Full Access (Default)

```python
uploader = GoogleSheetsUploader("settings.json", read_only=False)
# Scope: https://www.googleapis.com/auth/spreadsheets
```

Allows reading and writing to Google Sheets.

### Read-Only Access

```python
uploader = GoogleSheetsUploader("settings.json", read_only=True)
# Scope: https://www.googleapis.com/auth/spreadsheets.readonly
```

Only allows viewing Google Sheets (for testing/verification).

**Recommendation:** Use the minimum scope necessary. If you only need to upload data, use full access. If testing connection, use read-only.

## Vulnerable User Inputs

### 1. Spreadsheet ID

**Location:** Settings Frame → Google Sheets Integration

**Vulnerability:** Path traversal, injection attacks

```
DANGEROUS: ../../../etc/passwd
DANGEROUS: '; DROP TABLE sessions; --
DANGEROUS: <script>alert('xss')</script>
```

**Mitigation:**

- Input validation: Only allows alphanumeric, hyphens, underscores
- Google Sheets IDs are typically 44 characters
- Regex pattern: `^[a-zA-Z0-9_-]+$`

### 2. Sheet Name (Tab Name)

**Location:** Settings Frame → Google Sheets Integration

**Vulnerability:** XSS, path injection

```
DANGEROUS: <script>alert('xss')</script>
DANGEROUS: Sheet'; DROP TABLE--
DANGEROUS: ../../../secrets
```

**Mitigation:**

- Max length: 100 characters
- Blocked characters: `< > " ' \ / | ? *`
- Falls back to "Sessions" if invalid

### 3. Credentials File Path

**Location:** Settings Frame → Google Sheets Integration (Browse button)

**Vulnerability:** Path traversal

```
DANGEROUS: ../../../etc/passwd
DANGEROUS: C:\Windows\System32\config\sam
DANGEROUS: ~/sensitive/data.json
DANGEROUS: %APPDATA%/secrets.json
```

**Mitigation:**

- Blocks path traversal patterns: `..`, `~`, `/etc/`, `C:\Windows\`, `%`, `${`
- Only allows file extensions: `.json`, `.pickle`, `.pkl`
- Authentication fails for unsafe paths

### 4. Sphere Names

**Location:** Settings Frame → Sphere Management

**Vulnerability:** File path injection (spheres used in folder names)

```
DANGEROUS: ../../../
DANGEROUS: C:\sensitive\data
```

**Current Status:** ⚠️ **Needs sanitization**

**Recommendation:**

```python
def sanitize_sphere_name(name):
    # Remove path characters
    dangerous_chars = ['/', '\\', '..', '~', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        name = name.replace(char, '_')
    return name[:50]  # Limit length
```

### 5. Project Names

**Location:** Settings Frame → Project Management

**Vulnerability:** Similar to sphere names - used in data structures

```
DANGEROUS: <script>alert('xss')</script>
DANGEROUS: {"malicious": "json"}
```

**Current Status:** ⚠️ **Needs sanitization**

### 6. Break Action Names

**Location:** Settings Frame → Break Actions

**Vulnerability:** XSS if displayed in web interface

```
DANGEROUS: <img src=x onerror=alert('xss')>
```

**Current Status:** ⚠️ **Needs sanitization**

### 7. Session Notes/Comments

**Location:** Completion Frame → Project/Break comments

**Vulnerability:** XSS if displayed in Google Sheets or web

```
DANGEROUS: =cmd|'/c calc'!A1
DANGEROUS: <a href="javascript:alert('xss')">
```

**Current Status:** ⚠️ **Needs sanitization**

**Recommendation:**

- Escape special characters before uploading to Google Sheets
- Prefix formulas with single quote to prevent execution: `'=cmd|...`

### 8. Screenshot Folder Paths

**Location:** Automatically generated from session data

**Vulnerability:** Path traversal if session names are manipulated

```
DANGEROUS: session_../../sensitive/
```

**Current Status:** ⚠️ **Verify path construction**

## Input Validation Checklist

- [x] Spreadsheet ID validated
- [x] Sheet name sanitized
- [x] Credentials file path validated
- [x] Environment variables supported
- [x] OAuth scopes limited
- [ ] Sphere names sanitized
- [ ] Project names sanitized
- [ ] Break action names sanitized
- [ ] Session comments escaped
- [ ] Screenshot paths validated

## Best Practices

### For Users

1. **Never share** your `credentials.json` or `token.pickle` files
2. **Use environment variables** for sensitive config
3. **Review OAuth scopes** before authorizing
4. **Keep spreadsheet IDs private** - they're not passwords but still sensitive
5. **Be cautious** with screenshot feature - may capture sensitive information
6. **Regularly rotate** OAuth tokens if compromised

### For Developers

1. **Always validate** user input before file operations
2. **Use parameterized queries** for any database operations
3. **Escape output** before displaying in web/sheets
4. **Limit OAuth scopes** to minimum necessary
5. **Never log** credentials or tokens
6. **Use .gitignore** for all sensitive files
7. **Test input validation** with malicious payloads

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** open a public GitHub issue
2. Email the maintainer directly (see repository owner)
3. Include steps to reproduce
4. Allow time for a patch before public disclosure

## Security Audit Recommendations

### High Priority

1. ✅ Add input validation for Google Sheets settings
2. ✅ Support environment variables
3. ✅ Implement OAuth scope limitations
4. Add sanitization for sphere/project/action names
5. Escape session notes/comments before upload

### Medium Priority

6. Add CSRF protection if web interface is added
7. Implement rate limiting for API calls
8. Add logging of authentication attempts
9. Consider encrypting local `data.json`

### Low Priority

10. Add integrity checks for settings files
11. Implement session timeout for OAuth tokens
12. Add option to use service accounts instead of OAuth

## Secure Configuration Example

```json
{
  "google_sheets": {
    "enabled": true,
    "spreadsheet_id": "", // Use environment variable instead
    "sheet_name": "Sessions",
    "credentials_file": "" // Use environment variable instead
  }
}
```

```powershell
# Set in PowerShell profile for persistence
$env:GOOGLE_SHEETS_SPREADSHEET_ID = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
$env:GOOGLE_SHEETS_CREDENTIALS_FILE = "$HOME\Documents\secure\credentials.json"
```

## Additional Resources

- [Google Sheets API Security](https://developers.google.com/sheets/api/guides/authorizing)
- [OWASP Input Validation](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/rfc6819)
