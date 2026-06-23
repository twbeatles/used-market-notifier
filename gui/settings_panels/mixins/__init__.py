"""Settings dialog tab mixins."""

from .general import GeneralSettingsMixin
from .notifications import NotificationSettingsMixin
from .schedule import ScheduleSettingsMixin
from .seller import SellerSettingsMixin
from .maintenance import MaintenanceSettingsMixin
from .auto_tagging import AutoTaggingSettingsMixin
from .message_templates import MessageTemplatesSettingsMixin
from .persistence import SettingsPersistenceMixin

__all__ = [
    "GeneralSettingsMixin",
    "NotificationSettingsMixin",
    "ScheduleSettingsMixin",
    "SellerSettingsMixin",
    "MaintenanceSettingsMixin",
    "AutoTaggingSettingsMixin",
    "MessageTemplatesSettingsMixin",
    "SettingsPersistenceMixin",
]
