# Metrics Analysis

Analyze video performance metrics, identify trends, and compute insights from YouTube video data.

## Overview

This module processes video metadata exported by the video-fetching module, applying filters and computing analytics like top performers, optimal publish times, and popularity trends.

## Scripts

### `metrics_processing.py` - Local Python Analysis

Analyze video performance with configurable filters and insights.

**Features**:
- Flexible filtering by duration, views, title patterns
- Exclude shorts automatically
- Identify top performing videos
- Analyze best publish times and days
- Compute popularity trends over time
- Normalize metrics by duration

**Usage**:

```bash
# Process with default settings
python3 metrics_processing.py

# Custom input/config files via environment variables
VIDEO_LIST=my_videos.json VARS_FILE=my_config.json python3 metrics_processing.py
```

**Environment Variables**:
- `VIDEO_LIST` - Input video data file (default: `video_list.json`)
- `VARS_FILE` - Configuration file (default: `vars.example.json`)

**Output**:
Prints JSON to stdout with structure:
```json
{
  "stats": {
    "totalVideos": 150,
    "filteredVideos": 120,
    "excludedShorts": 30,
    "excludedByTitlePattern": 5,
    "avgViews": 15234.5,
    "avgViewsPerDay": 123.4
  },
  "topVideos": [
    {
      "videoId": "abc123",
      "title": "My Best Video",
      "views": 50000,
      "viewsPerDay": 500,
      "duration": "PT10M30S",
      "publishedAt": "2025-01-15T10:30:00Z"
    }
  ],
  "publishTimeInsights": {
    "bestDayOfWeek": "Tuesday",
    "bestHourOfDay": 14,
    "dayDistribution": {...},
    "hourDistribution": {...}
  },
  "popularityOverTime": [
    {"period": "2025-01-01", "avgViews": 12000, "videoCount": 10}
  ]
}
```

### `metrics_processing_n8n.js` - n8n Function Node

JavaScript implementation for use in n8n workflows.

**Features**:
- Identical logic to Python version
- Paste directly into n8n Function node
- Reads config from `items[0].json.vars` or inline `varsConfig`

**Usage in n8n**:

1. Add YouTube List Videos node (fetch videos)
2. Add Function node with this code
3. Pass configuration via previous node or edit `varsConfig` default

**Configuration via previous node**:
```javascript
// Previous node output:
{
  "videos": [...],
  "vars": {
    "exclude": {...},
    "filters": {...},
    "insights": {...}
  }
}
```

## Configuration

Uses `vars.example.json` (or custom file via `VARS_FILE`):

```json
{
  "exclude": {
    "videoIds": ["id1", "id2"],
    "titleContains": ["#shorts", "test"],
    "excludeShorts": true,
    "maxDurationSecondsForShorts": 60
  },
  "filters": {
    "minViews": 100,
    "minDurationSeconds": 60,
    "dateRange": {
      "start": "2024-01-01",
      "end": "2025-12-31"
    }
  },
  "insights": {
    "metric": "viewsPerDay",
    "topVideosLimit": 10,
    "normalizeByDuration": false,
    "popularityPeriod": "month"
  }
}
```

### Exclusion Rules (`exclude`)

- **`videoIds`**: Array of specific video IDs to exclude
- **`titleContains`**: Exclude videos with titles containing these strings (case-insensitive)
- **`excludeShorts`**: If `true`, exclude videos ≤ `maxDurationSecondsForShorts`
- **`maxDurationSecondsForShorts`**: Duration threshold for shorts (default: 60)

### Quality Filters (`filters`)

- **`minViews`**: Minimum view count to include
- **`minDurationSeconds`**: Minimum duration in seconds
- **`dateRange`**: Only include videos published within this range
  - `start`: ISO date string (e.g., "2024-01-01")
  - `end`: ISO date string

### Insights Configuration (`insights`)

- **`metric`**: Metric to analyze (`"views"`, `"viewsPerDay"`, `"likes"`, `"comments"`)
- **`topVideosLimit`**: Number of top performers to return (default: 10)
- **`normalizeByDuration`**: Divide metrics by duration for fair comparison
- **`popularityPeriod`**: Grouping period (`"day"`, `"week"`, `"month"`)

## Installation

```bash
pip install -r metrics-analysis/requirements.txt
```

## Input Requirements

Expects video data in format produced by `video-fetching/list_videos.py`:

```json
[
  {
    "videoId": "abc123",
    "title": "Video Title",
    "publishedAt": "2025-01-15T10:30:00Z",
    "duration": "PT10M30S",
    "viewCount": "1234",
    "likeCount": "56",
    "commentCount": "12"
  }
]
```

## Computed Metrics

### Views Per Day

```
viewsPerDay = totalViews / daysSincePublished
```

Accounts for recency - newer videos with high views/day may outperform older viral videos.

### Normalized Metrics

When `normalizeByDuration: true`:

```
normalizedMetric = metric / (durationSeconds / 60)
```

Useful for comparing shorts vs long-form content.

### Publish Time Analysis

- Groups videos by day of week and hour of day
- Computes average performance per time slot
- Identifies patterns in successful publish times

### Popularity Trends

Groups videos by `popularityPeriod` and computes:
- Average views per period
- Video count per period
- Trends over time

## Use Cases

### Find Best Publish Time

```bash
# Process last 90 days
cd video-fetching
python3 list_videos.py --days 90

cd ../metrics-analysis
python3 metrics_processing.py | jq '.publishTimeInsights'
```

Output:
```json
{
  "bestDayOfWeek": "Tuesday",
  "bestHourOfDay": 14,
  "dayDistribution": {
    "Monday": 12000,
    "Tuesday": 18000,
    "Wednesday": 15000
  }
}
```

### Identify Top Performers (Excluding Shorts)

```json
{
  "exclude": {
    "excludeShorts": true,
    "maxDurationSecondsForShorts": 60
  },
  "insights": {
    "metric": "viewsPerDay",
    "topVideosLimit": 20
  }
}
```

### Compare Content Categories

```bash
# Filter by title patterns
# Config 1: Gaming videos
{
  "filters": {"titleContains": ["gameplay"]}
}

# Config 2: Tutorial videos
{
  "filters": {"titleContains": ["how to", "tutorial"]}
}
```

### Analyze Growth Over Time

```json
{
  "insights": {
    "popularityPeriod": "month",
    "metric": "viewsPerDay"
  }
}
```

## Integration with n8n

### Basic Workflow

```
[YouTube List Videos Node]
    ↓
[Function Node: metrics_processing_n8n.js]
    ↓
[IF Node: Check if viewsPerDay > 500]
    ↓ Yes
[Slack/Email Alert: High performer detected]
```

### Advanced Workflow with Custom Config

```
[YouTube List Videos Node]
    ↓
[Set Node: Add vars config]
    {
      "videos": "{{ $json.items }}",
      "vars": {
        "exclude": {"excludeShorts": true},
        "insights": {"topVideosLimit": 5}
      }
    }
    ↓
[Function Node: metrics_processing_n8n.js]
    ↓
[Google Sheets: Log top performers]
```

### Editing n8n Script

Open `metrics_processing_n8n.js` and modify the `varsConfig` default:

```javascript
// Default configuration (modify as needed)
const varsConfig = {
  exclude: {
    excludeShorts: true,
    maxDurationSecondsForShorts: 60
  },
  insights: {
    metric: "viewsPerDay",
    topVideosLimit: 10
  }
};
```

## Output Examples

### Top Videos Output

```json
{
  "topVideos": [
    {
      "videoId": "abc123",
      "title": "Viral Video Title",
      "views": 100000,
      "viewsPerDay": 5000,
      "likes": 8000,
      "comments": 500,
      "duration": "PT8M15S",
      "publishedAt": "2025-01-20T14:30:00Z",
      "url": "https://youtube.com/watch?v=abc123"
    }
  ]
}
```

### Publish Time Insights

```json
{
  "publishTimeInsights": {
    "bestDayOfWeek": "Tuesday",
    "bestHourOfDay": 14,
    "dayDistribution": {
      "Monday": 12453,
      "Tuesday": 18932,
      "Wednesday": 14221
    },
    "hourDistribution": {
      "10": 8500,
      "14": 22000,
      "18": 15000
    }
  }
}
```

## Notes

- **Shorts detection**: Videos with `duration ≤ 60s` classified as shorts
- **Date handling**: All dates UTC, parsed from ISO 8601 strings
- **Missing data**: Videos without statistics are excluded from analysis
- **Division by zero**: Protected when computing averages and rates

## Troubleshooting

### No videos after filtering

```
{
  "stats": {"filteredVideos": 0}
}
```

**Solutions**:
- Reduce `minViews` threshold
- Remove date range restrictions
- Check `titleContains` exclusions aren't too broad

### Unexpected top videos

**Check**:
- `metric` setting (views vs viewsPerDay behave differently)
- `normalizeByDuration` - may skew results for very short videos
- Date range - ensure you're analyzing intended period

### n8n script errors

**Common issues**:
- Ensure input node outputs `items` array
- Check `items[0].json.vars` path if using external config
- Verify video objects have required fields (viewCount, duration, publishedAt)

## See Also

- [video-fetching/README.md](../video-fetching/README.md) - Generate input data
- [examples/vars.example.json](./examples/vars.example.json) - Full config example
- [CLAUDE.md](../CLAUDE.md) - Metrics processing architecture details
