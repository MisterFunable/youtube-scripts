# Translation Automation

Automated video translation and metadata management using OpenAI GPT models and YouTube Data API.

## Overview

This module provides tools for translating video metadata (titles, descriptions) and bulk updating video settings like visibility and language preferences.

## Scripts

### `process_translation.py` - Queue-Based Translation System

Process videos from a queue, translate metadata using OpenAI, and update YouTube.

**Features**:
- Queue-based processing (resume on failures)
- GPT-powered translation (titles and descriptions)
- Multi-language support
- Automatic progress tracking
- API quota-aware error handling

**Usage**:

```bash
# Process videos from queue
python3 process_translation.py

# Resume from specific position (skip first 10 videos)
python3 process_translation.py --skip 10
```

**Required Files**:
- `video_queue.json` - List of videos to process
- `.env` - OpenAI API key (see examples/.env.example)

**Input Format** (`video_queue.json`):
```json
[
  {
    "videoId": "abc123",
    "title": "Original Title",
    "description": "Original description...",
    "defaultLanguage": "en"
  }
]
```

**Workflow**:
1. Read next video from `video_queue.json`
2. Translate title and description using OpenAI
3. Update video metadata via YouTube API
4. Move to `processed.json`
5. Remove from queue
6. Repeat

**State Files**:
- `video_queue.json` - Unprocessed videos (updated on each success)
- `processed.json` - Completed videos (append-only log)

### `ensure_settings.py` - Batch Settings Updater

Ensure all videos have specific metadata settings (language, visibility, audience).

**Features**:
- Batch update video metadata
- Configurable visibility (public/private/unlisted)
- Set default language and audience settings
- Dry-run mode for testing

**Usage**:

```bash
# Update all videos in input file
python3 ensure_settings.py --input videos.json

# Dry run (preview changes without applying)
python3 ensure_settings.py --input videos.json --dry-run

# Set specific language
python3 ensure_settings.py --input videos.json --language es
```

**Command-line Arguments**:
- `--input FILE` - Input video list (required)
- `--dry-run` - Preview changes without updating
- `--language CODE` - Default language code (e.g., "en", "es")
- `--visibility STATUS` - public/private/unlisted

### `set_public.py` - Bulk Visibility Updater

Quickly set videos to public visibility.

**Features**:
- Batch visibility updates
- Simple interface for common operation
- Progress tracking

**Usage**:

```bash
# Set all videos in list to public
python3 set_public.py --input videos.json

# Dry run
python3 set_public.py --input videos.json --dry-run
```

## Installation

```bash
pip install -r translation-automation/requirements.txt
```

## Configuration

### Environment Variables

Create `.env` file (see `examples/.env.example`):

```bash
OPENAI_API_KEY=sk-your-api-key-here
YOUTUBE_API_KEY=optional-for-read-only-operations
```

### OpenAI Setup

1. Create account at https://platform.openai.com
2. Generate API key from dashboard
3. Add to `.env` file
4. Ensure billing is configured (GPT API requires payment)

**Recommended Model**: `gpt-4` or `gpt-3.5-turbo`

### Translation Languages

Configure target languages in script or via config:

```python
LANGUAGES = ["en", "es", "fr", "de"]  # English, Spanish, French, German
```

## Queue Processing Workflow

```
┌──────────────────────────────────────┐
│ Load video_queue.json                │
└────────┬─────────────────────────────┘
         │
    ┌────▼─────┐
    │ For each │
    │ video    │
    └────┬─────┘
         │
    ┌────▼─────────────────────────────┐
    │ Call OpenAI API                  │
    │ - Translate title                │
    │ - Translate description          │
    └────┬─────────────────────────────┘
         │
    ┌────▼─────────────────────────────┐
    │ Update YouTube video metadata    │
    │ - Set translated text            │
    │ - Set language codes             │
    └────┬─────────────────────────────┘
         │
    ┌────▼─────────────────────────────┐
    │ Update state files               │
    │ - Append to processed.json       │
    │ - Remove from video_queue.json   │
    └────┬─────────────────────────────┘
         │
    ┌────▼─────┐
    │ Success? │
    └──┬───┬───┘
       │   │
    Yes│   │No (quota/error)
       │   │
       │   └──> Stop, resume later
       │
    Next video
```

## Resuming After Quota Exhaustion

If YouTube API quota is exceeded mid-batch:

```bash
# Check how many were processed
wc -l processed.json

# Manual queue adjustment (remove first N processed)
python3 -c "import json; q=json.load(open('video_queue.json')); json.dump(q[50:], open('video_queue.json','w'), indent=2)"

# Resume processing
python3 process_translation.py
```

Or use `--skip` flag:

```bash
# Skip first 50 videos in queue
python3 process_translation.py --skip 50
```

## API Quota Management

### YouTube Data API

- **Daily quota**: 10,000 units
- **Update operation**: ~50 units per video
- **Max videos/day**: ~200 updates

**Strategies**:
- Process in smaller batches (20-30 videos)
- Use dry-run mode first
- Schedule updates after midnight PT (quota reset)

### OpenAI API

- **Rate limits**: Vary by account tier
- **Cost**: ~$0.01-0.05 per video (depends on text length and model)
- **Recommended**: Monitor usage in OpenAI dashboard

**Error handling**:
- Script automatically stops on quota errors
- Resume from where you left off
- No duplicate processing (uses queue system)

## Translation Quality

### GPT Prompts

Customize translation prompts for better results:

```python
prompt = f"""
Translate the following YouTube video metadata to {target_lang}:

Title: {original_title}
Description: {original_description}

Requirements:
- Keep SEO keywords
- Maintain formatting (line breaks, lists)
- Preserve URLs and hashtags
- Natural, engaging language
- Max 100 characters for title
"""
```

### Supported Languages

YouTube supports 80+ languages. Common codes:
- `en` - English
- `es` - Spanish
- `es-419` - Spanish (Latin America)
- `fr` - French
- `de` - German
- `pt` - Portuguese
- `ja` - Japanese
- `ko` - Korean

See full list: https://developers.google.com/youtube/v3/docs/i18nLanguages/list

## Use Cases

### Translate New Uploads

```bash
# Export last week's videos
cd video-fetching
python3 list_videos.py --days 7

# Extract to queue
jq '[.[] | {videoId, title, description, defaultLanguage}]' video_list.json > ../translation-automation/video_queue.json

# Process translations
cd ../translation-automation
python3 process_translation.py
```

### Ensure All Videos Have Language Set

```bash
# Fetch all videos
cd video-fetching
python3 list_videos.py --all

# Update default language
cd ../translation-automation
python3 ensure_settings.py --input ../video_list.json --language en
```

### Bulk Publish Private Videos

```bash
# Set all to public
python3 set_public.py --input video_list.json

# Or specific subset
jq '[.[] | select(.title | contains("Product Launch"))]' video_list.json > launch_videos.json
python3 set_public.py --input launch_videos.json
```

## Error Handling

### Common Errors

**OpenAI API Key Missing**:
```
Error: OPENAI_API_KEY not found in environment
```
Solution: Create `.env` file with valid API key

**YouTube Quota Exceeded**:
```
HttpError 403: quotaExceeded
```
Solution: Wait for quota reset or reduce batch size

**Invalid Video ID**:
```
HttpError 404: Video not found
```
Solution: Check video still exists and is owned by authenticated account

### Safe Processing

**Always dry-run first**:
```bash
python3 ensure_settings.py --input videos.json --dry-run
```

**Process in batches**:
```bash
# Split queue into chunks
jq '.[:50]' video_queue.json > batch1.json
jq '.[50:100]' video_queue.json > batch2.json

# Process each batch
python3 process_translation.py --input batch1.json
# Wait, check results
python3 process_translation.py --input batch2.json
```

## Integration Examples

### With Shorts Management

```bash
# Find today's shorts
cd shorts-management
python3 shorts_finder.py

# Convert to translation queue
jq '[.[] | {videoId, title, description}]' videos_today.json > ../translation-automation/video_queue.json

# Process
cd ../translation-automation
python3 process_translation.py
```

### Automated Daily Translation

```bash
#!/bin/bash
# daily_translate.sh

cd video-fetching
python3 list_videos.py --days 1

if [ -s video_list.json ]; then
  jq '[.[] | {videoId, title, description}]' video_list.json > ../translation-automation/video_queue.json
  cd ../translation-automation
  python3 process_translation.py
fi
```

## Examples Directory

- `.env.example` - Template for environment variables

## Notes

- **Authentication**: Uses same OAuth flow as other modules (requires `client_secret.json`)
- **State preservation**: Queue system ensures no duplicate processing
- **Idempotent**: Safe to re-run - skips already processed videos
- **Language codes**: YouTube uses BCP-47 standard (ISO 639-1)
- **Metadata limits**: Titles max 100 chars, descriptions max 5000 chars

## Security

**Never commit**:
- `.env` (contains API keys)
- `video_queue.json` (may contain unpublished video data)
- `processed.json` (contains video metadata)

All are in `.gitignore`.

## See Also

- [shared/README.md](../shared/README.md) - YouTube authentication
- [docs/SETUP.md](../docs/SETUP.md) - Initial OAuth setup
- [docs/SECURITY.md](../docs/SECURITY.md) - API key management
- [shorts-management/README.md](../shorts-management/README.md) - Alternative translation system
