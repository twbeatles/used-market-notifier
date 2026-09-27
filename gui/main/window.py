# gui/main_window.py
"""Fluent main window (MSFluentWindow + Navigation).

Canonical behaviors live in :mod:`gui.main.window_mixins` (one mixin per
responsibility). This module only composes them into ``MainWindow`` and
owns construction.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer

if TYPE_CHECKING:
    from qfluentwidgets import FluentWindow as MSFluentWindow
else:
    try:
        from qfluentwidgets import MSFluentWindow
    except ImportError:
        from qfluentwidgets import FluentWindow as MSFluentWindow

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
    UpdaterMixin,
)
from gui.qt_binding import (
    format_gui_qt_binding_error,
    inspect_gui_qt_bindings,
    is_pyside6_binding,
)
from monitor_engine import MonitorEngine
from settings_manager import SettingsManager

_binding_report = inspect_gui_qt_bindings(check_conflicting_dists=False)
if not _binding_report.ok or not is_pyside6_binding(_binding_report.fluent_binding or ""):
    raise ImportError(format_gui_qt_binding_error(_binding_report))


class MainWindow(  # pyright: ignore[reportIncompatibleMethodOverride]
    UiSetupMixin,
    TrayMixin,
    ShortcutsMixin,
    MaintenanceMixin,
    RecoveryMixin,
    LiveRefreshMixin,
    MonitoringMixin,
    ThemeMixin,
    UpdaterMixin,
    LifecycleMixin,
    MSFluentWindow,
):
    """Fluent main application window."""

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
        QTimer.singleShot(800, self._show_last_update_result)
        QTimer.singleShot(1500, self._start_auto_update_check_if_enabled)

