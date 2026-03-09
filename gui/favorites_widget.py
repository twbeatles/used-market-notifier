# gui/favorites_widget.py
"""Favorites management widget"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QMessageBox, QMenu, QDialog, 
    QFormLayout, QLineEdit, QSpinBox, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QAction, QColor, QFont
from db import DatabaseManager

class FavoritesEditDialog(QDialog):
    """Dialog to edit favorite notes and target price"""
    def __init__(self, notes: str, target_price: int | None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("즐겨찾기 수정")
        self.setFixedWidth(300)
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.target_price_spin = QSpinBox()
        self.target_price_spin.setRange(0, 1000000000)
        self.target_price_spin.setSingleStep(1000)
        self.target_price_spin.setSpecialValueText("설정 안함")
        self.target_price_spin.setValue(target_price if target_price else 0)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("메모를 입력하세요...")
        self.notes_edit.setText(notes)
        self.notes_edit.setMaximumHeight(100)
        
        form_layout.addRow("목표 가격:", self.target_price_spin)
        form_layout.addRow("메모:", self.notes_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        # Style
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; }
            QLabel { color: #cdd6f4; }
            QLineEdit, QSpinBox, QTextEdit { 
                background-color: #313244; 
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #b4befe; }
        """)

    def get_data(self):
        tp = self.target_price_spin.value()
        return {
            'target_price': tp if tp > 0 else None,
            'notes': self.notes_edit.toPlainText()
        }


class FavoritesWidget(QWidget):
    """Widget to display and manage favorites"""
    
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.db = engine.db
        self.setup_ui()

    def set_engine(self, engine):
        """Set or update the monitor engine (and DB reference)."""
        self.engine = engine
        self.db = engine.db if engine else None
        self.refresh_list()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("⭐ 즐겨찾기")
        title.setObjectName("title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self.refresh_list)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["플랫폼", "제목", "가격", "목표가", "메모", "등록일"])
        h_header = self.table.horizontalHeader()
        if h_header is not None:
            h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Table style
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        v_header = self.table.verticalHeader()
        if v_header is not None:
            v_header.setVisible(False)
        self.table.setSortingEnabled(True)  # Enable column sorting
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
        
        # Empty state placeholder
        from gui.loading_spinner import EmptyStateWidget
        self.empty_state = EmptyStateWidget(
            icon="⭐",
            title="즐겨찾기가 비어있습니다",
            message="관심있는 매물을 즐겨찾기에 추가해보세요.\n매물 목록에서 우클릭 → '즐겨찾기 추가'",
            parent=self
        )
        self.empty_state.hide()
        layout.addWidget(self.empty_state)
        
        # Context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.cellDoubleClicked.connect(self.on_double_click)
        
        self.refresh_list()
        
    def refresh_list(self):
        if self.db is None:
            self.table.setRowCount(0)
            self.table.hide()
            self.empty_state.show()
            return
        favorites = self.db.get_favorites()
        self.table.setRowCount(len(favorites))
        
        # Show/hide empty state
        if not favorites:
            self.table.hide()
            self.empty_state.show()
        else:
            self.empty_state.hide()
            self.table.show()
        
        for row, item in enumerate(favorites):
            # Platform
            self.table.setItem(row, 0, QTableWidgetItem(item['platform']))
            
            # Title
            title_item = QTableWidgetItem(item['title'])
            title_item.setData(Qt.ItemDataRole.UserRole, item['url'])
            title_item.setData(Qt.ItemDataRole.UserRole + 1, item['listing_id'])
            self.table.setItem(row, 1, title_item)
            
            # Price
            price_item = QTableWidgetItem(item['price'])
            if item.get('target_price') and item.get('price_numeric'):
                if item['price_numeric'] <= item['target_price']:
                     price_item.setForeground(QColor("#a6e3a1")) # Green if reached target
            self.table.setItem(row, 2, price_item)
            
            # Target Price
            tp = item.get('target_price')
            tp_text = f"{tp:,}원" if tp else "-"
            self.table.setItem(row, 3, QTableWidgetItem(tp_text))
            
            # Notes
            self.table.setItem(row, 4, QTableWidgetItem(item.get('notes', '')))
            
            # Added At
            date_str = item.get('fav_added_at', '')[:16]
            self.table.setItem(row, 5, QTableWidgetItem(date_str))
            
    def open_link(self, row):
        item = self.table.item(row, 1)
        if item:
            url = item.data(Qt.ItemDataRole.UserRole)
            
            # Check confirmation setting
            if hasattr(self.engine, 'settings') and self.engine.settings.settings.confirm_link_open:
                confirm = QMessageBox.question(
                    self, "링크 열기",
                    f"다음 상품 페이지로 이동하시겠습니까?\n{item.text()}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if confirm != QMessageBox.StandardButton.Yes:
                    return
                    
            if url is not None:
                QDesktopServices.openUrl(QUrl(str(url)))
            
    def on_double_click(self, row, col):
        if col == 1: # Title -> Open Link
            self.open_link(row)
        else: # Edit
            self.edit_favorite(row)
            
    def show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
            
        menu = QMenu(self)
        open_action = menu.addAction("🔗 링크 열기")
        edit_action = menu.addAction("✏️ 수정 (메모/목표가)")
        delete_action = menu.addAction("🗑️ 삭제")
        
        viewport = self.table.viewport()
        if viewport is None:
            return
        action = menu.exec(viewport.mapToGlobal(pos))
        
        if action == open_action:
            self.open_link(row)
        elif action == edit_action:
            self.edit_favorite(row)
        elif action == delete_action:
            self.delete_favorite(row)
            
    def edit_favorite(self, row):
        title_item = self.table.item(row, 1)
        if title_item is None:
            return
        listing_id = title_item.data(Qt.ItemDataRole.UserRole + 1)
        if listing_id is None:
            return
        
        # Get current values
        tp_item = self.table.item(row, 3)
        notes_item = self.table.item(row, 4)
        tp_text = tp_item.text().replace("원", "").replace(",", "").replace("-", "") if tp_item else ""
        target_price = int(tp_text) if tp_text else None
        notes = notes_item.text() if notes_item else ""
        
        dialog = FavoritesEditDialog(notes, target_price, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if self.db is not None:
                self.db.update_favorite(int(listing_id), data['notes'], data['target_price'])
                self.refresh_list()
            
    def delete_favorite(self, row):
        title_item = self.table.item(row, 1)
        if title_item is None:
            return
        listing_id = title_item.data(Qt.ItemDataRole.UserRole + 1)
        if listing_id is None:
            return
        title = title_item.text()
        
        confirm = QMessageBox.question(
            self, "삭제 확인", 
            f"'{title}'을(를) 즐겨찾기에서 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            if self.db is not None:
                self.db.remove_favorite(int(listing_id))
                self.refresh_list()
