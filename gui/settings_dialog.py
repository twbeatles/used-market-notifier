"""Compatibility facade for settings dialog classes."""

from .settings_panels.dialog import (
    CleanupWorker,
    MessageTemplateEditDialog,
    NotificationTestThread,
    SettingsDialog,
    TagRuleEditDialog,
)

__all__ = [
    "SettingsDialog",
    "CleanupWorker",
    "TagRuleEditDialog",
    "MessageTemplateEditDialog",
    "NotificationTestThread",
]
