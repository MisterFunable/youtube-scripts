# YouTube Shorts Management Tools

A comprehensive suite of Python scripts for managing YouTube Shorts, including finding, analyzing, translating, and updating video metadata.

## 📋 Overview

This collection of tools helps you:
- **Find and export** Shorts from your YouTube channel
- **Analyze content** to extract frequent words and phrases
- **Translate videos** using custom translation dictionaries
- **Update metadata** with automated translations and settings
- **Manage video settings** with configurable defaults

## 🛠️ Scripts

### Core Scripts

#### `shorts_finder.py` - Find and Export Shorts
Finds YouTube Shorts from your channel and exports them to JSON.

```bash
# Find today's Shorts
python shorts_finder.py

# Find Shorts from last 7 days
python shorts_finder.py --days 7

# Find all Shorts (no date filter)
python shorts_finder.py --all

# Limit results
python shorts_finder.py --max 10

# Custom output file
python shorts_finder.py --output my_shorts.json

# Test API connection
python shorts_finder.py --test
```

#### `shorts_updater.py` - Update Video Metadata
Updates video titles, descriptions, tags, and visibility with translations and settings.

```bash
# Update videos from default file
python shorts_updater.py

# Update specific video
python shorts_updater.py --video-id VIDEO_ID

# Dry run (preview changes)
python shorts_updater.py --dry-run

# Custom input file
python shorts_updater.py --input my_videos.json

# Target language
python shorts_updater.py --language es

# Test API connection
python shorts_updater.py --test
```

#### `word_extractor.py` - Content Analysis
Extracts frequent words and phrases from video titles and descriptions.

```bash
# Analyze all videos
python word_extractor.py

# Limit analysis to recent videos
python word_extractor.py --max-videos 50

# Custom output file
python word_extractor.py --output my_words.json

# Adjust phrase length
python word_extractor.py --phrase-length 4

# Test API connection
python word_extractor.py --test
```

### Legacy Scripts

#### `find_videos.py` - Legacy Video Finder
Simple script to find today's Shorts (basic version of `shorts_finder.py`).

#### `update_videos.py` - Legacy Video Updater
Basic video metadata updater (simplified version of `shorts_updater.py`).

#### `extract-frequent-words.py` - Legacy Word Extractor
Basic word extraction (simplified version of `word_extractor.py`).

### Service Modules

#### `shorts_service.py` - Core Service
Main service class handling YouTube API operations for Shorts.

#### `translation_service.py` - Translation Engine
Handles custom translations using JSON dictionaries.

## ⚙️ Configuration

### `video_settings.json`
Default settings for video metadata:

```json
{
  "default_title_prefix": "",
  "default_description_prefix": "Gracias por mirar! ✨",
  "default_visibility": "private",
  "audience": "notMadeForKids",
  "license": "youtube",
  "language": "es",
  "enable_languages": ["en", "es", "es-419"],
  "push_to_subscribers": false,
  "tags_template": ["#toys", "#figures", "#unboxing"],
  "fallback_to_gpt": true
}
```

### `custom_translations.json`
Custom translation dictionary for automated translations.

### Authentication Files
- `client_secret.json` - YouTube API credentials
- `token.pickle` - Authentication token

## 📊 Output Files

- `videos_today.json` - Exported video data
- `frequent_words.json` - Extracted words/phrases
- `videos_today.json` - Default video export

## 🔧 Setup

1. **Install Dependencies**
   ```bash
   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client isodate
   ```

2. **Configure Authentication**
   - Place your `client_secret.json` in the shorts folder
   - Run any script to authenticate (will create `token.pickle`)

3. **Customize Settings**
   - Edit `video_settings.json` for default metadata
   - Add custom translations to `custom_translations.json`

## 🚀 Workflow Examples

### Daily Shorts Management
```bash
# 1. Find today's Shorts
python shorts_finder.py

# 2. Update metadata with translations
python shorts_updater.py

# 3. Analyze content for insights
python word_extractor.py
```

### Content Analysis
```bash
# Analyze recent content
python word_extractor.py --max-videos 100 --output recent_analysis.json

# Find all Shorts for comprehensive analysis
python shorts_finder.py --all --output all_shorts.json
```

### Batch Updates
```bash
# Preview changes before applying
python shorts_updater.py --dry-run

# Apply updates to specific videos
python shorts_updater.py --video-id VIDEO_ID1 --video-id VIDEO_ID2
```

## 🔍 Features

### Smart Shorts Detection
- Automatically identifies videos ≤ 60 seconds
- Filters by publication date
- Includes view counts and engagement metrics

### Translation System
- Custom translation dictionaries
- Fallback to external services
- Support for multiple languages
- Case-insensitive matching

### Content Analysis
- Extracts words and phrases
- Filters common stopwords
- Configurable phrase lengths
- Frequency analysis

### Metadata Management
- Automated title/description prefixes
- Default tag templates
- Visibility controls
- Audience settings

## 📝 Notes

- All scripts use the YouTube Data API v3
- Authentication tokens are cached in `token.pickle`
- Legacy scripts are kept for compatibility
- New scripts offer enhanced features and better error handling

## 🐛 Troubleshooting

### API Connection Issues
```bash
# Test connection
python shorts_finder.py --test
```

### Authentication Problems
- Delete `token.pickle` and re-authenticate
- Ensure `client_secret.json` is valid

### Translation Issues
- Check `custom_translations.json` format
- Verify target language codes

## 📄 License

This project uses the YouTube Data API. Ensure compliance with YouTube's Terms of Service and API quotas.

### How to Resume Processing from a Specific Video

If you need to resume processing from a specific position (e.g., after hitting the YouTube API quota):

1. **Remove the already-processed videos from `videos_today.json`.**  
   For example, to start from the 349th video onward, run this command in your terminal:

   ```bash
   python3 -c "import json; d=json.load(open('youtube/shorts/videos_today.json')); json.dump(d[348:], open('youtube/shorts/videos_today.json','w'), indent=2, ensure_ascii=False)"
   ```

2. **Run the updater as usual:**

   ```bash
   python3 shorts_updater.py --input videos_today.json
   ```

This will ensure the script starts from the correct position and processes the remaining videos.
