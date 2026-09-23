"""Main-window behavior mixins (one responsibility per module)."""

from .lifecycle import LifecycleMixin
from .live_refresh import LiveRefreshMixin
from .maintenance import MaintenanceMixin
from .monitoring import MonitoringMixin
from .recovery import RecoveryMixin
from .shortcuts import ShortcutsMixin
from .theme import ThemeMixin
from .tray import TrayMixin
from .ui_setup import UiSetupMixin
from .updater import UpdaterMixin

__all__ = [
    "LifecycleMixin",
    "LiveRefreshMixin",
    "MaintenanceMixin",
    "MonitoringMixin",
    "RecoveryMixin",
    "ShortcutsMixin",
    "ThemeMixin",
    "TrayMixin",
    "UiSetupMixin",
    "UpdaterMixin",
]
