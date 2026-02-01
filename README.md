<div align="right">

[![n8n](https://img.shields.io/badge/n8n-EA4B71?style=for-the-badge&logo=n8n&logoColor=white)](https://n8n.io)
[![YouTube API](https://img.shields.io/badge/YouTube_API-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://developers.google.com/youtube)
[![OpenAI API](https://img.shields.io/badge/OpenAI_API-412991?style=for-the-badge&logo=openai&logoColor=white)](https://platform.openai.com)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Built with Cursor](https://img.shields.io/badge/Built_with-Cursor-000000?style=for-the-badge&logo=cursor&logoColor=white)](https://cursor.sh)

</div>

# YouTube Automation Toolkit - Pre-N8N Implementation

A powerful Python-based automation suite for YouTube channel management, featuring video analytics, content translation, and Shorts workflow automation. Built before migrating to N8N workflows - preserved as reference implementation.

---

Python-based automation tools for YouTube channel management, created before migrating to N8N workflows. Preserved as a reference implementation and backup of functional features.

## Context

This repository represents "the old-fashioned way" of automating YouTube operations using Python and the YouTube Data API v3. While fully functional, maintaining these scripts became challenging, leading to an eventual migration to N8N for easier workflow management.

**This repo serves as**:
- Reference implementation for YouTube API patterns
- Backup of working automation features
- Foundation for future N8N workflow design
- Learning resource for YouTube API usage

## Features

### 🎥 Video Fetching (`video-fetching/`)
Fetch and export video metadata from your YouTube channel.

**Key Features**:
- Configurable date range filtering
- JSON export for downstream processing
- Automatic pagination and batching
- Backup utilities

[Read more →](./video-fetching/README.md)

### 📊 Metrics Analysis (`metrics-analysis/`)
Analyze video performance across multiple dimensions.

**Key Features**:
- Identify top-performing videos
- Find optimal publish times and days
- Track popularity trends
- N8N-ready JavaScript version included

[Read more →](./metrics-analysis/README.md)

### 🌐 Translation Automation (`translation-automation/`)
Automated video metadata translation using OpenAI.

**Key Features**:
- Queue-based processing system
- GPT-powered translations
- Batch visibility updates
- Multi-language support

[Read more →](./translation-automation/README.md)

### 📱 Shorts Management (`shorts-management/`)
**Most mature system** - Complete Shorts workflow automation.

**Key Features**:
- Find and filter YouTube Shorts
- Automated translation and metadata updates
- Content analysis (frequent word extraction)
- Web UI for management
- Docker deployment ready

[Read more →](./shorts-management/README.md)

## Quick Start

### 1. Install Dependencies

```bash
# Install shared dependencies
pip install -r requirements.txt

# Or install module-specific dependencies
pip install -r video-fetching/requirements.txt
pip install -r metrics-analysis/requirements.txt
pip install -r translation-automation/requirements.txt
pip install -r shorts-management/requirements.txt
```

### 2. Setup Authentication

All modules require YouTube Data API v3 access via OAuth 2.0.

**Quick setup**:
1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable YouTube Data API v3
3. Create OAuth 2.0 credentials (Desktop app)
4. Download as `client_secret.json`
5. Place in repository root

[Detailed setup guide →](./docs/SETUP.md)

### 3. Run Your First Script

```bash
# Test API connection
cd video-fetching
python3 list_videos.py --test

# Fetch recent videos
python3 list_videos.py --days 7

# Analyze metrics
cd ../metrics-analysis
python3 metrics_processing.py
```

## Architecture

### Shared Utilities (`shared/`)

Core authentication and API wrappers used across all modules:
- `youtube_auth.py` - OAuth 2.0 authentication manager
- `youtube_service.py` - YouTube API service wrapper
- `youtube_utils.py` - Helper functions for data processing
- `config.py` - Centralized configuration constants

All modules import from `shared/` for consistent authentication and API access patterns.

### Module Independence

Each feature module is self-contained:
- Own README with usage examples
- Own `requirements.txt`
- Can be used independently or together
- Shares common utilities from `shared/`

See [CLAUDE.md](./CLAUDE.md) for detailed architectural documentation.

## Security

**CRITICAL**: Never commit sensitive files to version control.

**Required files** (not included in repo):
- `client_secret.json` - OAuth credentials from Google Cloud
- `token.pickle` - Cached authentication token (auto-generated)
- `.env` - API keys for OpenAI, etc.
- `video_list.json`, `video_queue.json` - Generated data files

All sensitive files are protected by `.gitignore`.

[Security best practices →](./docs/SECURITY.md)

## Common Workflows

### Daily Video Monitoring

```bash
# Fetch today's videos
cd video-fetching
python3 list_videos.py --days 1

# Analyze performance
cd ../metrics-analysis
python3 metrics_processing.py
```

### Shorts Management Pipeline

```bash
cd shorts-management

# Find today's Shorts
python3 shorts_finder.py

# Update metadata with translations
python3 shorts_updater.py --dry-run  # Preview first
python3 shorts_updater.py            # Apply changes

# Analyze content
python3 word_extractor.py
```

### Translation Automation

```bash
# Export videos to translate
cd video-fetching
python3 list_videos.py --days 7

# Create queue
jq '[.[] | {videoId, title, description}]' video_list.json > ../translation-automation/video_queue.json

# Process translations
cd ../translation-automation
python3 process_translation.py
```

### Metrics Analysis for N8N

```bash
# Fetch data
cd video-fetching
python3 list_videos.py --days 30

# Process locally
cd ../metrics-analysis
python3 metrics_processing.py > results.json

# Or use metrics_processing_n8n.js in n8n Function node
```

## API Quota Management

YouTube Data API quota: **10,000 units/day** (resets midnight PT)

**Typical costs**:
- List 100 videos: ~4 units
- Update 10 videos: ~500 units
- Full analysis run: ~50 units

**Tips**:
- Use `--dry-run` before batch updates
- Schedule heavy operations after quota reset
- Monitor usage in [Google Cloud Console](https://console.cloud.google.com/)

## Why This Repo Exists

### The Journey

1. **Started**: Manual Python scripts for one-off tasks
2. **Evolved**: Built increasingly sophisticated features
3. **Struggled**: Maintenance and scheduling became burdensome
4. **Migrated**: Moved to N8N for better workflow management
5. **Preserved**: Kept this repo as reference and backup

### Current Status

- ✅ **Fully functional** - All scripts work as documented
- ✅ **Battle-tested** - Used in production before N8N migration
- ✅ **Well-documented** - Comprehensive READMEs and examples
- ⚠️ **Not actively maintained** - Preserved as-is, not for new features
- 📚 **Reference implementation** - Great for learning YouTube API

### Use This Repo If...

- You want to understand YouTube API operations
- You need a quick Python script for one-off tasks
- You're designing N8N workflows and want reference implementations
- You prefer code over visual workflow builders
- You're learning YouTube Data API v3

### Consider N8N Instead If...

- You need recurring scheduled workflows
- You want visual workflow design
- You need complex conditional logic
- You want easier maintenance and updates
- You're integrating with multiple services

## Module Documentation

| Module | Purpose | Key Scripts | Documentation |
|--------|---------|-------------|---------------|
| `shared/` | Authentication & API wrappers | `youtube_auth.py`, `youtube_service.py` | [README](./shared/README.md) |
| `video-fetching/` | Export video metadata | `list_videos.py` | [README](./video-fetching/README.md) |
| `metrics-analysis/` | Performance analytics | `metrics_processing.py` | [README](./metrics-analysis/README.md) |
| `translation-automation/` | Automated translations | `process_translation.py` | [README](./translation-automation/README.md) |
| `shorts-management/` | Complete Shorts workflow | `shorts_finder.py`, `shorts_updater.py` | [README](./shorts-management/README.md) |

## Documentation

- [SETUP.md](./docs/SETUP.md) - OAuth setup and authentication guide
- [SECURITY.md](./docs/SECURITY.md) - Security best practices and credential management
- [CLAUDE.md](./CLAUDE.md) - Detailed architectural documentation and patterns

## Requirements

### Python Version
- Python 3.7 or higher
- Tested on Python 3.9+

### Core Dependencies
```
google-api-python-client>=2.131.0
google-auth>=2.34.0
google-auth-oauthlib>=1.2.1
isodate>=0.6.1
```

### Optional Dependencies
- `openai>=1.3.0` - For translation automation
- `flask>=2.3.3` - For Shorts web UI
- `psutil>=5.9.5` - For system monitoring

See individual module `requirements.txt` for specific dependencies.

## Contributing

This repository is **archived for reference** and not accepting new features. However:

- ✅ Bug fixes and security patches welcome
- ✅ Documentation improvements appreciated
- ✅ Example additions helpful
- ❌ New features better suited for N8N workflows

## Troubleshooting

### Authentication Issues

```bash
# Delete cached token and re-authenticate
rm token.pickle
python3 video-fetching/list_videos.py --test
```

### API Quota Exceeded

```bash
# Check quota usage in Google Cloud Console
# https://console.cloud.google.com/apis/dashboard

# Wait for reset (midnight PT) or reduce batch sizes
```

### Import Errors

```bash
# Ensure running from correct directory
cd video-fetching  # Not from root
python3 list_videos.py

# Or use absolute imports
PYTHONPATH=/path/to/repo python3 video-fetching/list_videos.py
```

### Missing Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Or module-specific
pip install -r shorts-management/requirements.txt
```

## Project Structure

```
youtube-automations/
├── .gitignore                    # Comprehensive ignore rules
├── README.md                     # This file
├── CLAUDE.md                     # Architectural documentation
├── requirements.txt              # Shared dependencies
│
├── shared/                       # Shared utilities
│   ├── README.md
│   ├── youtube_auth.py
│   ├── youtube_service.py
│   ├── youtube_utils.py
│   └── config.py
│
├── video-fetching/               # Video export tools
│   ├── README.md
│   ├── requirements.txt
│   ├── list_videos.py
│   ├── backup_videos.py
│   └── examples/
│
├── metrics-analysis/             # Performance analytics
│   ├── README.md
│   ├── requirements.txt
│   ├── metrics_processing.py
│   ├── metrics_processing_n8n.js
│   └── examples/
│
├── translation-automation/       # Translation tools
│   ├── README.md
│   ├── requirements.txt
│   ├── process_translation.py
│   ├── ensure_settings.py
│   ├── set_public.py
│   └── examples/
│
├── shorts-management/            # Complete Shorts system
│   ├── README.md
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── shorts_finder.py
│   ├── shorts_updater.py
│   ├── word_extractor.py
│   ├── web_ui.py
│   ├── templates/
│   └── examples/
│
└── docs/                         # Documentation
    ├── SETUP.md                  # OAuth setup guide
    └── SECURITY.md               # Security practices
```

## License

MIT License - Feel free to learn from and adapt these scripts.

## Acknowledgments

Built with:
- [YouTube Data API v3](https://developers.google.com/youtube/v3)
- [Google API Python Client](https://github.com/googleapis/google-api-python-client)
- [OpenAI API](https://platform.openai.com/)
- [Flask](https://flask.palletsprojects.com/)

---

**Note**: This is a preserved reference implementation. For new projects, consider using [N8N](https://n8n.io/) for more maintainable workflow automation.
