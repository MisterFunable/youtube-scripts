# Setup Guide

Complete guide to setting up OAuth authentication for YouTube Data API v3.

## Prerequisites

- Google account with a YouTube channel
- Python 3.7 or higher
- Basic command-line knowledge

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" dropdown → "New Project"
3. Enter project name (e.g., "YouTube Automations")
4. Click "Create"
5. Wait for project creation, then select it

## Step 2: Enable YouTube Data API v3

1. In Google Cloud Console, navigate to "APIs & Services" → "Library"
2. Search for "YouTube Data API v3"
3. Click on the API from results
4. Click "Enable"
5. Wait for activation (usually instant)

## Step 3: Configure OAuth Consent Screen

1. Navigate to "APIs & Services" → "OAuth consent screen"
2. Select **"External"** user type (unless using Google Workspace)
3. Click "Create"

### Fill in Required Fields

**App information**:
- **App name**: YouTube Automations (or your preferred name)
- **User support email**: Your email address
- **App logo**: Optional

**App domain**:
- Leave blank for personal use
- **Developer contact information**: Your email address

4. Click "Save and Continue"

### Scopes

5. Click "Add or Remove Scopes"
6. Filter for "YouTube Data API v3"
7. Select the following scopes:

**For read-only access**:
- `.../auth/youtube.readonly` - View YouTube account info

**For read/write access** (required for updates):
- `.../auth/youtube.force-ssl` - Manage YouTube account

8. Click "Update" → "Save and Continue"

### Test Users

9. Click "Add Users"
10. Add your Google account email
11. Click "Add" → "Save and Continue"

### Summary

12. Review information
13. Click "Back to Dashboard"

## Step 4: Create OAuth Credentials

1. Navigate to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. **Application type**: Desktop app
4. **Name**: YouTube Automation Client (or your preferred name)
5. Click "Create"

### Download Credentials

6. In the popup, click "Download JSON"
7. Save file to your computer
8. Rename the file to **`client_secret.json`**
9. Move to your project's root directory

## Step 5: Verify File Structure

Your project root should now have:

```
youtube-automations/
├── client_secret.json          # OAuth credentials (DO NOT COMMIT)
├── shared/
│   ├── youtube_auth.py
│   ├── youtube_service.py
│   └── config.py
└── ...
```

**IMPORTANT**: Ensure `client_secret.json` is in the root directory, NOT inside subdirectories.

## Step 6: First Authentication

### Run Any Script

```bash
# Example: Test video fetching
cd video-fetching
python3 list_videos.py --test
```

### OAuth Flow

1. Script will open your default browser
2. You may see "Google hasn't verified this app" warning
   - Click "Advanced"
   - Click "Go to [App Name] (unsafe)" - this is YOUR app, it's safe
3. Select your Google account
4. Review permissions
5. Click "Allow"
6. Browser will show "The authentication flow has completed"
7. Return to terminal

### Token Created

After successful authentication:
- `token.pickle` is created in the root directory
- Future runs will use this cached token
- Token auto-refreshes when expired

## Verification

```bash
# Test connection
cd video-fetching
python3 list_videos.py --test

# Expected output:
# Successfully connected to YouTube API
# Channel ID: UC...
```

## Troubleshooting

### "client_secret.json not found"

**Cause**: File is missing or in wrong location

**Solution**:
1. Verify file is named exactly `client_secret.json` (not `client_secret(1).json` or similar)
2. Ensure it's in the project root directory
3. Check file isn't empty (should contain JSON with `client_id`, `client_secret`)

### "Access blocked: This app's request is invalid"

**Cause**: OAuth consent screen not configured properly

**Solution**:
1. Go back to OAuth consent screen
2. Ensure your email is added as a test user
3. Verify required scopes are selected
4. Try re-downloading credentials

### "The user has not granted the app <scope>"

**Cause**: Missing required scope in OAuth consent screen

**Solution**:
1. Go to "APIs & Services" → "OAuth consent screen"
2. Click "Edit App"
3. In "Scopes" step, add missing scope:
   - Read-only: `youtube.readonly`
   - Read/write: `youtube.force-ssl`
4. Delete `token.pickle` and re-authenticate

### "invalid_grant" Error

**Cause**: Token expired or scope changed

**Solution**:
```bash
# Delete cached token
rm token.pickle

# Re-authenticate
python3 video-fetching/list_videos.py --test
```

### "Redirect URI mismatch"

**Cause**: Wrong application type selected

**Solution**:
1. Delete OAuth client in Google Cloud Console
2. Create new one with "Desktop app" type (NOT "Web application")
3. Re-download credentials

### Browser Doesn't Open

**Cause**: Running on headless server or SSH session

**Solution**: Use manual OAuth flow
```python
# In youtube_auth.py, modify get_authenticated_service():
flow = InstalledAppFlow.from_client_secrets_file(
    CLIENT_SECRET_FILE,
    SCOPES,
    redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # Add this
)

# Follow manual URL authorization flow
```

## Security Best Practices

### Protect Credentials

**Never commit to git**:
- `client_secret.json`
- `token.pickle`
- `.env`

**Verify `.gitignore`**:
```bash
# Check these are ignored
git status --ignored

# Should NOT show:
# client_secret.json
# token.pickle
# .env
```

### Rotate Compromised Credentials

If credentials are exposed:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to "APIs & Services" → "Credentials"
3. Find your OAuth 2.0 Client ID
4. Click trash icon to delete
5. Create new OAuth client (follow Step 4 above)
6. Download new `client_secret.json`
7. Delete old `token.pickle`
8. Re-authenticate

### Revoke Access

To revoke app access to your YouTube account:

1. Go to [Google Account Permissions](https://myaccount.google.com/permissions)
2. Find your app name
3. Click "Remove Access"

## Quota Management

### Daily Quota

- Default: **10,000 units/day**
- Resets: Daily at **midnight Pacific Time (PT)**

### Request Costs

| Operation | Cost (units) |
|-----------|--------------|
| List videos | 1 per page (50 videos) |
| Get video details | 1 per batch (50 videos) |
| Update video | 50 per video |
| Delete video | 50 per video |

### Check Quota Usage

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to "APIs & Services" → "Dashboard"
3. Click "YouTube Data API v3"
4. View quota usage graphs

### Increase Quota

To request higher quota limits:

1. Navigate to "IAM & Admin" → "Quotas"
2. Filter for "YouTube Data API v3"
3. Select quota to increase
4. Click "Edit Quotas"
5. Fill out request form (requires business justification)

**Note**: Quota increases are reviewed by Google and may take several days.

## Multiple Channels

To manage multiple YouTube channels:

### Option 1: Separate Tokens

```bash
# Authenticate for Channel A
python3 list_videos.py --test
mv token.pickle token_channelA.pickle

# Authenticate for Channel B
python3 list_videos.py --test
mv token.pickle token_channelB.pickle

# Use specific token
cp token_channelA.pickle token.pickle
python3 list_videos.py
```

### Option 2: Separate Projects

Create separate Google Cloud projects for each channel, each with its own `client_secret.json`.

## Production Deployment

### Publishing Your App

If moving beyond testing (>100 users):

1. Navigate to "OAuth consent screen"
2. Click "Publish App"
3. Submit for Google verification
4. Wait for approval (can take weeks)

**Not required for personal use** with test users.

## Environment Setup Checklist

- [ ] Google Cloud project created
- [ ] YouTube Data API v3 enabled
- [ ] OAuth consent screen configured
- [ ] Required scopes added
- [ ] Email added as test user
- [ ] OAuth credentials created and downloaded
- [ ] `client_secret.json` in project root
- [ ] `.gitignore` configured
- [ ] First authentication successful
- [ ] `token.pickle` created
- [ ] Test script runs successfully

## Next Steps

- [Security Guide](./SECURITY.md) - Protect your credentials
- [Shared Utilities](../shared/README.md) - Understand authentication flow
- [Video Fetching](../video-fetching/README.md) - Start using the API

## Additional Resources

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)
- [API Quotas](https://developers.google.com/youtube/v3/getting-started#quota)
- [Python Quickstart](https://developers.google.com/youtube/v3/quickstart/python)
