# config.py

# Telegram Configuration
# Please fill in your Telegram Bot Token and Chat ID
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID_HERE"

# Search Keywords
# Add the keywords you want to monitor
KEYWORDS = [
    "맥북 에어 M2 미개봉",
    "아이폰 15 프로",
    "닌텐도 스위치 OLED"
]

# Database Config
DB_PATH = "listings.db"

# Scraper Config
CHECK_INTERVAL_SECONDS = 300  # 5 minutes
HEADLESS_MODE = True
