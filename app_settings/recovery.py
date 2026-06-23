"""Compatibility facade for settings recovery."""

from .mixins.recovery import SettingsRecoveryMixin
from .manager import SettingsManager

__all__ = ["SettingsManager", "SettingsRecoveryMixin"]
