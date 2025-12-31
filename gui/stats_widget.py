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
import sys
sys.path.insert(0, '..')
from export_manager import ExportManager

from .components import StatCard
from .charts import PlatformChart, DailyChart


class StatsWidget(QWidget):
    """Modern statistics dashboard"""
    
    def __init__(self, engine=None, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setup_ui()
        
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_stats)
        self.refresh_timer.start(30000)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
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
        export_btn.clicked.connect(self.show_export_menu)
        header_layout.addWidget(export_btn)
        
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.setObjectName("secondary")
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
        
        # Charts row
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(16)
        
        # Platform pie chart
        platform_group = QGroupBox("플랫폼별 분포")
        platform_layout = QVBoxLayout(platform_group)
        platform_layout.setContentsMargins(12, 20, 12, 12)
        self.platform_chart = PlatformChart()
        platform_layout.addWidget(self.platform_chart)
        charts_layout.addWidget(platform_group, 1)
        
        # Daily chart
        daily_group = QGroupBox("일별 추이 (최근 7일)")
        daily_layout = QVBoxLayout(daily_group)
        daily_layout.setContentsMargins(12, 20, 12, 12)
        self.daily_chart = DailyChart()
        daily_layout.addWidget(self.daily_chart)
        charts_layout.addWidget(daily_group, 2)
        
        layout.addLayout(charts_layout)
        
        # Tables row
        tables_layout = QHBoxLayout()
        tables_layout.setSpacing(16)
        
        # Recent items table
        recent_group = QGroupBox("최근 발견된 상품")
        recent_layout = QVBoxLayout(recent_group)
        recent_layout.setContentsMargins(12, 20, 12, 12)
        
        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(5)
        self.recent_table.setHorizontalHeaderLabels(["플랫폼", "제목", "가격", "키워드", "시간"])
        self.recent_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.recent_table.setAlternatingRowColors(True)
        self.recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.recent_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setStyleSheet("""
            QTableWidget {
                background-color: #1f2335;
                alternate-background-color: #292e42;
                gridline-color: #3b4261;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:hover {
                background-color: #3b4261;
            }
            QTableWidget::item:selected {
                background-color: #7aa2f7;
                color: #1e1e2e;
            }
        """)
        self.recent_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.recent_table.customContextMenuRequested.connect(self.show_context_menu)
        self.recent_table.cellDoubleClicked.connect(self.on_table_double_click)
        recent_layout.addWidget(self.recent_table)
        
        tables_layout.addWidget(recent_group, 2)
        
        # Price changes table  
        price_group = QGroupBox("가격 변동")
        price_layout = QVBoxLayout(price_group)
        price_layout.setContentsMargins(12, 20, 12, 12)
        
        self.price_table = QTableWidget()
        self.price_table.setColumnCount(4)
        self.price_table.setHorizontalHeaderLabels(["상품", "이전가격", "현재가격", "시간"])
        self.price_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.price_table.setAlternatingRowColors(True)
        self.price_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.price_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.price_table.verticalHeader().setVisible(False)
        self.price_table.setStyleSheet(self.recent_table.styleSheet())
        self.price_table.cellDoubleClicked.connect(self.on_table_double_click)
        
        price_layout.addWidget(self.price_table)
        tables_layout.addWidget(price_group, 1)
        
        layout.addLayout(tables_layout)

    def refresh_stats(self):
        """Refresh statistics"""
        if not self.engine:
            return
            
        try:
            stats = self.engine.get_stats()
            
            # Update cards
            self.total_card.set_value(str(stats['total_listings']))
            counts = {x['platform']: x['count'] for x in stats.get('by_platform', [])}
            self.danggeun_card.set_value(str(counts.get('danggeun', 0)))
            self.bunjang_card.set_value(str(counts.get('bunjang', 0)))
            self.joonggonara_card.set_value(str(counts.get('joonggonara', 0)))
            
            # Update recent table
            recent = stats.get('recent_listings', [])
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
                self.recent_table.setItem(i, 4, QTableWidgetItem(item.get('created_at', '')[11:16]))
            
            # Update price changes table
            changes = stats.get('price_changes', [])
            self.price_table.setRowCount(len(changes))
            for i, change in enumerate(changes):
                title_item = QTableWidgetItem(change.get('title', '')[:30])
                title_item.setData(Qt.ItemDataRole.UserRole, change.get('url'))
                self.price_table.setItem(i, 0, title_item)
                
                self.price_table.setItem(i, 1, QTableWidgetItem(str(change.get('old_price', ''))))
                self.price_table.setItem(i, 2, QTableWidgetItem(str(change.get('new_price', ''))))
                self.price_table.setItem(i, 3, QTableWidgetItem(change.get('changed_at', '')[11:16]))

            # Update charts
            self.platform_chart.update_chart(counts)
            self.daily_chart.update_chart(stats.get('daily_stats', []))
                
        except Exception as e:
            print(f"Error refreshing stats: {e}")

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
            
        data = self.engine.db.get_recent_listings(limit=100)
        fields = ['platform', 'title', 'price', 'keyword', 'url', 'created_at']
        
        success = False
        if format_type == "csv":
            success = ExportManager.export_to_csv(data, filename, fields)
        else:
            success = ExportManager.export_to_excel(data, filename, fields)
            
        if success:
            QMessageBox.information(self, "완료", "저장되었습니다.")
        else:
            QMessageBox.critical(self, "실패", "저장에 실패했습니다. (openpyxl 설치 확인 필요)")
