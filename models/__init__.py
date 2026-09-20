# models.py
"""Data models for Used Market Notifier.

Canonical implementations live in this package, split by domain
(SRP: one module per concept group). This ``__init__`` re-exports the
previous ``models.py`` public surface so every existing
``from models import ...`` keeps working.
"""

from price_utils import parse_price_kr

from .app_settings import AppSettings, KeywordPreset
from .enums import NotificationType, Platform, SaleStatus, ThemeMode
from .favorites import FavoriteItem, SellerFilter
from .item import Item
from .notifications import NotificationLog, NotificationSchedule, NotifierConfig
from .search_keyword import SearchKeyword
from .tagging import MessageTemplate, TagRule

__all__ = [
    "AppSettings",
    "FavoriteItem",
    "Item",
    "KeywordPreset",
    "MessageTemplate",
    "NotificationLog",
    "NotificationSchedule",
    "NotificationType",
    "NotifierConfig",
    "Platform",
    "SaleStatus",
    "SearchKeyword",
    "SellerFilter",
    "TagRule",
    "ThemeMode",
    "parse_price_kr",
]
