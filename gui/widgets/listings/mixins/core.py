"""Mixin module: core."""

# gui/listings_widget.py
"""All listings browser widget - Shows all scraped items"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QLineEdit, QMessageBox, QMenu, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence
from typing import Optional

from ....link_utils import open_external_url


class ListingsCoreMixin:
    """Core behavior."""

    def __init__(self, engine=None, parent=None):
        super().__init__(parent)
        self.engine = engine
        self._standalone_db = None  # For accessing DB without engine running
        self.current_page = 0
        self.page_size = 50
        self.total_count = 0
        self.current_platform = "all"
        self.search_text = ""
        self.current_status = "all"  # Status filter: all, for_sale, reserved, sold
        self._pending_refresh = False
        self._last_table_signature = None

        self.setup_ui()

        # Auto refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._on_refresh_timer)
        self.refresh_timer.start(60000)  # Refresh every minute

        # Search debounce timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._do_search)

        # Try to load existing data on startup
        QTimer.singleShot(200, self._load_initial_listings)

        # Setup keyboard shortcuts
        self._setup_shortcuts()


    def _load_initial_listings(self):
        """Load listings from DB even if engine isn't running"""
        if not self.engine:
            try:
                from db import DatabaseManager
                from settings_manager import SettingsManager
                settings = SettingsManager()
                self._standalone_db = DatabaseManager(settings.settings.db_path)
                self.refresh_listings(force=True)
            except Exception as e:
                print(f"Could not load initial listings: {e}")


    def set_engine(self, engine):
        """Set or update the monitor engine"""
        self.engine = engine
        self._standalone_db = None  # Use engine's DB instead
        self.refresh_listings(force=True)


    def _on_refresh_timer(self):
        if not self.isVisible():
            self._pending_refresh = True
            return
        self.refresh_listings()


    def showEvent(self, a0):
        super().showEvent(a0)
        if self._pending_refresh:
            self.refresh_listings(force=True)


    def closeEvent(self, a0):
        """Clean up resources on close"""
        # Stop refresh timer
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()

        # Close standalone database connection to prevent memory leak
        if self._standalone_db:
            try:
                self._standalone_db.close()
                self._standalone_db = None
            except Exception:
                pass

        super().closeEvent(a0)
