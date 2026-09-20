"""Application settings and keyword presets."""

from dataclasses import dataclass, field
from typing import Optional

from .enums import ThemeMode
from .favorites import SellerFilter
from .notifications import NotificationSchedule, NotifierConfig
from .search_keyword import SearchKeyword
from .tagging import MessageTemplate, TagRule


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
    conditional_metadata_enrichment_enabled: bool = True

    # Scraper engine strategy
    # - playwright_primary: Playwright first, Selenium fallback
    # - selenium_primary: Selenium first, Playwright fallback
    # - selenium_only: Selenium only (no fallback)
    scraper_mode: str = "playwright_primary"
    fallback_on_empty_results: bool = True
    max_fallback_per_cycle: int = 3

    # Message templates (#29)
    message_templates: list[MessageTemplate] = field(default_factory=list)


__all__ = ["KeywordPreset", "AppSettings"]
