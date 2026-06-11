"""Notification queue payloads and policy helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from models import AppSettings, Item


@dataclass
class NotificationJob:
    """Queued notification payload."""

    item: Item
    is_price_change: bool = False
    old_price: Optional[str] = None
    new_price: Optional[str] = None
    listing_id: Optional[int] = None
    attempts: int = 0
    enqueued_at: float = 0.0
    target_channels: list[str] = field(default_factory=list)


@dataclass
class NotificationDeliveryResult:
    """Per-channel delivery outcome for one queued notification."""

    attempted_channels: list[str] = field(default_factory=list)
    successful_channels: list[str] = field(default_factory=list)
    failed_channels: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class NotificationPolicyDecision:
    """Decision for whether a notification may be sent now."""

    allowed: bool
    status: str = ""
    reason: str = ""


class NotificationPolicy:
    """Shared notification enablement and schedule policy."""

    def __init__(self, settings: AppSettings):
        self.settings = settings

    def evaluate(self) -> NotificationPolicyDecision:
        if not self.settings.notifications_enabled:
            return NotificationPolicyDecision(False, "skipped_disabled", "global notifications disabled")

        schedule = self.settings.notification_schedule
        if not schedule.is_active_now():
            return NotificationPolicyDecision(False, "skipped_schedule", "outside scheduled hours")

        return NotificationPolicyDecision(True)
