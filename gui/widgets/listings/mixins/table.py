"""Mixin module: table."""

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


class ListingsTableMixin:
    """Table behavior."""

    def _make_table_signature(self, listings: list[dict], platform: Optional[str], status: Optional[str], offset: int):
        return (
            platform,
            status,
            self.search_text,
            self.current_page,
            self.page_size,
            self.total_count,
            offset,
            tuple(
                (
                    row.get("id"),
                    row.get("platform"),
                    row.get("article_id"),
                    row.get("title"),
                    row.get("price"),
                    row.get("keyword"),
                    row.get("created_at"),
                    row.get("sale_status"),
                )
                for row in listings
            ),
        )


    def refresh_listings(self, force: bool = False):
        # Get DB from engine or standalone
        db = None
        if self.engine and hasattr(self.engine, 'db'):
            db = self.engine.db
        elif self._standalone_db:
            db = self._standalone_db

        if not db:
            return

        try:
            # Get listings from database with filters
            offset = self.current_page * self.page_size

            platform = None if self.current_platform == "all" else self.current_platform
            status = None if self.current_status == "all" else self.current_status

            # Use new DB method with status filter
            listings = db.get_listings_by_status(
                status=status,
                platform=platform,
                search=self.search_text,
                limit=self.page_size,
                offset=offset
            )

            # Get total count (approximate when filtering)
            self.total_count = db.get_listings_count(
                platform=platform,
                search=self.search_text,
                status=status,
            )

            signature = self._make_table_signature(listings, platform, status, offset)
            if not force and signature == self._last_table_signature:
                total_pages = max(1, (self.total_count + self.page_size - 1) // self.page_size)
                self.page_label.setText(f"{self.current_page + 1} / {total_pages}")
                self.count_label.setText(f"총 {self.total_count:,}개")
                self.prev_btn.setEnabled(self.current_page > 0)
                self.next_btn.setEnabled(self.current_page < total_pages - 1)
                return

            # Update table
            self.table.setRowCount(len(listings))
            for i, item in enumerate(listings):
                # Platform - colorful icon display
                platform = item.get('platform', '')
                platform_icons = {
                    'danggeun': '🥕 당근',
                    'bunjang': '⚡ 번개',
                    'joonggonara': '🛒 중고'
                }
                platform_item = QTableWidgetItem(platform_icons.get(platform, platform))
                platform_item.setData(Qt.ItemDataRole.UserRole, item)  # Store full item data
                platform_item.setData(Qt.ItemDataRole.UserRole + 1, item.get('id'))
                self.table.setItem(i, 0, platform_item)

                # Title with truncation hint
                title = item.get('title', '')
                title_item = QTableWidgetItem(title[:60] + '...' if len(title) > 60 else title)
                title_item.setToolTip(title)  # Full title on hover
                self.table.setItem(i, 1, title_item)

                # Price with formatting
                price = item.get('price', '')
                price_item = QTableWidgetItem(price)
                self.table.setItem(i, 2, price_item)

                # Keyword
                self.table.setItem(i, 3, QTableWidgetItem(item.get('keyword', '')))

                # Date - formatted nicely
                created = item.get('created_at', '')
                if created:
                    created = created[:16].replace('T', ' ')
                self.table.setItem(i, 4, QTableWidgetItem(created))

                # Link button with better visibility
                link_item = QTableWidgetItem("🔗 열기")
                link_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, 5, link_item)

            # Update pagination
            total_pages = max(1, (self.total_count + self.page_size - 1) // self.page_size)
            self.page_label.setText(f"{self.current_page + 1} / {total_pages}")
            self.count_label.setText(f"총 {self.total_count:,}개")

            self.prev_btn.setEnabled(self.current_page > 0)
            self.next_btn.setEnabled(self.current_page < total_pages - 1)
            self._last_table_signature = signature
            self._pending_refresh = False

        except Exception as e:
            print(f"Error refreshing listings: {e}")


    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_listings(force=True)


    def next_page(self):
        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.refresh_listings(force=True)
