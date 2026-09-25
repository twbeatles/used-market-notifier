from typing import TYPE_CHECKING
"""Mixin module: presets."""

from models import KeywordPreset, SearchKeyword


if TYPE_CHECKING:
    from app_settings.manager import SettingsManager
    _HostBase_PresetSettingsMixin = SettingsManager
else:
    _HostBase_PresetSettingsMixin = object

class PresetSettingsMixin(_HostBase_PresetSettingsMixin):
    """Presets behavior."""

    def add_preset(self, preset: KeywordPreset) -> None:
        """Add a new keyword preset"""
        self.settings.keyword_presets.append(preset)
        self.save()


    def remove_preset(self, index: int) -> None:
        """Remove a preset by index"""
        if 0 <= index < len(self.settings.keyword_presets):
            self.settings.keyword_presets.pop(index)
            self.save()


    def get_presets(self) -> list[KeywordPreset]:
        """Get all presets"""
        return self.settings.keyword_presets


    def apply_preset(self, preset: KeywordPreset, keyword_text: str) -> SearchKeyword:
        """Create a SearchKeyword from preset with given keyword text"""
        return SearchKeyword(
            keyword=keyword_text,
            min_price=preset.min_price,
            max_price=preset.max_price,
            location=preset.location,
            exclude_keywords=preset.exclude_keywords.copy(),
            platforms=preset.platforms.copy(),
        )
