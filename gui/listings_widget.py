# gui/listings_widget.py
"""All listings browser widget - Shows all scraped items"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QLineEdit, QMessageBox, QMenu, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices, QShortcut, QKeySequence


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
        self.current_status = "all"  # Status filter: all, for_sale, reserved, sold
        
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
        
        # Setup keyboard shortcuts
        self._setup_shortcuts()
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for listing interactions"""
        # Enter: Open selected item link
        shortcut_open = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        shortcut_open.activated.connect(self._open_selected)
        
        # F: Add to favorites
        shortcut_fav = QShortcut(QKeySequence(Qt.Key.Key_F), self)
        shortcut_fav.activated.connect(self._add_selected_to_favorites)
    
    def _open_selected(self):
        """Open currently selected item"""
        row = self.table.currentRow()
        if row >= 0:
            self.on_row_double_click(row, 0)
    
    def _add_selected_to_favorites(self):
        """Add currently selected item to favorites"""
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item:
                listing_id = item.data(Qt.ItemDataRole.UserRole + 1)
                db = self.engine.db if self.engine else self._standalone_db
                if listing_id and db:
                    if db.add_favorite(listing_id):
                        QMessageBox.information(self, "성공", "즐겨찾기에 추가되었습니다.")
                    else:
                        QMessageBox.warning(self, "알림", "이미 즐겨찾기에 등록된 상품입니다.")
    
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
        
        # Status filter dropdown (replaces exclude_sold checkbox)
        status_label = QLabel("상태:")
        status_label.setStyleSheet("color: #a6adc8;")
        header_layout.addWidget(status_label)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["전체", "판매중", "예약중", "판매완료"])
        self.status_combo.setStyleSheet("""
            QComboBox {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 8px 12px;
                color: #cdd6f4;
                min-width: 80px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow { image: none; border: none; }
        """)
        self.status_combo.currentTextChanged.connect(self.on_status_changed)
        header_layout.addWidget(self.status_combo)
        
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
        
        # Compare button
        compare_btn = QPushButton("📊 비교")
        compare_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)
        compare_btn.setToolTip("선택한 매물들을 비교합니다 (2-5개 선택)")
        compare_btn.clicked.connect(self._compare_selected)
        header_layout.addWidget(compare_btn)
        
        # Export button (Feature #16)
        export_btn = QPushButton("📥 내보내기")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #f9e2af;
                color: #1e1e2e;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #fab387;
            }
        """)
        export_btn.setToolTip("현재 필터가 적용된 매물을 CSV/Excel로 내보내기")
        export_btn.clicked.connect(self._show_export_dialog)
        header_layout.addWidget(export_btn)
        
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
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)  # Allow multi-select
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
                search=self.search_text
            )
            
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
        note_action = menu.addAction("📝 메모 추가/편집")
        message_action = menu.addAction("📨 판매자에게 메시지")
        
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        
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
            listing = {
                'platform': self.table.item(row, 0).text() if self.table.item(row, 0) else '',
                'title': self.table.item(row, 1).text() if self.table.item(row, 1) else '',
                'price': self.table.item(row, 2).text() if self.table.item(row, 2) else '',
                'url': item.data(Qt.ItemDataRole.UserRole),
                'seller': '',
                'location': ''
            }
        
        from gui.message_dialog import MessageDialog
        
        # Get target price from favorites if available
        target_price = None
        if db.is_favorite(listing_id):
            fav_details = db.get_favorite_details(listing_id)
            if fav_details:
                target_price = fav_details.get('target_price')
        
        dialog = MessageDialog(listing, target_price, parent=self)
        dialog.exec()
    
    def closeEvent(self, event):
        """Clean up resources on close"""
        # Stop refresh timer
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        
        # Close standalone database connection to prevent memory leak
        if self._standalone_db:
            try:
                self._standalone_db.close()
                self._standalone_db = None
            except Exception:
                pass
        
        super().closeEvent(event)

