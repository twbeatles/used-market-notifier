"""Mixin module: core."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFileDialog,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
)

from export_manager import ExportManager
from models import Item

from ....charts import DailyChart, PlatformChart
from ....components import StatCard
from ....link_utils import open_external_url


class StatsCoreMixin:
    """Core behavior."""

    def __init__(self, engine=None, parent=None):
        super().__init__(parent)
        self.engine = engine
        self._standalone_db = None
        self._pending_refresh = False
        self._last_platform_signature = None
        self._last_daily_signature = None
        self._last_recent_signature = None
        self._last_changes_signature = None
        self._last_analysis_signature = None
        self._last_status_signature = None
        self.setup_ui()

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._on_refresh_timer)
        self.refresh_timer.start(30000)
        QTimer.singleShot(100, self._load_initial_stats)


    def _load_initial_stats(self):
        """Load stats from DB even if engine isn't running."""
        if self.engine:
            return
        try:
            from db import DatabaseManager
            from settings_manager import SettingsManager

            settings = SettingsManager()
            self._standalone_db = DatabaseManager(settings.settings.db_path)
            self.refresh_stats(force=True)
        except Exception as e:
            print(f"Could not load initial stats: {e}")


    def set_engine(self, engine):
        """Set or update the monitor engine."""
        self.engine = engine
        self._standalone_db = None
        self.refresh_stats(force=True)


    def _on_refresh_timer(self):
        if not self.isVisible():
            self._pending_refresh = True
            return
        self.refresh_stats()


    def _get_active_db(self):
        if self.engine and hasattr(self.engine, "db"):
            return self.engine.db
        return self._standalone_db


    def showEvent(self, a0):
        super().showEvent(a0)
        if self._pending_refresh:
            self.refresh_stats(force=True)


    def closeEvent(self, a0):
        if hasattr(self, "refresh_timer"):
            self.refresh_timer.stop()
        if self._standalone_db:
            try:
                self._standalone_db.close()
                self._standalone_db = None
            except Exception:
                pass
        super().closeEvent(a0)
