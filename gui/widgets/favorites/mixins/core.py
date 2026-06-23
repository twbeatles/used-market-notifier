"""Mixin module: core."""

# gui/favorites_widget.py
"""Favorites management widget"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QMessageBox, QMenu, QDialog,
    QFormLayout, QLineEdit, QSpinBox, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QFont
from db import DatabaseManager
from ....link_utils import open_external_url

class FavoritesCoreMixin:
    """Core behavior."""

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.db = engine.db
        self.setup_ui()


    def set_engine(self, engine):
        """Set or update the monitor engine (and DB reference)."""
        self.engine = engine
        self.db = engine.db if engine else None
        self.refresh_list()


    def refresh_list(self):
        if self.db is None:
            self.table.setRowCount(0)
            self.table.hide()
            self.empty_state.show()
            return
        favorites = self.db.get_favorites()
        self.table.setRowCount(len(favorites))

        # Show/hide empty state
        if not favorites:
            self.table.hide()
            self.empty_state.show()
        else:
            self.empty_state.hide()
            self.table.show()

        for row, item in enumerate(favorites):
            # Platform
            self.table.setItem(row, 0, QTableWidgetItem(item['platform']))

            # Title
            title_item = QTableWidgetItem(item['title'])
            title_item.setData(Qt.ItemDataRole.UserRole, item['url'])
            title_item.setData(Qt.ItemDataRole.UserRole + 1, item['listing_id'])
            self.table.setItem(row, 1, title_item)

            # Price
            price_item = QTableWidgetItem(item['price'])
            if item.get('target_price') and item.get('price_numeric'):
                if item['price_numeric'] <= item['target_price']:
                     price_item.setForeground(QColor("#a6e3a1")) # Green if reached target
            self.table.setItem(row, 2, price_item)

            # Target Price
            tp = item.get('target_price')
            tp_text = f"{tp:,}원" if tp else "-"
            self.table.setItem(row, 3, QTableWidgetItem(tp_text))

            # Notes
            self.table.setItem(row, 4, QTableWidgetItem(item.get('notes', '')))

            # Added At
            date_str = item.get('fav_added_at', '')[:16]
            self.table.setItem(row, 5, QTableWidgetItem(date_str))
