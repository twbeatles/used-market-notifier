"""Mixin module: filters."""

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


class ListingsFiltersMixin:
    """Filters behavior."""

    def on_search_changed(self, text):
        self.search_text = text
        self.current_page = 0
        # Use debounce to avoid excessive API calls
        self.search_timer.stop()
        self.search_timer.start(300)  # Wait 300ms after last keystroke


    def _do_search(self):
        """Actually perform the search after debounce"""
        self.refresh_listings(force=True)


    def on_platform_changed(self, text):
        platform_map = {
            "전체": "all",
            "당근마켓": "danggeun",
            "번개장터": "bunjang",
            "중고나라": "joonggonara"
        }
        self.current_platform = platform_map.get(text, "all")
        self.current_page = 0
        self.refresh_listings(force=True)


    def on_status_changed(self, text):
        """Handle status filter change"""
        status_map = {
            "전체": "all",
            "판매중": "for_sale",
            "예약중": "reserved",
            "판매완료": "sold"
        }
        self.current_status = status_map.get(text, "all")
        self.current_page = 0
        self.refresh_listings(force=True)
