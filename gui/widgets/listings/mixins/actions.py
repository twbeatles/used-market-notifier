"""Mixin module: actions."""

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


class ListingsActionsMixin:
    """Actions behavior."""

    def on_row_double_click(self, row, col):
        item = self.table.item(row, 0)
        if not item:
            return

        payload = item.data(Qt.ItemDataRole.UserRole)
        url = None
        if isinstance(payload, dict):
            url = payload.get("url") or payload.get("link")
        elif isinstance(payload, str):
            url = payload

        if url:
            open_external_url(self, self.engine, url, item.text())


    def show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        menu = QMenu(self)
        open_action = menu.addAction("🔗 링크 열기")
        fav_action = menu.addAction("⭐ 즐겨찾기 추가")
        note_action = menu.addAction("📝 메모 추가/편집")
        message_action = menu.addAction("📨 판매자에게 메시지")

        viewport = self.table.viewport()
        if viewport is None:
            return
        action = menu.exec(viewport.mapToGlobal(pos))

        if action == open_action:
            self.on_row_double_click(row, 0)
        elif action == fav_action:
            item = self.table.item(row, 0)
            if item:
                listing_id = item.data(Qt.ItemDataRole.UserRole + 1)
                db = self.engine.db if self.engine else self._standalone_db
                if listing_id and db:
                    if db.add_favorite(listing_id):
                        QMessageBox.information(self, "성공", "즐겨찾기에 추가되었습니다.")
                    else:
                        QMessageBox.warning(self, "알림", "이미 즐겨찾기에 등록된 상품입니다.")
        elif action == note_action:
            item = self.table.item(row, 0)
            if item:
                listing_id = item.data(Qt.ItemDataRole.UserRole + 1)
                db = self.engine.db if self.engine else self._standalone_db
                if listing_id and db:
                    self._show_note_dialog(listing_id, db)
        elif action == message_action:
            self._show_message_dialog(row)


    def _show_note_dialog(self, listing_id: int, db):
        """Show note edit dialog for a listing"""
        from gui.note_dialog import NoteDialog

        # Get existing note
        existing = db.get_listing_note(listing_id)
        note = existing.get('note', '') if existing else ''
        status_tag = existing.get('status_tag', 'interested') if existing else 'interested'

        dialog = NoteDialog(note, status_tag, self)
        if dialog.exec():
            new_note = dialog.get_note()
            new_tag = dialog.get_status_tag()
            db.add_listing_note(listing_id, new_note, new_tag)
            QMessageBox.information(self, "성공", "메모가 저장되었습니다.")


    def _compare_selected(self):
        """Open compare dialog with selected listings"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())

        if len(selected_rows) < 2:
            QMessageBox.information(self, "알림", "비교할 매물을 2개 이상 선택하세요.\n(Ctrl+클릭으로 다중 선택)")
            return

        if len(selected_rows) > 5:
            QMessageBox.warning(self, "알림", "최대 5개까지만 비교할 수 있습니다.")
            return

        # Collect listing data
        listings = []
        for row in sorted(selected_rows):
            item = self.table.item(row, 0)
            if item:
                listing_data = item.data(Qt.ItemDataRole.UserRole)
                if listing_data:
                    listings.append(listing_data)

        if listings:
            from gui.compare_dialog import CompareDialog
            dialog = CompareDialog(listings, self)
            dialog.exec()


    def _show_export_dialog(self):
        """Show export dialog with current filters"""
        db = self.engine.db if self.engine else self._standalone_db
        if not db:
            QMessageBox.warning(self, "알림", "데이터베이스에 연결되지 않았습니다.")
            return

        from gui.export_dialog import ExportDialog

        # Pass current filters to the dialog
        current_filters = {
            'platform': None if self.current_platform == "all" else self.current_platform,
            'status': None if self.current_status == "all" else self.current_status,
            'search': self.search_text,
            'include_sold': self.current_status != "sold"
        }

        dialog = ExportDialog(db, current_filters, self)
        dialog.exec()


    def _show_message_dialog(self, row: int):
        """Show message dialog for a listing"""
        item = self.table.item(row, 0)
        if not item:
            return

        db = self.engine.db if self.engine else self._standalone_db
        if not db:
            return

        listing_id = item.data(Qt.ItemDataRole.UserRole + 1)
        if not listing_id:
            return

        # Get full listing data from database
        listing = db.get_listing_by_id(listing_id) if hasattr(db, 'get_listing_by_id') else None

        if not listing:
            # Fallback: construct from table data
            payload = item.data(Qt.ItemDataRole.UserRole) if item else None
            fallback_url = ""
            if isinstance(payload, dict):
                fallback_url = payload.get("url") or payload.get("link") or ""
            elif isinstance(payload, str):
                fallback_url = payload
            platform_item = self.table.item(row, 0)
            title_item = self.table.item(row, 1)
            price_item = self.table.item(row, 2)
            listing = {
                'platform': platform_item.text() if platform_item else '',
                'title': title_item.text() if title_item else '',
                'price': price_item.text() if price_item else '',
                'url': fallback_url,
                'seller': '',
                'location': ''
            }

        from gui.message_dialog import MessageDialog
        from settings_manager import SettingsManager

        # Get target price from favorites if available
        target_price = None
        if db.is_favorite(listing_id):
            fav_details = db.get_favorite_details(listing_id)
            if fav_details:
                target_price_raw = fav_details.get('target_price')
                target_price = target_price_raw if isinstance(target_price_raw, int) else None

        # Load custom message templates from settings (if available)
        custom_templates = None
        try:
            if self.engine and hasattr(self.engine, "settings"):
                custom_templates = getattr(self.engine.settings.settings, "message_templates", None)
            if custom_templates is None:
                custom_templates = SettingsManager().settings.message_templates
        except Exception:
            custom_templates = None

        dialog = MessageDialog(listing, target_price, custom_templates=custom_templates, parent=self)
        dialog.exec()
