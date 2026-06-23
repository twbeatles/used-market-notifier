"""Mixin module: actions."""

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


class StatsActionsMixin:
    """Actions behavior."""

    def on_table_double_click(self, row, col):
        _ = col
        sender = self.sender()
        url = None
        if sender is self.recent_table:
            item = self.recent_table.item(row, 0)
            url = item.data(Qt.ItemDataRole.UserRole) if item else None
        elif sender is self.price_table:
            item = self.price_table.item(row, 0)
            url = item.data(Qt.ItemDataRole.UserRole) if item else None
        elif sender is self.status_history_table:
            item = self.status_history_table.item(row, 0)
            url = item.data(Qt.ItemDataRole.UserRole) if item else None

        if url:
            self.open_url(url)


    def open_url(self, url):
        open_external_url(self, self.engine, url)


    def show_context_menu(self, pos):
        row = self.recent_table.rowAt(pos.y())
        if row < 0:
            return

        menu = QMenu(self)
        fav_action = menu.addAction("즐겨찾기에 추가")
        block_action = menu.addAction("판매자 차단")

        viewport = self.recent_table.viewport()
        if viewport is None:
            return
        action = menu.exec(viewport.mapToGlobal(pos))
        if action == fav_action:
            self.add_to_favorites(row)
        elif action == block_action:
            self.block_seller(row)


    def _listing_to_item(listing: dict) -> Item:
        return Item(
            platform=str(listing.get("platform", "")),
            article_id=str(listing.get("article_id", "")),
            title=str(listing.get("title", "")),
            price=str(listing.get("price", "")),
            link=str(listing.get("url", "")),
            keyword=str(listing.get("keyword", "")),
            thumbnail=listing.get("thumbnail"),
            seller=listing.get("seller"),
            location=listing.get("location"),
            price_numeric=listing.get("price_numeric"),
        )


    def block_seller(self, row):
        """Block the seller of the selected item."""
        item = self.recent_table.item(row, 0)
        if item is None:
            return

        db = self._get_active_db()
        if db is None:
            QMessageBox.warning(self, "실패", "데이터베이스 연결을 찾지 못했습니다.")
            return

        listing_id = item.data(Qt.ItemDataRole.UserRole + 1)
        seller = item.data(Qt.ItemDataRole.UserRole + 2)
        platform = item.data(Qt.ItemDataRole.UserRole + 3)
        listing = db.get_listing_by_id(int(listing_id)) if listing_id else None

        enrichment_enabled = bool(
            self.engine
            and hasattr(self.engine, "settings")
            and getattr(self.engine.settings.settings, "metadata_enrichment_enabled", False)
        )
        if not seller and enrichment_enabled and listing and self.engine:
            try:
                enriched = self.engine.enrich_item_metadata_once(self._listing_to_item(listing), platform=platform)
                if enriched.seller or enriched.location:
                    db.add_listing(enriched)
                    listing = db.get_listing_by_id(int(listing_id)) if listing_id else listing
                    seller = (listing or {}).get("seller") or enriched.seller
                    self.refresh_stats(force=True)
            except Exception as e:
                QMessageBox.warning(self, "보강 실패", f"seller/location 보강 중 오류가 발생했습니다.\n{e}")
                return

        if not seller:
            QMessageBox.warning(
                self,
                "판매자 정보 없음",
                "이 항목에는 판매자 정보가 없어 차단할 수 없습니다.\n"
                "설정에서 seller/location 보강 수집을 켜면 가능한 플랫폼에서는 상세 페이지에서 한 번 더 시도합니다.",
            )
            return

        confirm = QMessageBox.question(
            self,
            "판매자 차단",
            f"판매자 '{seller}' ({platform})를 차단할까요?\n이후 이 판매자의 상품은 알림에서 제외됩니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes and self.engine:
            self.engine.db.add_seller_filter(seller, platform, is_blocked=True)
            QMessageBox.information(self, "완료", "판매자를 차단했습니다.")


    def add_to_favorites(self, row):
        item = self.recent_table.item(row, 0)
        if not item:
            return

        listing_id = item.data(Qt.ItemDataRole.UserRole + 1)
        if listing_id and self.engine:
            if self.engine.db.add_favorite(listing_id):
                QMessageBox.information(self, "성공", "즐겨찾기에 추가했습니다.")
            else:
                QMessageBox.warning(self, "알림", "이미 즐겨찾기에 등록된 상품입니다.")


    def show_export_menu(self):
        btn = self.sender()
        if not isinstance(btn, QWidget):
            return
        menu = QMenu(self)
        csv_action = menu.addAction("CSV로 내보내기 (최근 100개)")
        excel_action = menu.addAction("Excel로 내보내기 (최근 100개)")

        action = menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
        if action == csv_action:
            self.export_data("csv")
        elif action == excel_action:
            self.export_data("excel")


    def export_data(self, format_type):
        filter_str = "CSV Files (*.csv)" if format_type == "csv" else "Excel Files (*.xlsx)"
        filename, _ = QFileDialog.getSaveFileName(self, "파일 저장", "", filter_str)
        if not filename:
            return

        db = self._get_active_db()
        if not db:
            QMessageBox.warning(self, "오류", "데이터베이스 연결이 없습니다.")
            return

        data = db.get_recent_listings(limit=100)
        fields = ["platform", "title", "price", "keyword", "url", "created_at"]
        if format_type == "csv":
            success, message = ExportManager.export_to_csv(data, filename, fields)
        else:
            success, message = ExportManager.export_to_excel(data, filename, fields)

        if success:
            QMessageBox.information(self, "완료", message)
        else:
            QMessageBox.critical(self, "실패", f"내보내기에 실패했습니다: {message}")
