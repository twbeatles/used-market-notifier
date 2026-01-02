# gui/listings_widget.py
"""All listings browser widget - Shows all scraped items"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QLineEdit, QMessageBox, QMenu, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices


class ListingsWidget(QWidget):
    """Widget to browse all scraped listings"""
    
    def __init__(self, engine=None, parent=None):
        super().__init__(parent)
        self.engine = engine
        self._standalone_db = None  # For accessing DB without engine running
        self.current_page = 0
        self.page_size = 50
        self.total_count = 0
        self.current_platform = "all"
        self.search_text = ""
        self.exclude_sold = True  # Default: exclude sold items
        
        self.setup_ui()
        
        # Auto refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_listings)
        self.refresh_timer.start(60000)  # Refresh every minute
        
        # Search debounce timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._do_search)
        
        # Try to load existing data on startup
        QTimer.singleShot(200, self._load_initial_listings)
    
    def _load_initial_listings(self):
        """Load listings from DB even if engine isn't running"""
        if not self.engine:
            try:
                from db import DatabaseManager
                from settings_manager import SettingsManager
                settings = SettingsManager()
                self._standalone_db = DatabaseManager(settings.settings.db_path)
                self.refresh_listings()
            except Exception as e:
                print(f"Could not load initial listings: {e}")
    
    def set_engine(self, engine):
        """Set or update the monitor engine"""
        self.engine = engine
        self._standalone_db = None  # Use engine's DB instead
        self.refresh_listings()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📋 전체 매물 목록")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #cdd6f4;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 제목 검색...")
        self.search_input.setMinimumWidth(200)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 8px 12px;
                color: #cdd6f4;
            }
            QLineEdit:focus {
                border: 1px solid #89b4fa;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_changed)
        header_layout.addWidget(self.search_input)
        
        # Platform filter
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["전체", "당근마켓", "번개장터", "중고나라"])
        self.platform_combo.setStyleSheet("""
            QComboBox {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 8px 12px;
                color: #cdd6f4;
                min-width: 100px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
        """)
        self.platform_combo.currentTextChanged.connect(self.on_platform_changed)
        header_layout.addWidget(self.platform_combo)
        
        # Exclude sold checkbox
        self.exclude_sold_check = QCheckBox("판매완료 제외")
        self.exclude_sold_check.setChecked(True)
        self.exclude_sold_check.setStyleSheet("""
            QCheckBox {
                color: #cdd6f4;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #45475a;
                border-radius: 4px;
                background-color: #313244;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #a6e3a1;
                border-radius: 4px;
                background-color: #a6e3a1;
            }
        """)
        self.exclude_sold_check.stateChanged.connect(self.on_exclude_sold_changed)
        header_layout.addWidget(self.exclude_sold_check)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_listings)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["플랫폼", "제목", "가격", "키워드", "등록일", "링크"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 60)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self.on_row_double_click)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
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
                color: #cdd6f4;
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
        layout.addWidget(self.table, 1)
        
        # Pagination
        pagination_layout = QHBoxLayout()
        
        self.count_label = QLabel("총 0개")
        self.count_label.setStyleSheet("color: #6c7086;")
        pagination_layout.addWidget(self.count_label)
        
        pagination_layout.addStretch()
        
        self.prev_btn = QPushButton("◀ 이전")
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
            QPushButton:disabled {
                color: #6c7086;
            }
        """)
        self.prev_btn.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_btn)
        
        self.page_label = QLabel("1 / 1")
        self.page_label.setStyleSheet("color: #cdd6f4; padding: 0 16px;")
        pagination_layout.addWidget(self.page_label)
        
        self.next_btn = QPushButton("다음 ▶")
        self.next_btn.setStyleSheet(self.prev_btn.styleSheet())
        self.next_btn.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_btn)
        
        layout.addLayout(pagination_layout)
    
    def on_search_changed(self, text):
        self.search_text = text
        self.current_page = 0
        # Use debounce to avoid excessive API calls
        self.search_timer.stop()
        self.search_timer.start(300)  # Wait 300ms after last keystroke
    
    def _do_search(self):
        """Actually perform the search after debounce"""
        self.refresh_listings()
    
    def on_platform_changed(self, text):
        platform_map = {
            "전체": "all",
            "당근마켓": "danggeun",
            "번개장터": "bunjang",
            "중고나라": "joonggonara"
        }
        self.current_platform = platform_map.get(text, "all")
        self.current_page = 0
        self.refresh_listings()
    
    def on_exclude_sold_changed(self, state):
        """Handle exclude sold checkbox change"""
        self.exclude_sold = state == 2  # Qt.CheckState.Checked
        self.current_page = 0
        self.refresh_listings()
    
    def refresh_listings(self):
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
            listings = db.get_listings_paginated(
                platform=platform,
                search=self.search_text,
                limit=self.page_size * 2 if self.exclude_sold else self.page_size,  # Fetch more if filtering
                offset=offset
            )
            
            # Apply sold filter client-side
            if self.exclude_sold:
                sold_patterns = ["판매완료", "거래완료", "예약중"]
                listings = [
                    item for item in listings
                    if not any(p in (item.get('title', '') or '') for p in sold_patterns)
                ][:self.page_size]  # Limit to page size after filtering
            
            # Get total count (approximate when filtering)
            self.total_count = db.get_listings_count(
                platform=platform,
                search=self.search_text
            )
            
            # Update table
            self.table.setRowCount(len(listings))
            for i, item in enumerate(listings):
                # Platform
                platform_item = QTableWidgetItem(item.get('platform', ''))
                platform_item.setData(Qt.ItemDataRole.UserRole, item.get('url'))
                platform_item.setData(Qt.ItemDataRole.UserRole + 1, item.get('id'))
                self.table.setItem(i, 0, platform_item)
                
                # Title
                self.table.setItem(i, 1, QTableWidgetItem(item.get('title', '')))
                
                # Price
                self.table.setItem(i, 2, QTableWidgetItem(item.get('price', '')))
                
                # Keyword
                self.table.setItem(i, 3, QTableWidgetItem(item.get('keyword', '')))
                
                # Date
                created = item.get('created_at', '')
                if created:
                    created = created[:16].replace('T', ' ')
                self.table.setItem(i, 4, QTableWidgetItem(created))
                
                # Link button
                link_item = QTableWidgetItem("🔗")
                link_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, 5, link_item)
            
            # Update pagination
            total_pages = max(1, (self.total_count + self.page_size - 1) // self.page_size)
            self.page_label.setText(f"{self.current_page + 1} / {total_pages}")
            self.count_label.setText(f"총 {self.total_count:,}개")
            
            self.prev_btn.setEnabled(self.current_page > 0)
            self.next_btn.setEnabled(self.current_page < total_pages - 1)
            
        except Exception as e:
            print(f"Error refreshing listings: {e}")
    
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_listings()
    
    def next_page(self):
        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.refresh_listings()
    
    def on_row_double_click(self, row, col):
        item = self.table.item(row, 0)
        if item:
            url = item.data(Qt.ItemDataRole.UserRole)
            if url:
                QDesktopServices.openUrl(QUrl(url))
    
    def show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        
        menu = QMenu(self)
        open_action = menu.addAction("🔗 링크 열기")
        fav_action = menu.addAction("⭐ 즐겨찾기 추가")
        
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        
        if action == open_action:
            self.on_row_double_click(row, 0)
        elif action == fav_action:
            item = self.table.item(row, 0)
            if item:
                listing_id = item.data(Qt.ItemDataRole.UserRole + 1)
                if listing_id and self.engine:
                    if self.engine.db.add_favorite(listing_id):
                        QMessageBox.information(self, "성공", "즐겨찾기에 추가되었습니다.")
                    else:
                        QMessageBox.warning(self, "알림", "이미 즐겨찾기에 등록된 상품입니다.")
