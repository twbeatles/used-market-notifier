"""Settings dialog tab mixins."""

from .auto_tagging import AutoTaggingSettingsMixin
from .general import GeneralSettingsMixin
from .maintenance import MaintenanceSettingsMixin
from .message_templates import MessageTemplatesSettingsMixin
from .notifications import NotificationSettingsMixin
from .persistence import SettingsPersistenceMixin
from .schedule import ScheduleSettingsMixin
from .seller import SellerSettingsMixin
from .updater import UpdateSettingsMixin

__all__ = [
    "GeneralSettingsMixin",
    "NotificationSettingsMixin",
    "ScheduleSettingsMixin",
    "SellerSettingsMixin",
    "MaintenanceSettingsMixin",
    "UpdateSettingsMixin",
    "AutoTaggingSettingsMixin",
    "MessageTemplatesSettingsMixin",
    "SettingsPersistenceMixin",
]
