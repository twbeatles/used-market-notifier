"""Mixin module: shortcuts."""

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


class ListingsShortcutsMixin:
    """Shortcuts behavior."""

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for listing interactions"""
        # Enter: Open selected item link
        shortcut_open = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        shortcut_open.activated.connect(self._open_selected)

        # Ctrl+F: Focus search box (common convention)
        shortcut_find = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_find.activated.connect(self._focus_search)

        # F: Add to favorites
        shortcut_fav = QShortcut(QKeySequence(Qt.Key.Key_F), self)
        shortcut_fav.activated.connect(self._add_selected_to_favorites)


    def _focus_search(self):
        try:
            self.search_input.setFocus()
            self.search_input.selectAll()
        except Exception:
            pass


    def _open_selected(self):
        """Open currently selected item"""
        row = self.table.currentRow()
        if row >= 0:
            self.on_row_double_click(row, 0)


    def _add_selected_to_favorites(self):
        """Add currently selected item to favorites"""
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item:
                listing_id = item.data(Qt.ItemDataRole.UserRole + 1)
                db = self.engine.db if self.engine else self._standalone_db
                if listing_id and db:
                    if db.add_favorite(listing_id):
                        QMessageBox.information(self, "성공", "즐겨찾기에 추가되었습니다.")
                    else:
                        QMessageBox.warning(self, "알림", "이미 즐겨찾기에 등록된 상품입니다.")
