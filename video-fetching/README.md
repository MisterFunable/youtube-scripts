# Video Fetching

Fetch and export YouTube video metadata to JSON for analysis and processing.

## Overview

This module provides tools to retrieve video information from your YouTube channel, including metadata, statistics, and content details. Output is saved as JSON for use by other modules or external tools.

## Scripts

### `list_videos.py` - Main Video Lister

Fetch videos from your channel with flexible date filtering.

**Features**:
- Fetches all video metadata (title, description, statistics, duration, etc.)
- Configurable date range filtering
- Pagination handling for large channels
- JSON output with optional pretty printing
- Automatic backup creation on overwrites

**Usage**:

```bash
# Fetch videos from last 7 days (default)
python3 list_videos.py

# Fetch all videos from channel
python3 list_videos.py --all

# Fetch videos from last 30 days
python3 list_videos.py --days 30

# Custom output file
python3 list_videos.py --output my_videos.json

# Test API connection
python3 list_videos.py --test
```

**Command-line Arguments**:
- `--all` - Fetch all videos (ignores --days)
- `--days N` - Fetch videos from last N days (default: 7, max: 365)
- `--output FILE` - Output file path (default: `video_list.json`)
- `--test` - Test API connection and exit

**Output Format**:

```json
[
  {
    "videoId": "abc123",
    "title": "My Video Title",
    "description": "Video description...",
    "publishedAt": "2025-01-15T10:30:00Z",
    "duration": "PT10M30S",
    "viewCount": "1234",
    "likeCount": "56",
    "commentCount": "12",
    "tags": ["tag1", "tag2"],
    "thumbnails": {...},
    "categoryId": "22",
    "defaultLanguage": "en"
  },
  ...
]
```

### `backup_videos.py` - Backup Utility

Create timestamped backups of video metadata.

**Usage**:

```bash
# Backup current video_list.json
python3 backup_videos.py

# Backup specific file
python3 backup_videos.py --input my_videos.json --output backups/
```

**Features**:
- Automatic timestamped filenames
- Preserves original JSON formatting
- Creates backup directory if needed

## Installation

```bash
# From repository root
pip install -r video-fetching/requirements.txt

# Or install root dependencies (includes these)
pip install -r requirements.txt
```

## Configuration

Default settings are defined in `shared/config.py`:

```python
DEFAULT_OUTPUT_FILE = "video_list.json"
DEFAULT_DAYS_BACK = 7
MAX_DAYS_BACK = 365
MAX_RESULTS_PER_REQUEST = 50
```

Override via command-line arguments.

## Authentication

Requires YouTube Data API v3 credentials. See [docs/SETUP.md](../docs/SETUP.md) for OAuth setup.

**Required files** (not in repo, see `.gitignore`):
- `client_secret.json` - OAuth credentials
- `token.pickle` - Auto-generated authentication token

## Output Files

**Included in repository**:
- `examples/vars.example.json` - Example configuration for metrics processing

**Generated (gitignored)**:
- `video_list.json` - Default output file
- `backups/video_list_backup_*.json` - Timestamped backups

## Data Flow

```
┌──────────────────────────────────────┐
│ Authenticate via shared/youtube_auth │
└────────────┬─────────────────────────┘
             │
   ┌─────────▼──────────┐
   │ Get uploads        │
   │ playlist ID        │
   └─────────┬──────────┘
             │
   ┌─────────▼──────────┐
   │ Paginate through   │
   │ playlist (50/page) │
   └─────────┬──────────┘
             │
   ┌─────────▼──────────┐
   │ Batch fetch video  │
   │ details (50/batch) │
   └─────────┬──────────┘
             │
   ┌─────────▼──────────┐
   │ Filter by date     │
   │ (if --days used)   │
   └─────────┬──────────┘
             │
   ┌─────────▼──────────┐
   │ Save to JSON       │
   └────────────────────┘
```

## API Quota Usage

YouTube Data API quota: **10,000 units/day**

**Per execution**:
- List playlist items: ~1 unit per page (50 videos)
- Video details: ~1 unit per batch (50 videos)

**Examples**:
- 100 videos: ~4 units
- 500 videos: ~20 units
- 1000 videos: ~40 units

Safe to run multiple times per day for most channels.

## Use Cases

### Daily Video Monitoring

```bash
# Add to cron for daily exports
0 9 * * * cd /path/to/repo && python3 video-fetching/list_videos.py --days 1
```

### Full Channel Archive

```bash
# Export entire channel history
python3 list_videos.py --all --output archive_$(date +%Y%m%d).json
```

### Feed to Metrics Analysis

```bash
# Export last 30 days for analysis
python3 list_videos.py --days 30 --output video_list.json

# Then process with metrics module
cd ../metrics-analysis
python3 metrics_processing.py
```

### Feed to Translation Pipeline

```bash
# Export recent videos for translation
python3 list_videos.py --days 7

# Extract video IDs for queue
jq '[.[] | {videoId, title, description}]' video_list.json > video_queue.json
```

## Error Handling

**Common errors**:

1. **Invalid credentials**
   ```
   Error: client_secret.json not found
   ```
   Solution: Download OAuth credentials (see [docs/SETUP.md](../docs/SETUP.md))

2. **Quota exceeded**
   ```
   HttpError 403: quotaExceeded
   ```
   Solution: Wait until quota resets (daily at midnight PT) or reduce fetch range

3. **No videos found**
   ```
   No videos found in the specified range
   ```
   Solution: Check --days value or try --all flag

## Examples Directory

- `vars.example.json` - Sample configuration for metrics processing module

## Integration with Other Modules

### Metrics Analysis

```bash
python3 video-fetching/list_videos.py --days 30
cd metrics-analysis
python3 metrics_processing.py  # Reads video_list.json
```

### Shorts Management

```bash
python3 video-fetching/list_videos.py --all
# Shorts module has its own finder, but can use this data too
```

### Translation Automation

```bash
python3 video-fetching/list_videos.py --days 7
# Extract to queue format for translation pipeline
```

## Testing

```bash
# Test API connection without fetching videos
python3 list_videos.py --test

# Expected output:
# "Successfully connected to YouTube API"
# "Channel ID: UC..."
```

## Notes

- All timestamps are in UTC (ISO 8601 format with 'Z' suffix)
- Duration uses ISO 8601 format (e.g., "PT10M30S" = 10 minutes 30 seconds)
- Statistics are strings (not integers) as returned by API
- Video IDs are unique and stable identifiers
- Deleted/private videos won't appear in results

## See Also

- [shared/README.md](../shared/README.md) - Authentication and service utilities
- [metrics-analysis/README.md](../metrics-analysis/README.md) - Process exported data
- [docs/SETUP.md](../docs/SETUP.md) - Initial setup guide
