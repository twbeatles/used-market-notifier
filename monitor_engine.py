"""Compatibility facade for the engine package."""

from engine.monitor import (
    MonitorEngine,
    NotificationDeliveryResult,
    NotificationJob,
    NotificationPolicy,
    NotificationPolicyDecision,
    NotifierProtocol,
    ScraperProtocol,
    SettingsProvider,
)

__all__ = [
    "MonitorEngine",
    "NotificationDeliveryResult",
    "NotificationJob",
    "NotificationPolicy",
    "NotificationPolicyDecision",
    "NotifierProtocol",
    "ScraperProtocol",
    "SettingsProvider",
]
