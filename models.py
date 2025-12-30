# models.py
"""Data models for Used Market Notifier"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Platform(Enum):
    DANGGEUN = "danggeun"
    BUNJANG = "bunjang"
    JOONGGONARA = "joonggonara"


class NotificationType(Enum):
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"


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
    price_numeric: Optional[int] = None  # Parsed price for filtering

    def parse_price(self) -> int:
        """Extract numeric price from price string"""
        if self.price_numeric is not None:
            return self.price_numeric
        try:
            # Remove non-numeric characters except digits
            cleaned = ''.join(c for c in self.price if c.isdigit())
            self.price_numeric = int(cleaned) if cleaned else 0
        except:
            self.price_numeric = 0
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
        if not item.location:
            return True  # Allow if location unknown
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
class AppSettings:
    """Application settings"""
    check_interval_seconds: int = 300
    headless_mode: bool = True
    db_path: str = "listings.db"
    minimize_to_tray: bool = True
    start_minimized: bool = False
    auto_start_monitoring: bool = False
    notification_schedule: NotificationSchedule = field(default_factory=NotificationSchedule)
    notifiers: list[NotifierConfig] = field(default_factory=list)
    keywords: list[SearchKeyword] = field(default_factory=list)
