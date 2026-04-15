# models.py
"""Data models for Used Market Notifier"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from price_utils import parse_price_kr


class Platform(Enum):
    DANGGEUN = "danggeun"
    BUNJANG = "bunjang"
    JOONGGONARA = "joonggonara"


class NotificationType(Enum):
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"


class SaleStatus(Enum):
    """Sale status of a listing"""
    FOR_SALE = "for_sale"       # 판매중
    RESERVED = "reserved"       # 예약중
    SOLD = "sold"               # 판매완료
    UNKNOWN = "unknown"         # 상태 미확인


@dataclass
class Item:
    """Represents a listing item from any platform"""
    platform: str
    article_id: str
    title: str
    price: str
    link: str
    keyword: str
    thumbnail: Optional[str] = None
    seller: Optional[str] = None
    location: Optional[str] = None
    sale_status: Optional[str] = None
    price_numeric: Optional[int] = None  # Parsed price for filtering

    def parse_price(self) -> int:
        """Extract numeric price from price string"""
        if self.price_numeric is not None:
            return self.price_numeric
        self.price_numeric = parse_price_kr(self.price)
        return self.price_numeric


@dataclass
class SearchKeyword:
    """Represents a search keyword with filters"""
    keyword: str
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    location: Optional[str] = None
    exclude_keywords: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=lambda: ["danggeun", "bunjang", "joonggonara"])
    enabled: bool = True
    group_name: Optional[str] = None
    custom_interval: Optional[int] = None
    target_price: Optional[int] = None
    notify_enabled: bool = True  # Per-keyword notification toggle

    def matches_price(self, item: Item) -> bool:
        """Check if item price is within range"""
        price = item.parse_price()
        if price == 0:
            return True  # Allow items with unknown price
        if self.min_price and price < self.min_price:
            return False
        if self.max_price and price > self.max_price:
            return False
        return True

    def matches_location(self, item: Item) -> bool:
        """Check if item location matches filter"""
        if not self.location:
            return True

        item_platform = (item.platform or "").lower()
        # Danggeun location filtering is strict: unknown location should not pass.
        if item_platform == "danggeun":
            if not item.location:
                return False
            return self.location.lower() in item.location.lower()

        # Other platforms keep best-effort behavior.
        if not item.location:
            return True
        return self.location.lower() in item.location.lower()

    def has_excluded_words(self, item: Item) -> bool:
        """Check if item contains excluded keywords"""
        if not self.exclude_keywords:
            return False
        title_lower = item.title.lower()
        return any(ex.lower() in title_lower for ex in self.exclude_keywords)

    def matches(self, item: Item) -> bool:
        """Check if item passes all filters"""
        return (
            self.matches_price(item) and
            self.matches_location(item) and
            not self.has_excluded_words(item)
        )


@dataclass
class FavoriteItem:
    """Represents a favorited item"""
    listing_id: int
    added_at: str  # ISO format string
    notes: str = ""
    target_price: Optional[int] = None


@dataclass
class KeywordPreset:
    """Preset for quickly applying keyword configurations"""
    name: str
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    location: Optional[str] = None
    exclude_keywords: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=lambda: ["danggeun", "bunjang", "joonggonara"])


@dataclass
class NotificationLog:
    """Log of sent notifications"""
    id: int
    listing_id: int
    notification_type: str
    sent_at: str
    is_read: bool = False
    message_preview: str = ""


@dataclass
class SellerFilter:
    """Filter for specific sellers"""
    seller_name: str
    platform: str
    is_blocked: bool = True
    notes: str = ""


class ThemeMode(Enum):
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


@dataclass
class NotificationSchedule:
    """Notification schedule settings"""
    enabled: bool = True
    start_hour: int = 0  # 0-23
    end_hour: int = 24   # 0-24 (24 means midnight next day)
    days: list[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6])  # 0=Monday

    def is_active_now(self) -> bool:
        """Check if notifications are active at current time"""
        if not self.enabled:
            return False
        from datetime import datetime
        now = datetime.now()
        if now.weekday() not in self.days:
            return False
        current_hour = now.hour
        if self.start_hour <= self.end_hour:
            return self.start_hour <= current_hour < self.end_hour
        else:
            # Overnight schedule (e.g., 22:00 - 06:00)
            return current_hour >= self.start_hour or current_hour < self.end_hour


@dataclass
class NotifierConfig:
    """Configuration for a notification channel"""
    type: NotificationType
    enabled: bool = False
    token: str = ""
    chat_id: str = ""
    webhook_url: str = ""  # For Discord/Slack


@dataclass
class TagRule:
    """Rule for auto-tagging listings based on title keywords"""
    tag_name: str           # 태그 이름 (예: "A급")
    keywords: list[str] = field(default_factory=list)  # 트리거 키워드들
    color: str = "#89b4fa"  # 태그 색상
    icon: str = "🏷️"        # 태그 아이콘
    enabled: bool = True


@dataclass
class MessageTemplate:
    """Template for quick messages to sellers"""
    name: str               # 템플릿 이름
    content: str            # 템플릿 내용 (변수: {title}, {price}, {seller}, {location}, {target_price})
    platform: str = "all"   # "all", "danggeun", "bunjang", "joonggonara"


@dataclass
class AppSettings:
    """Application settings"""
    check_interval_seconds: int = 300
    headless_mode: bool = True
    db_path: str = "listings.db"
    minimize_to_tray: bool = True
    start_minimized: bool = False
    auto_start_monitoring: bool = False
    theme_mode: ThemeMode = ThemeMode.DARK
    confirm_link_open: bool = True
    notifications_enabled: bool = False  # Notifications OFF by default
    notification_schedule: NotificationSchedule = field(default_factory=NotificationSchedule)
    notifiers: list[NotifierConfig] = field(default_factory=list)
    keywords: list[SearchKeyword] = field(default_factory=list)
    keyword_presets: list[KeywordPreset] = field(default_factory=list)
    seller_filters: list[SellerFilter] = field(default_factory=list)
    
    # Backup settings (#17)
    auto_backup_enabled: bool = True
    auto_backup_interval_days: int = 7
    backup_keep_count: int = 5
    
    # Cleanup settings (#18)
    auto_cleanup_enabled: bool = False
    cleanup_days: int = 30
    cleanup_exclude_favorites: bool = True
    cleanup_exclude_noted: bool = True
    
    # Auto-tagging settings (#28)
    auto_tagging_enabled: bool = True
    tag_rules: list[TagRule] = field(default_factory=list)
    metadata_enrichment_enabled: bool = False

    # Scraper engine strategy
    # - playwright_primary: Playwright first, Selenium fallback
    # - selenium_primary: Selenium first, Playwright fallback
    # - selenium_only: Selenium only (no fallback)
    scraper_mode: str = "playwright_primary"
    fallback_on_empty_results: bool = True
    max_fallback_per_cycle: int = 3
    
    # Message templates (#29)
    message_templates: list[MessageTemplate] = field(default_factory=list)
