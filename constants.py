# constants.py
"""Centralized constants for the application"""

# Database
DB_CACHE_TTL_SECONDS = 30
DEFAULT_DB_PATH = "listings.db"

# Pagination
DEFAULT_PAGE_SIZE = 50

# Timing
SCRAPE_DELAY_SECONDS = 2
DRIVER_WAIT_TIMEOUT = 10
DRIVER_PAGE_LOAD_TIMEOUT = 30
AUTO_REFRESH_INTERVAL_MS = 60000
SEARCH_DEBOUNCE_MS = 300
KEYWORD_PAUSE_MS = 2000

# Retry
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 1.0
RETRY_BACKOFF_MULTIPLIER = 2.0

# Backup
DEFAULT_BACKUP_DIR = "backup"
DEFAULT_BACKUP_KEEP_COUNT = 5
DEFAULT_BACKUP_INTERVAL_DAYS = 7

# Cleanup
DEFAULT_CLEANUP_DAYS = 30

# Auto-tagging default colors
TAG_COLORS = {
    'green': '#a6e3a1',
    'blue': '#89b4fa',
    'red': '#f38ba8',
    'yellow': '#f9e2af',
    'teal': '#94e2d5',
    'purple': '#cba6f7',
    'peach': '#fab387',
    'sapphire': '#74c7ec',
}

# Platform identifiers
PLATFORMS = ['danggeun', 'bunjang', 'joonggonara']

PLATFORM_NAMES = {
    'danggeun': '당근마켓',
    'bunjang': '번개장터',
    'joonggonara': '중고나라',
}

PLATFORM_ICONS = {
    'danggeun': '🥕',
    'bunjang': '⚡',
    'joonggonara': '🛒',
}

# Sale status
SALE_STATUS = {
    'for_sale': '판매중',
    'reserved': '예약중',
    'sold': '판매완료',
    'unknown': '알수없음',
}
