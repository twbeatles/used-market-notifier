# gui/notification_history.py
"""Notification history widget"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QComboBox, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QColor
from db import DatabaseManager

class NotificationHistoryWidget(QWidget):
    """Widget to display notification history"""
    
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.db = engine.db
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📢 알림 히스토리")
        title.setObjectName("title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Filter
        self.type_filter = QComboBox()
        self.type_filter.addItem("전체 알림", "all")
        self.type_filter.addItem("Telegram", "telegram")
        self.type_filter.addItem("Discord", "discord")
        self.type_filter.addItem("Slack", "slack")
        self.type_filter.currentTextChanged.connect(self.refresh_list)
        header_layout.addWidget(self.type_filter)
        
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self.refresh_list)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["시간", "플랫폼", "유형", "제목", "미리보기"])
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 300)
        
        # Table style
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
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
            }
        """)
        
        layout.addWidget(self.table)
        
        self.table.cellDoubleClicked.connect(self.on_double_click)
        
        self.refresh_list()
        
    def refresh_list(self):
        logs = self.db.get_notification_logs(limit=100)
        
        # Filter
        filter_type = self.type_filter.currentData()
        if filter_type != "all":
            logs = [l for l in logs if l['notification_type'] == filter_type]
        
        self.table.setRowCount(len(logs))
        
        for row, item in enumerate(logs):
            # Time
            self.table.setItem(row, 0, QTableWidgetItem(item['sent_at']))
            
            # Platform
            self.table.setItem(row, 1, QTableWidgetItem(item.get('platform', '')))
            
            # Type
            type_item = QTableWidgetItem(item['notification_type'].capitalize())
            if item['notification_type'] == 'telegram':
                type_item.setForeground(QColor("#58a6ff")) # Blue
            elif item['notification_type'] == 'discord':
                type_item.setForeground(QColor("#7289da")) # Purple-ish
            elif item['notification_type'] == 'slack':
                type_item.setForeground(QColor("#e01e5a")) # Red-ish
            self.table.setItem(row, 2, type_item)
            
            # Title
            title_item = QTableWidgetItem(item.get('title', ''))
            title_item.setData(Qt.ItemDataRole.UserRole, item.get('url'))
            self.table.setItem(row, 3, title_item)
            
            # Preview (Message)
            self.table.setItem(row, 4, QTableWidgetItem(item.get('message_preview', '')))

            
    def on_double_click(self, row, col):
        title_item = self.table.item(row, 3)
        if title_item:
            url = title_item.data(Qt.ItemDataRole.UserRole)
            if url:
                # Confirm
                if hasattr(self.engine, 'settings') and self.engine.settings.settings.confirm_link_open:
                     confirm = QMessageBox.question(
                         self, "링크 열기",
                         f"다음 링크로 이동하시겠습니까?\n{url}",
                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                     )
                     if confirm != QMessageBox.StandardButton.Yes:
                         return
                
                QDesktopServices.openUrl(QUrl(url))
