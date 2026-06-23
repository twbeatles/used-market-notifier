"""Application settings package."""

from .constants import SETTINGS_FILE
from .manager import SettingsManager

__all__ = ["SettingsManager", "SETTINGS_FILE"]
