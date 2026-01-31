"""Configuration settings for YouTube scripts."""

# API Configuration
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.pickle"

# Output Configuration
DEFAULT_OUTPUT_FILE = "video_list.json"
BACKUP_DIR = "backups"

# Date Filtering
DEFAULT_DAYS_BACK = 7
MAX_DAYS_BACK = 365

# API Limits
MAX_RESULTS_PER_REQUEST = 50
DEFAULT_MAX_VIDEOS = None  # None means no limit

# Video Details to include
INCLUDE_STATISTICS = True
INCLUDE_TAGS = True
INCLUDE_DESCRIPTION = True 