"""Mixin module: notifiers."""

from typing import Optional, TYPE_CHECKING
from models import NotifierConfig, NotificationType


if TYPE_CHECKING:
    from app_settings.manager import SettingsManager
    _HostBase_NotifierSettingsMixin = SettingsManager
else:
    _HostBase_NotifierSettingsMixin = object

class NotifierSettingsMixin(_HostBase_NotifierSettingsMixin):
    """Notifiers behavior."""

    def get_telegram_config(self) -> Optional[NotifierConfig]:
        for n in self.settings.notifiers:
            if n.type == NotificationType.TELEGRAM:
                return n
        return None


    def get_discord_config(self) -> Optional[NotifierConfig]:
        for n in self.settings.notifiers:
            if n.type == NotificationType.DISCORD:
                return n
        return None


    def get_slack_config(self) -> Optional[NotifierConfig]:
        for n in self.settings.notifiers:
            if n.type == NotificationType.SLACK:
                return n
        return None

    # Preset methods
