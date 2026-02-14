# gui/stats_widget.py
"""Enhanced statistics dashboard with modern card design"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QGridLayout, QScrollArea, QFrame, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QSizePolicy, QMenu, QMessageBox,
    QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QColor, QFont, QAction, QDesktopServices
from export_manager import ExportManager

from .components import StatCard
from .charts import PlatformChart, DailyChart


class StatsWidget(QWidget):
    """Modern statistics dashboard"""
    
    def __init__(self, engine=None, parent=None):
        super().__init__(parent)
        self.engine = engine
        self._standalone_db = None  # For accessing DB without engine running
        self.setup_ui()
        
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_stats)
        self.refresh_timer.start(30000)
        
        # Try to load existing data on startup
        QTimer.singleShot(100, self._load_initial_stats)
    
    def _load_initial_stats(self):
        """Load stats from DB even if engine isn't running"""
        if not self.engine:
            try:
                from db import DatabaseManager
                from settings_manager import SettingsManager
                settings = SettingsManager()
                self._standalone_db = DatabaseManager(settings.settings.db_path)
                self.refresh_stats()
            except Exception as e:
                print(f"Could not load initial stats: {e}")
    
    def set_engine(self, engine):
        """Set or update the monitor engine"""
        self.engine = engine
        self._standalone_db = None  # Use engine's DB instead
        self.refresh_stats()
    
    def setup_ui(self):
        # Main layout for this widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create scroll area for the content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)
        
        # Content widget inside scroll area
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📊 통계 대시보드")
        title.setObjectName("title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        export_btn = QPushButton("💾 내보내기")
        export_btn.setObjectName("secondary")
        export_btn.setToolTip("통계 데이터를 CSV 또는 Excel로 저장")
        export_btn.clicked.connect(self.show_export_menu)
        header_layout.addWidget(export_btn)
        
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.setObjectName("secondary")
        refresh_btn.setToolTip("통계 데이터를 새로 불러옵니다")
        refresh_btn.clicked.connect(self.refresh_stats)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Stat cards row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        
        self.total_card = StatCard("전체 상품", "0", "📦", "#7aa2f7")
        cards_layout.addWidget(self.total_card)
        
        self.danggeun_card = StatCard("당근마켓", "0", "🥕", "#ff9e64")
        cards_layout.addWidget(self.danggeun_card)
        
        self.bunjang_card = StatCard("번개장터", "0", "⚡", "#bb9af7")
        cards_layout.addWidget(self.bunjang_card)
        
        self.joonggonara_card = StatCard("중고나라", "0", "🛒", "#9ece6a")
        cards_layout.addWidget(self.joonggonara_card)
        
        layout.addLayout(cards_layout)
        
        # Charts section - using tabs for better visibility
        from PyQt6.QtWidgets import QTabWidget
        
        charts_tabs = QTabWidget()
        charts_tabs.setMinimumHeight(220)
        charts_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Platform pie chart
        platform_widget = QWidget()
        platform_layout = QVBoxLayout(platform_widget)
        platform_layout.setContentsMargins(12, 12, 12, 12)
        self.platform_chart = PlatformChart()
        self.platform_chart.setMinimumHeight(180)
        platform_layout.addWidget(self.platform_chart)
        charts_tabs.addTab(platform_widget, "📊 플랫폼별 분포")
        
        # Daily chart
        daily_widget = QWidget()
        daily_layout = QVBoxLayout(daily_widget)
        daily_layout.setContentsMargins(12, 12, 12, 12)
        self.daily_chart = DailyChart()
        self.daily_chart.setMinimumHeight(180)
        daily_layout.addWidget(self.daily_chart)
        charts_tabs.addTab(daily_widget, "📈 일별 추이 (최근 7일)")
        
        layout.addWidget(charts_tabs)
        
        # Tables section - using tabs for better space utilization
        from PyQt6.QtWidgets import QTabWidget
        
        tables_tabs = QTabWidget()
        tables_tabs.setMinimumHeight(280)
        tables_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Recent items table
        recent_widget = QWidget()
        recent_layout = QVBoxLayout(recent_widget)
        recent_layout.setContentsMargins(8, 12, 8, 8)
        
        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(5)
        self.recent_table.setHorizontalHeaderLabels(["플랫폼", "제목", "가격", "키워드", "시간"])
        self.recent_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.recent_table.setColumnWidth(0, 80)
        self.recent_table.setColumnWidth(2, 100)
        self.recent_table.setColumnWidth(3, 100)
        self.recent_table.setColumnWidth(4, 60)
        self.recent_table.setAlternatingRowColors(True)
        self.recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.recent_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setMinimumHeight(220)
        self.recent_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.recent_table.setStyleSheet("""
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
        """)
        self.recent_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.recent_table.customContextMenuRequested.connect(self.show_context_menu)
        self.recent_table.cellDoubleClicked.connect(self.on_table_double_click)
        recent_layout.addWidget(self.recent_table)
        
        tables_tabs.addTab(recent_widget, "🆕 최근 발견된 상품")
        
        # Price changes table  
        price_widget = QWidget()
        price_layout = QVBoxLayout(price_widget)
        price_layout.setContentsMargins(8, 12, 8, 8)
        
        self.price_table = QTableWidget()
        self.price_table.setColumnCount(4)
        self.price_table.setHorizontalHeaderLabels(["상품", "이전가격", "현재가격", "시간"])
        self.price_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.price_table.setColumnWidth(1, 100)
        self.price_table.setColumnWidth(2, 100)
        self.price_table.setColumnWidth(3, 60)
        self.price_table.setAlternatingRowColors(True)
        self.price_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.price_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.price_table.verticalHeader().setVisible(False)
        self.price_table.setStyleSheet(self.recent_table.styleSheet())
        self.price_table.cellDoubleClicked.connect(self.on_table_double_click)
        
        price_layout.addWidget(self.price_table)
        tables_tabs.addTab(price_widget, "💰 가격 변동")
        
        # Keyword Price Analysis Table (New)
        analysis_widget = QWidget()
        analysis_layout = QVBoxLayout(analysis_widget)
        analysis_layout.setContentsMargins(8, 12, 8, 8)
        
        self.analysis_table = QTableWidget()
        self.analysis_table.setColumnCount(5)
        self.analysis_table.setHorizontalHeaderLabels(["키워드", "매물수", "최저가", "평균가", "최고가"])
        self.analysis_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.analysis_table.setColumnWidth(1, 60)
        self.analysis_table.setColumnWidth(2, 100)
        self.analysis_table.setColumnWidth(3, 100)
        self.analysis_table.setColumnWidth(4, 100)
        self.analysis_table.setAlternatingRowColors(True)
        self.analysis_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.analysis_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.analysis_table.verticalHeader().setVisible(False)
        self.analysis_table.setStyleSheet(self.recent_table.styleSheet())
        
        analysis_layout.addWidget(self.analysis_table)
        tables_tabs.addTab(analysis_widget, "📊 키워드 시세")
        
        layout.addWidget(tables_tabs, 1)  # stretch factor 1 to take remaining space
        
        # Complete scroll area setup
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def refresh_stats(self):
        """Refresh statistics"""
        # Get DB from engine or standalone
        db = None
        if self.engine and hasattr(self.engine, 'db'):
            db = self.engine.db
        elif self._standalone_db:
            db = self._standalone_db
        
        if not db:
            return
            
        try:
            # Get stats directly from DB
            total = db.get_total_listings()
            by_platform = db.get_listings_by_platform()
            
            # Update cards
            self.total_card.set_value(str(total))
            self.danggeun_card.set_value(str(by_platform.get('danggeun', 0)))
            self.bunjang_card.set_value(str(by_platform.get('bunjang', 0)))
            self.joonggonara_card.set_value(str(by_platform.get('joonggonara', 0)))
            
            # Update recent table
            recent = db.get_recent_listings(20)
            self.recent_table.setRowCount(len(recent))
            for i, item in enumerate(recent):
                platform_item = QTableWidgetItem(item.get('platform', ''))
                platform_item.setData(Qt.ItemDataRole.UserRole, item.get('url'))
                platform_item.setData(Qt.ItemDataRole.UserRole + 1, item.get('id'))
                platform_item.setData(Qt.ItemDataRole.UserRole + 2, item.get('seller'))
                platform_item.setData(Qt.ItemDataRole.UserRole + 3, item.get('platform'))
                self.recent_table.setItem(i, 0, platform_item)
                
                self.recent_table.setItem(i, 1, QTableWidgetItem(item.get('title', '')))
                self.recent_table.setItem(i, 2, QTableWidgetItem(item.get('price', '')))
                self.recent_table.setItem(i, 3, QTableWidgetItem(item.get('keyword', '')))
                created = item.get('created_at', '')
                self.recent_table.setItem(i, 4, QTableWidgetItem(created[11:16] if len(created) > 16 else ''))
            
            # Update price changes table
            changes = db.get_price_changes(20)
            self.price_table.setRowCount(len(changes))
            for i, change in enumerate(changes):
                title_item = QTableWidgetItem(change.get('title', '')[:30])
                title_item.setData(Qt.ItemDataRole.UserRole, change.get('url'))
                self.price_table.setItem(i, 0, title_item)
                
                self.price_table.setItem(i, 1, QTableWidgetItem(str(change.get('old_price', ''))))
                self.price_table.setItem(i, 2, QTableWidgetItem(str(change.get('new_price', ''))))
                changed_at = change.get('changed_at', '')
                self.price_table.setItem(i, 3, QTableWidgetItem(changed_at[11:16] if len(changed_at) > 16 else ''))

            # Update analysis table
            analysis = db.get_keyword_price_stats()
            self.analysis_table.setRowCount(len(analysis))
            for i, row in enumerate(analysis):
                self.analysis_table.setItem(i, 0, QTableWidgetItem(row.get('keyword', '')))
                self.analysis_table.setItem(i, 1, QTableWidgetItem(str(row.get('count', 0))))
                
                min_p = row.get('min_price', 0)
                avg_p = row.get('avg_price', 0)
                max_p = row.get('max_price', 0)
                
                self.analysis_table.setItem(i, 2, QTableWidgetItem(f"{min_p:,}원" if min_p else "-"))
                self.analysis_table.setItem(i, 3, QTableWidgetItem(f"{avg_p:,}원" if avg_p else "-"))
                self.analysis_table.setItem(i, 4, QTableWidgetItem(f"{max_p:,}원" if max_p else "-"))

            # Update charts
            self.platform_chart.update_chart(by_platform)
            daily_stats = db.get_daily_stats(7)
            self.daily_chart.update_chart(daily_stats)
                
        except Exception as e:
            print(f"Error refreshing stats: {e}")
            import traceback
            traceback.print_exc()

    def on_table_double_click(self, row, col):
        sender = self.sender()
        url = None
        if sender == self.recent_table:
             item = self.recent_table.item(row, 0)
             if item: url = item.data(Qt.ItemDataRole.UserRole)
        elif sender == self.price_table:
             item = self.price_table.item(row, 0)
             if item: url = item.data(Qt.ItemDataRole.UserRole)
             
        if url:
             self.open_url(url)

    def open_url(self, url):
        if hasattr(self.engine, 'settings') and self.engine.settings.settings.confirm_link_open:
                confirm = QMessageBox.question(
                    self, "링크 열기",
                    f"다음 링크로 이동하시겠습니까?\n{url}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if confirm != QMessageBox.StandardButton.Yes:
                    return
        QDesktopServices.openUrl(QUrl(url))

    def show_context_menu(self, pos):
        """Show context menu for recent items"""
        row = self.recent_table.rowAt(pos.y())
        if row < 0:
            return
            
        menu = QMenu(self)
        fav_action = menu.addAction("⭐ 즐겨찾기 추가")
        block_action = menu.addAction("🚫 판매자 차단")
        
        action = menu.exec(self.recent_table.viewport().mapToGlobal(pos))
        
        if action == fav_action:
            self.add_to_favorites(row)
        elif action == block_action:
            self.block_seller(row)

    def block_seller(self, row):
        """Block the seller of the selected item"""
        item = self.recent_table.item(row, 0)
        seller = item.data(Qt.ItemDataRole.UserRole + 2)
        platform = item.data(Qt.ItemDataRole.UserRole + 3)
        
        if not seller:
            QMessageBox.warning(self, "실패", "판매자 정보가 없습니다.")
            return
            
        confirm = QMessageBox.question(
            self, "판매자 차단",
            f"판매자 '{seller}' ({platform})을(를) 차단하시겠습니까?\n앞으로 이 판매자의 상품은 알림이 오지 않습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.engine.db.add_seller_filter(seller, platform, is_blocked=True)
            QMessageBox.information(self, "완료", "판매자가 차단되었습니다.")

    def add_to_favorites(self, row):
        """Add selected item to favorites"""
        item = self.recent_table.item(row, 0)
        if not item:
            return
            
        listing_id = item.data(Qt.ItemDataRole.UserRole + 1)
        if listing_id:
            if self.engine.db.add_favorite(listing_id):
                 QMessageBox.information(self, "성공", "즐겨찾기에 추가되었습니다.")
            else:
                 QMessageBox.warning(self, "알림", "이미 즐겨찾기에 등록된 상품입니다.")

    def show_export_menu(self):
        """Show export options menu"""
        btn = self.sender()
        menu = QMenu(self)
        csv_action = menu.addAction("CSV로 저장 (최근 100개)")
        excel_action = menu.addAction("Excel로 저장 (최근 100개)")
        
        action = menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
        
        if action == csv_action:
            self.export_data("csv")
        elif action == excel_action:
            self.export_data("excel")

    def export_data(self, format_type):
        """Export data to file"""
        filter_str = "CSV Files (*.csv)" if format_type == "csv" else "Excel Files (*.xlsx)"
        filename, _ = QFileDialog.getSaveFileName(self, "파일 저장", "", filter_str)
        
        if not filename:
            return
        
        # Get DB reference
        db = self.engine.db if self.engine else self._standalone_db
        if not db:
            QMessageBox.warning(self, "오류", "데이터베이스 연결이 없습니다.")
            return
            
        data = db.get_recent_listings(limit=100)
        fields = ['platform', 'title', 'price', 'keyword', 'url', 'created_at']
        
        if format_type == "csv":
            success, message = ExportManager.export_to_csv(data, filename, fields)
        else:
            success, message = ExportManager.export_to_excel(data, filename, fields)
            
        if success:
            QMessageBox.information(self, "완료", f"✅ {message}")
        else:
            QMessageBox.critical(self, "실패", f"저장 실패: {message}")
    
    def closeEvent(self, event):
        """Clean up resources on close"""
        # Stop refresh timer
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        
        # Close standalone database connection
        if self._standalone_db:
            try:
                self._standalone_db.close()
                self._standalone_db = None
            except Exception:
                pass
        
        super().closeEvent(event)
