# Shared Utilities

Common utilities for YouTube API authentication and service operations, used across all modules in this repository.

## Modules

### `youtube_auth.py` - Authentication Manager

Handles OAuth2 authentication flow with token caching and automatic refresh.

**Key Class**: `YouTubeAuth`

**Methods**:
- `get_authenticated_service()` - Returns authenticated YouTube API service object
- Automatically handles token refresh when expired
- Creates new token if none exists or credentials invalid

**Usage**:
```python
from shared.youtube_auth import YouTubeAuth

auth = YouTubeAuth()
youtube = auth.get_authenticated_service()
```

### `youtube_service.py` - YouTube API Wrapper

Core service class providing common YouTube API operations.

**Key Class**: `YouTubeService`

**Methods**:
- `get_upload_playlist_id()` - Get the uploads playlist ID for a channel
- `get_video_ids(playlist_id, max_results)` - Fetch video IDs from playlist
- `get_video_details(video_ids)` - Get detailed metadata for videos (batched by 50)
- `filter_videos_by_date(videos, days_back)` - Filter by publication date

**Usage**:
```python
from shared.youtube_service import YouTubeService

service = YouTubeService()
playlist_id = service.get_upload_playlist_id()
video_ids = service.get_video_ids(playlist_id)
videos = service.get_video_details(video_ids)
```

### `youtube_utils.py` - Utility Functions

Helper functions for video data processing.

**Functions**:
- `format_duration(duration)` - Convert ISO 8601 duration to readable format
- `parse_duration_to_seconds(duration)` - Convert ISO 8601 to total seconds
- Date/time utilities for timezone-aware processing

**Usage**:
```python
from shared.youtube_utils import parse_duration_to_seconds

duration_seconds = parse_duration_to_seconds("PT1M30S")  # Returns 90
```

### `config.py` - Configuration Constants

Centralized configuration for file paths and API settings.

**Constants**:
- `CLIENT_SECRET_FILE` - OAuth credentials file path
- `TOKEN_FILE` - Cached authentication token path
- `DEFAULT_OUTPUT_FILE` - Default video list output location
- `DEFAULT_DAYS_BACK` - Default lookback period (7 days)
- `MAX_DAYS_BACK` - Maximum allowed lookback (365 days)
- `MAX_RESULTS_PER_REQUEST` - YouTube API page size (50)

**Usage**:
```python
from shared.config import CLIENT_SECRET_FILE, DEFAULT_DAYS_BACK

# Use constants throughout your scripts
```

## Authentication Flow

```
┌─────────────────────────────────────────────────────┐
│ 1. Check for existing token.pickle                  │
└──────────────────┬──────────────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │ Token exists?     │
         └─────┬─────────┬───┘
               │ Yes     │ No
               │         │
     ┌─────────▼───┐   ┌─▼────────────────────────┐
     │ Token valid?│   │ Start OAuth flow         │
     └──┬──────┬───┘   │ - Open browser           │
        │ Yes  │ No    │ - User authorizes        │
        │      │       │ - Save token.pickle      │
        │   ┌──▼───────▼─────────────────────────┐│
        │   │ Refresh token with client_secret.json│
        │   └──────────────┬────────────────────────┘
        │                  │
     ┌──▼──────────────────▼───┐
     │ Return authenticated    │
     │ YouTube service object  │
     └─────────────────────────┘
```

## Required Files

These files are **NOT** included in the repository (see `.gitignore`):

1. **`client_secret.json`** - OAuth 2.0 credentials from Google Cloud Console
   - Get from: https://console.cloud.google.com/apis/credentials
   - Download as JSON, rename to `client_secret.json`
   - Place in repository root

2. **`token.pickle`** - Auto-generated on first authentication
   - Created automatically during OAuth flow
   - Cached to avoid repeated browser authentication
   - Auto-refreshed when expired

## OAuth Scopes

Different operations require different permission scopes:

- **Read-only**: `https://www.googleapis.com/auth/youtube.readonly`
  - List videos, fetch metadata, view statistics

- **Read/Write**: `https://www.googleapis.com/auth/youtube.force-ssl`
  - Update video metadata, change visibility, modify descriptions

To change scopes, delete `token.pickle` and re-authenticate.

## Error Handling

All service classes handle common API errors:

- **Quota exceeded**: Raises clear error message
- **Invalid credentials**: Triggers re-authentication flow
- **Network errors**: Retries with exponential backoff
- **Invalid video IDs**: Filters out and continues processing

## Dependencies

```
google-api-python-client>=2.131.0
google-auth>=2.34.0
google-auth-oauthlib>=1.2.1
isodate>=0.6.1
```

Install via root `requirements.txt` or module-specific requirements.

## Integration Examples

### Minimal Video Lister

```python
from shared.youtube_auth import YouTubeAuth
from shared.youtube_service import YouTubeService

# Authenticate
auth = YouTubeAuth()
service = YouTubeService(auth.get_authenticated_service())

# Fetch videos from last 7 days
playlist_id = service.get_upload_playlist_id()
video_ids = service.get_video_ids(playlist_id)
videos = service.get_video_details(video_ids)
recent = service.filter_videos_by_date(videos, days_back=7)

print(f"Found {len(recent)} videos from last week")
```

### Custom Date Range

```python
from datetime import datetime, timedelta, timezone
from shared.youtube_service import YouTubeService

service = YouTubeService()
all_videos = service.get_video_details(service.get_video_ids(...))

# Filter manually for custom logic
cutoff = datetime.now(timezone.utc) - timedelta(days=30)
monthly_videos = [
    v for v in all_videos
    if datetime.fromisoformat(v['publishedAt'].replace('Z', '+00:00')) > cutoff
]
```

## Notes

- All datetime operations use timezone-aware UTC
- Video IDs are batched in groups of 50 for API efficiency
- Service methods return raw API responses (dict format)
- Token refresh happens automatically - no manual intervention needed

## See Also

- [docs/SETUP.md](../docs/SETUP.md) - Detailed OAuth setup guide
- [docs/SECURITY.md](../docs/SECURITY.md) - Security best practices
