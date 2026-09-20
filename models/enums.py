"""Domain enums (platform, notification channel, sale status, theme)."""

from enum import Enum


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


class ThemeMode(Enum):
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


__all__ = ["Platform", "NotificationType", "SaleStatus", "ThemeMode"]
