# gui/main_window.py
"""Main application window - Fixed visibility issues.

Canonical behaviors live in :mod:`gui.main.window_mixins` (one mixin per
responsibility: UI setup, tray, shortcuts, maintenance, recovery, live
refresh, monitoring, theme, lifecycle). This module only composes them
into ``MainWindow`` and owns construction.
"""

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMainWindow
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from settings_manager import SettingsManager
from monitor_engine import MonitorEngine
from backup_manager import BackupManager
from db import DatabaseManager
from gui.main.window_mixins import (
    LifecycleMixin,
    LiveRefreshMixin,
    MaintenanceMixin,
    MonitoringMixin,
    RecoveryMixin,
    ShortcutsMixin,
    ThemeMixin,
    TrayMixin,
    UiSetupMixin,
)


class MainWindow(  # pyright: ignore[reportIncompatibleMethodOverride]
    # Multiple QWidget-fragment bases re-expose identical Qt event
    # handlers whose stubs only differ in parameter names (a0/event).
    UiSetupMixin,
    TrayMixin,
    ShortcutsMixin,
    MaintenanceMixin,
    RecoveryMixin,
    LiveRefreshMixin,
    MonitoringMixin,
    ThemeMixin,
    LifecycleMixin,
    QMainWindow,
):
    """Main application window"""

    def __init__(self, settings_manager: SettingsManager | None = None):
        super().__init__()

        self.settings_manager = settings_manager or SettingsManager()
        # Shared DB connection for the UI lifetime (engine must not close this DB).
        self.db = DatabaseManager(self.settings_manager.settings.db_path)
        self.engine = MonitorEngine(self.settings_manager, db=self.db)
        self.monitor_thread = None
        self._is_quitting = False
        self._live_data_dirty = {"stats": False, "listings": False}
        self._ui_refresh_request_count = 0

        self.setup_ui()
        self.setup_tray()
        self.setup_shortcuts()
        self._ui_refresh_timer = QTimer(self)
        self._ui_refresh_timer.setSingleShot(True)
        self._ui_refresh_timer.timeout.connect(self._flush_live_data_refresh)

        if self.settings_manager.settings.start_minimized:
            self.hide()
            self.tray_icon.show()

        # Check for auto backup on startup
        self.backup_manager = BackupManager()
        if self.settings_manager.settings.auto_backup_enabled:
            self._check_auto_backup()

        QTimer.singleShot(0, self._show_settings_recovery_notice)
        # Run startup maintenance (cleanup) once after UI is shown.
        QTimer.singleShot(0, self._run_startup_maintenance)
