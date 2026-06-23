"""JSON-based settings manager."""

import json
import logging
from pathlib import Path
from typing import Optional

from models import AppSettings

from .constants import SETTINGS_FILE
from .mixins import (
    KeywordSettingsMixin,
    NotifierSettingsMixin,
    PresetSettingsMixin,
    SettingsNormalizationMixin,
    SettingsRecoveryMixin,
    SettingsSerializationMixin,
    SettingsDeserializationMixin,
)

class SettingsManager(
    SettingsNormalizationMixin,
    SettingsSerializationMixin,
    SettingsDeserializationMixin,
    SettingsRecoveryMixin,
    KeywordSettingsMixin,
    NotifierSettingsMixin,
    PresetSettingsMixin,
):
    """Manages application settings with JSON persistence."""

    VALID_PLATFORMS = ("danggeun", "bunjang", "joonggonara")
    VALID_SCRAPER_MODES = ("playwright_primary", "selenium_primary", "selenium_only")

    def __init__(self, settings_path: Optional[str] = None):
        self.settings_path = Path(settings_path or SETTINGS_FILE)
        self.logger = logging.getLogger("SettingsManager")
        self.load_recovery_state: dict[str, object] = {
            "used_default": False,
            "recovered_from_backup": False,
            "broken_settings_path": None,
            "recovered_backup_path": None,
            "error": None,
            "normalized_fields": [],
        }
        self.last_recovered_backup: Optional[str] = None
        self.settings = self.load()


    def load(self) -> AppSettings:
        """Load settings from JSON file"""
        if not self.settings_path.exists():
            self._reset_load_recovery_state()
            return self._create_default()

        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._reset_load_recovery_state()
            return self._from_dict(data)
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
            print(f"Error loading settings: {e}")
            return self._recover_from_broken_settings(e)


    def save(self) -> bool:
        """Save settings to JSON file"""
        try:
            data = self._to_dict(self.settings)
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

