"""Compatibility facade for settings serialization."""

from .mixins.serialization import SettingsSerializationMixin
from .manager import SettingsManager

__all__ = ["SettingsManager", "SettingsSerializationMixin"]
