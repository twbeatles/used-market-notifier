"""Enhanced statistics dashboard."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices
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

from .charts import DailyChart, PlatformChart
from .components import StatCard


class StatsWidget(QWidget):
    """Statistics dashboard with recent listings, price changes, and status history."""

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

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            """
        )

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title = QLabel("통계 대시보드")
        title.setObjectName("title")
        header_layout.addWidget(title)
        header_layout.addStretch()

        export_btn = QPushButton("내보내기")
        export_btn.setObjectName("secondary")
        export_btn.clicked.connect(self.show_export_menu)
        header_layout.addWidget(export_btn)

        refresh_btn = QPushButton("새로고침")
        refresh_btn.setObjectName("secondary")
        refresh_btn.clicked.connect(lambda: self.refresh_stats(force=True))
        header_layout.addWidget(refresh_btn)
        layout.addLayout(header_layout)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        self.total_card = StatCard("전체 상품", "0", "건", "#7aa2f7")
        self.danggeun_card = StatCard("당근마켓", "0", "건", "#ff9e64")
        self.bunjang_card = StatCard("번개장터", "0", "건", "#bb9af7")
        self.joonggonara_card = StatCard("중고나라", "0", "건", "#9ece6a")
        cards_layout.addWidget(self.total_card)
        cards_layout.addWidget(self.danggeun_card)
        cards_layout.addWidget(self.bunjang_card)
        cards_layout.addWidget(self.joonggonara_card)
        layout.addLayout(cards_layout)

        charts_tabs = QTabWidget()
        charts_tabs.setMinimumHeight(220)
        charts_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        platform_widget = QWidget()
        platform_layout = QVBoxLayout(platform_widget)
        platform_layout.setContentsMargins(12, 12, 12, 12)
        self.platform_chart = PlatformChart()
        self.platform_chart.setMinimumHeight(180)
        platform_layout.addWidget(self.platform_chart)
        charts_tabs.addTab(platform_widget, "플랫폼 분포")

        daily_widget = QWidget()
        daily_layout = QVBoxLayout(daily_widget)
        daily_layout.setContentsMargins(12, 12, 12, 12)
        self.daily_chart = DailyChart()
        self.daily_chart.setMinimumHeight(180)
        daily_layout.addWidget(self.daily_chart)
        charts_tabs.addTab(daily_widget, "최근 7일 추이")
        layout.addWidget(charts_tabs)

        tables_tabs = QTabWidget()
        tables_tabs.setMinimumHeight(300)
        tables_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.recent_table = self._create_table(["플랫폼", "제목", "가격", "키워드", "시간"], stretch_col=1)
        self.recent_table.setColumnWidth(0, 90)
        self.recent_table.setColumnWidth(2, 120)
        self.recent_table.setColumnWidth(3, 140)
        self.recent_table.setColumnWidth(4, 80)
        self.recent_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.recent_table.customContextMenuRequested.connect(self.show_context_menu)
        self.recent_table.cellDoubleClicked.connect(self.on_table_double_click)
        tables_tabs.addTab(self._table_tab(self.recent_table), "최근 발견 상품")

        self.price_table = self._create_table(["상품", "이전 가격", "현재 가격", "시간"], stretch_col=0)
        self.price_table.setColumnWidth(1, 120)
        self.price_table.setColumnWidth(2, 120)
        self.price_table.setColumnWidth(3, 120)
        self.price_table.cellDoubleClicked.connect(self.on_table_double_click)
        tables_tabs.addTab(self._table_tab(self.price_table), "가격 변동")

        self.analysis_table = self._create_table(["키워드", "매물 수", "최저가", "평균가", "최고가"], stretch_col=0)
        self.analysis_table.setColumnWidth(1, 80)
        self.analysis_table.setColumnWidth(2, 120)
        self.analysis_table.setColumnWidth(3, 120)
        self.analysis_table.setColumnWidth(4, 120)
        tables_tabs.addTab(self._table_tab(self.analysis_table), "키워드 시세")

        self.status_history_table = self._create_table(
            ["플랫폼", "제목", "이전 상태", "현재 상태", "시간"],
            stretch_col=1,
        )
        self.status_history_table.setColumnWidth(0, 90)
        self.status_history_table.setColumnWidth(2, 110)
        self.status_history_table.setColumnWidth(3, 110)
        self.status_history_table.setColumnWidth(4, 150)
        self.status_history_table.cellDoubleClicked.connect(self.on_table_double_click)
        tables_tabs.addTab(self._table_tab(self.status_history_table), "판매 상태 변경")

        layout.addWidget(tables_tabs, 1)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def _create_table(self, headers: list[str], stretch_col: int) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        h_header = table.horizontalHeader()
        if h_header is not None:
            h_header.setSectionResizeMode(stretch_col, QHeaderView.ResizeMode.Stretch)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        v_header = table.verticalHeader()
        if v_header is not None:
            v_header.setVisible(False)
        table.setStyleSheet(
            """
            QTableWidget {
                background-color: #1e1e2e;
                alternate-background-color: #313244;
                gridline-color: #45475a;
                border: none;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:hover {
                background-color: #45475a;
            }
            QTableWidget::item:selected {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
            QHeaderView::section {
                background-color: #181825;
                color: #a6adc8;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #45475a;
                font-weight: bold;
            }
            """
        )
        return table

    def _table_tab(self, table: QTableWidget) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.addWidget(table)
        return widget

    def _signature_recent(self, recent: list[dict]):
        return tuple(
            (item.get("id"), item.get("platform"), item.get("title"), item.get("price"), item.get("keyword"))
            for item in recent
        )

    def _signature_changes(self, changes: list[dict]):
        return tuple(
            (
                row.get("platform"),
                row.get("article_id"),
                row.get("title"),
                row.get("old_price"),
                row.get("new_price"),
                row.get("changed_at"),
            )
            for row in changes
        )

    def _signature_analysis(self, analysis: list[dict]):
        return tuple(
            (
                row.get("keyword"),
                row.get("count"),
                row.get("min_price"),
                row.get("avg_price"),
                row.get("max_price"),
            )
            for row in analysis
        )

    def _signature_status_history(self, history: list[dict]):
        return tuple(
            (
                row.get("platform"),
                row.get("title"),
                row.get("old_status"),
                row.get("new_status"),
                row.get("changed_at"),
            )
            for row in history
        )

    def refresh_stats(self, force: bool = False):
        """Refresh statistics."""
        db = None
        if self.engine and hasattr(self.engine, "db"):
            db = self.engine.db
        elif self._standalone_db:
            db = self._standalone_db
        if not db:
            return

        try:
            snap = db.get_dashboard_snapshot(
                recent_limit=20,
                price_change_limit=20,
                price_change_days=20,
                daily_days=7,
            )
            total = snap["total"]
            by_platform = snap["by_platform"]
            recent = snap["recent"]
            changes = snap["price_changes"]
            analysis = snap["analysis"]
            daily_stats = snap["daily_stats"]
            status_history = snap.get("status_history", [])

            self.total_card.set_value(str(total))
            self.danggeun_card.set_value(str(by_platform.get("danggeun", 0)))
            self.bunjang_card.set_value(str(by_platform.get("bunjang", 0)))
            self.joonggonara_card.set_value(str(by_platform.get("joonggonara", 0)))

            recent_sig = self._signature_recent(recent)
            if force or recent_sig != self._last_recent_signature:
                self.recent_table.setRowCount(len(recent))
                for row_index, item in enumerate(recent):
                    platform_item = QTableWidgetItem(item.get("platform", ""))
                    platform_item.setData(Qt.ItemDataRole.UserRole, item.get("url"))
                    platform_item.setData(Qt.ItemDataRole.UserRole + 1, item.get("id"))
                    platform_item.setData(Qt.ItemDataRole.UserRole + 2, item.get("seller"))
                    platform_item.setData(Qt.ItemDataRole.UserRole + 3, item.get("platform"))
                    self.recent_table.setItem(row_index, 0, platform_item)
                    self.recent_table.setItem(row_index, 1, QTableWidgetItem(item.get("title", "")))
                    self.recent_table.setItem(row_index, 2, QTableWidgetItem(item.get("price", "")))
                    self.recent_table.setItem(row_index, 3, QTableWidgetItem(item.get("keyword", "")))
                    created = item.get("created_at", "")
                    self.recent_table.setItem(
                        row_index,
                        4,
                        QTableWidgetItem(created[11:16] if len(created) > 16 else created),
                    )
                self._last_recent_signature = recent_sig

            changes_sig = self._signature_changes(changes)
            if force or changes_sig != self._last_changes_signature:
                self.price_table.setRowCount(len(changes))
                for row_index, change in enumerate(changes):
                    title_item = QTableWidgetItem(change.get("title", "")[:40])
                    title_item.setData(Qt.ItemDataRole.UserRole, change.get("url"))
                    self.price_table.setItem(row_index, 0, title_item)
                    self.price_table.setItem(row_index, 1, QTableWidgetItem(str(change.get("old_price", ""))))
                    self.price_table.setItem(row_index, 2, QTableWidgetItem(str(change.get("new_price", ""))))
                    changed_at = change.get("changed_at", "")
                    self.price_table.setItem(
                        row_index,
                        3,
                        QTableWidgetItem(changed_at[11:16] if len(changed_at) > 16 else changed_at),
                    )
                self._last_changes_signature = changes_sig

            analysis_sig = self._signature_analysis(analysis)
            if force or analysis_sig != self._last_analysis_signature:
                self.analysis_table.setRowCount(len(analysis))
                for row_index, row in enumerate(analysis):
                    self.analysis_table.setItem(row_index, 0, QTableWidgetItem(row.get("keyword", "")))
                    self.analysis_table.setItem(row_index, 1, QTableWidgetItem(str(row.get("count", 0))))
                    min_p = row.get("min_price", 0)
                    avg_p = row.get("avg_price", 0)
                    max_p = row.get("max_price", 0)
                    self.analysis_table.setItem(
                        row_index,
                        2,
                        QTableWidgetItem(f"{min_p:,}원" if min_p else "-"),
                    )
                    self.analysis_table.setItem(
                        row_index,
                        3,
                        QTableWidgetItem(f"{avg_p:,}원" if avg_p else "-"),
                    )
                    self.analysis_table.setItem(
                        row_index,
                        4,
                        QTableWidgetItem(f"{max_p:,}원" if max_p else "-"),
                    )
                self._last_analysis_signature = analysis_sig

            status_sig = self._signature_status_history(status_history)
            if force or status_sig != self._last_status_signature:
                self.status_history_table.setRowCount(len(status_history))
                for row_index, row in enumerate(status_history):
                    platform_item = QTableWidgetItem(row.get("platform", ""))
                    platform_item.setData(Qt.ItemDataRole.UserRole, row.get("url"))
                    self.status_history_table.setItem(row_index, 0, platform_item)
                    self.status_history_table.setItem(row_index, 1, QTableWidgetItem(row.get("title", "")))
                    self.status_history_table.setItem(
                        row_index, 2, QTableWidgetItem(str(row.get("old_status", "")))
                    )
                    self.status_history_table.setItem(
                        row_index, 3, QTableWidgetItem(str(row.get("new_status", "")))
                    )
                    self.status_history_table.setItem(
                        row_index, 4, QTableWidgetItem(row.get("changed_at", ""))
                    )
                self._last_status_signature = status_sig

            platform_sig = tuple(sorted(by_platform.items()))
            daily_sig = tuple((row.get("date"), row.get("items_found"), row.get("new_items")) for row in daily_stats)
            if force or platform_sig != self._last_platform_signature:
                self.platform_chart.update_chart(by_platform)
                self._last_platform_signature = platform_sig
            if force or daily_sig != self._last_daily_signature:
                self.daily_chart.update_chart(daily_stats)
                self._last_daily_signature = daily_sig
            self._pending_refresh = False
        except Exception as e:
            print(f"Error refreshing stats: {e}")
            import traceback

            traceback.print_exc()

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
        if self.engine and hasattr(self.engine, "settings") and self.engine.settings.settings.confirm_link_open:
            confirm = QMessageBox.question(
                self,
                "링크 열기",
                f"다음 링크로 이동할까요?\n{url}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
        QDesktopServices.openUrl(QUrl(url))

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

    def _get_active_db(self):
        if self.engine and hasattr(self.engine, "db"):
            return self.engine.db
        return self._standalone_db

    @staticmethod
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
