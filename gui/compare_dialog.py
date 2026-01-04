# gui/compare_dialog.py
"""Dialog for comparing multiple listings side by side"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices


class CompareDialog(QDialog):
    """Dialog to compare selected listings side by side"""
    
    def __init__(self, listings: list, parent=None):
        super().__init__(parent)
        self.listings = listings
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("📊 매물 비교")
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)
        self.setStyleSheet("QDialog { background-color: #1e1e2e; }")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QHBoxLayout()
        title = QLabel(f"📊 매물 비교 ({len(self.listings)}개)")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #cdd6f4;")
        header.addWidget(title)
        header.addStretch()
        
        close_btn = QPushButton("✖ 닫기")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #585b70; }
        """)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)
        
        # Comparison table (rows = attributes, columns = items)
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.listings))
        self.table.setRowCount(6)  # Platform, Title, Price, Seller, Location, Link
        
        # Row headers
        row_labels = ["플랫폼", "제목", "가격", "판매자", "지역", "링크"]
        self.table.setVerticalHeaderLabels(row_labels)
        
        # Column headers (item numbers)
        col_labels = [f"매물 {i+1}" for i in range(len(self.listings))]
        self.table.setHorizontalHeaderLabels(col_labels)
        
        # Fill data
        for col, item in enumerate(self.listings):
            platform_icons = {
                'danggeun': '🥕 당근마켓',
                'bunjang': '⚡ 번개장터',
                'joonggonara': '🛒 중고나라'
            }
            
            self.table.setItem(0, col, QTableWidgetItem(
                platform_icons.get(item.get('platform', ''), item.get('platform', ''))
            ))
            self.table.setItem(1, col, QTableWidgetItem(item.get('title', '')))
            self.table.setItem(2, col, QTableWidgetItem(item.get('price', '')))
            self.table.setItem(3, col, QTableWidgetItem(item.get('seller', '-')))
            self.table.setItem(4, col, QTableWidgetItem(item.get('location', '-')))
            
            link_item = QTableWidgetItem("🔗 열기")
            link_item.setData(Qt.ItemDataRole.UserRole, item.get('url', ''))
            self.table.setItem(5, col, link_item)
        
        # Style
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(45)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e2e;
                gridline-color: #45475a;
                border: none;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 8px;
                color: #cdd6f4;
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
        self.table.cellDoubleClicked.connect(self._on_cell_clicked)
        
        layout.addWidget(self.table)
        
        # Price comparison highlight
        self._highlight_best_price()
    
    def _highlight_best_price(self):
        """Highlight the lowest price in green"""
        prices = []
        for col in range(len(self.listings)):
            item = self.listings[col]
            price_num = item.get('price_numeric', 0)
            if price_num and price_num > 0:
                prices.append((col, price_num))
        
        if prices:
            min_col = min(prices, key=lambda x: x[1])[0]
            price_item = self.table.item(2, min_col)
            if price_item:
                price_item.setBackground(Qt.GlobalColor.darkGreen)
                price_item.setText(price_item.text() + " ⭐ 최저가")
    
    def _on_cell_clicked(self, row, col):
        """Open link when link row is clicked"""
        if row == 5:  # Link row
            item = self.table.item(row, col)
            if item:
                url = item.data(Qt.ItemDataRole.UserRole)
                if url:
                    QDesktopServices.openUrl(QUrl(url))
