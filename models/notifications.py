"""Notification log, schedule, and channel-config models."""

from dataclasses import dataclass, field
from typing import Optional

from .enums import NotificationType


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


__all__ = ["NotificationLog", "NotificationSchedule", "NotifierConfig"]
