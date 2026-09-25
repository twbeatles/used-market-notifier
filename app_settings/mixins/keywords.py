from typing import TYPE_CHECKING
"""Mixin module: keywords."""

from models import SearchKeyword


if TYPE_CHECKING:
    from app_settings.manager import SettingsManager
    _HostBase_KeywordSettingsMixin = SettingsManager
else:
    _HostBase_KeywordSettingsMixin = object

class KeywordSettingsMixin(_HostBase_KeywordSettingsMixin):
    """Keywords behavior."""

    def add_keyword(self, keyword: SearchKeyword) -> None:
        self.settings.keywords.append(keyword)
        self.save()


    def remove_keyword(self, index: int) -> None:
        if 0 <= index < len(self.settings.keywords):
            self.settings.keywords.pop(index)
            self.save()


    def update_keyword(self, index: int, keyword: SearchKeyword) -> None:
        if 0 <= index < len(self.settings.keywords):
            self.settings.keywords[index] = keyword
            self.save()
