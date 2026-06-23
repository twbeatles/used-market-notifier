"""Compatibility facade for settings presets."""

from .mixins.presets import PresetSettingsMixin
from .manager import SettingsManager

__all__ = ["SettingsManager", "PresetSettingsMixin"]
