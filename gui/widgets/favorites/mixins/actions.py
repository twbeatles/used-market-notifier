"""Mixin module: actions."""

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

class FavoritesActionsMixin:
    """Actions behavior."""

    def open_link(self, row):
        item = self.table.item(row, 1)
        if item:
            url = item.data(Qt.ItemDataRole.UserRole)
            open_external_url(self, self.engine, url, item.text())


    def on_double_click(self, row, col):
        if col == 1: # Title -> Open Link
            self.open_link(row)
        else: # Edit
            self.edit_favorite(row)


    def show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        menu = QMenu(self)
        open_action = menu.addAction("🔗 링크 열기")
        edit_action = menu.addAction("✏️ 수정 (메모/목표가)")
        delete_action = menu.addAction("🗑️ 삭제")

        viewport = self.table.viewport()
        if viewport is None:
            return
        action = menu.exec(viewport.mapToGlobal(pos))

        if action == open_action:
            self.open_link(row)
        elif action == edit_action:
            self.edit_favorite(row)
        elif action == delete_action:
            self.delete_favorite(row)


    def edit_favorite(self, row):
        title_item = self.table.item(row, 1)
        if title_item is None:
            return
        listing_id = title_item.data(Qt.ItemDataRole.UserRole + 1)
        if listing_id is None:
            return

        # Get current values
        tp_item = self.table.item(row, 3)
        notes_item = self.table.item(row, 4)
        tp_text = tp_item.text().replace("원", "").replace(",", "").replace("-", "") if tp_item else ""
        target_price = int(tp_text) if tp_text else None
        notes = notes_item.text() if notes_item else ""

        dialog = FavoritesEditDialog(notes, target_price, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if self.db is not None:
                self.db.update_favorite(int(listing_id), data['notes'], data['target_price'])
                self.refresh_list()


    def delete_favorite(self, row):
        title_item = self.table.item(row, 1)
        if title_item is None:
            return
        listing_id = title_item.data(Qt.ItemDataRole.UserRole + 1)
        if listing_id is None:
            return
        title = title_item.text()

        confirm = QMessageBox.question(
            self, "삭제 확인",
            f"'{title}'을(를) 즐겨찾기에서 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            if self.db is not None:
                self.db.remove_favorite(int(listing_id))
                self.refresh_list()
