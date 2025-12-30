# gui/keyword_manager.py
"""Enhanced keyword management widget with modern card-based design"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QDialog, QFormLayout, QLineEdit, QSpinBox, QComboBox,
    QCheckBox, QLabel, QGroupBox, QMessageBox, QTextEdit, QFrame,
    QScrollArea, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QFont
import sys
sys.path.insert(0, '..')
from models import SearchKeyword


class KeywordCard(QFrame):
    """Individual keyword card with modern design"""
    
    clicked = pyqtSignal(int)
    double_clicked = pyqtSignal(int)
    
    def __init__(self, index: int, keyword: SearchKeyword, parent=None):
        super().__init__(parent)
        self.index = index
        self.keyword = keyword
        self.selected = False
        self.setup_ui()
    
    def setup_ui(self):
        self.setObjectName("keywordCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Header row
        header = QHBoxLayout()
        
        # Status indicator
        status = "🟢" if self.keyword.enabled else "⏸️"
        status_label = QLabel(status)
        status_label.setStyleSheet("font-size: 14pt;")
        header.addWidget(status_label)
        
        # Keyword name
        name_label = QLabel(self.keyword.keyword)
        name_label.setStyleSheet("font-size: 13pt; font-weight: bold; color: #c0caf5;")
        header.addWidget(name_label)
        
        header.addStretch()
        
        # Platform badges
        for platform in self.keyword.platforms:
            badge = self.create_platform_badge(platform)
            header.addWidget(badge)
        
        layout.addLayout(header)
        
        # Details row
        details = QHBoxLayout()
        details.setSpacing(16)
        
        # Price range
        if self.keyword.min_price or self.keyword.max_price:
            min_str = f"{self.keyword.min_price:,}" if self.keyword.min_price else "0"
            max_str = f"{self.keyword.max_price:,}" if self.keyword.max_price else "∞"
            price_label = QLabel(f"💰 {min_str} ~ {max_str}원")
            price_label.setStyleSheet("color: #9ece6a; font-size: 9pt;")
            details.addWidget(price_label)
        
        # Location
        if self.keyword.location:
            loc_label = QLabel(f"📍 {self.keyword.location}")
            loc_label.setStyleSheet("color: #ff9e64; font-size: 9pt;")
            details.addWidget(loc_label)
        
        # Excludes
        if self.keyword.exclude_keywords:
            ex_label = QLabel(f"🚫 {len(self.keyword.exclude_keywords)}개 제외")
            ex_label.setStyleSheet("color: #f7768e; font-size: 9pt;")
            details.addWidget(ex_label)
        
        details.addStretch()
        layout.addLayout(details)
    
    def create_platform_badge(self, platform: str) -> QLabel:
        colors = {
            'danggeun': ('#ff9e64', '🥕'),
            'bunjang': ('#bb9af7', '⚡'),
            'joonggonara': ('#9ece6a', '🛒')
        }
        color, emoji = colors.get(platform, ('#7aa2f7', '📦'))
        
        badge = QLabel(emoji)
        badge.setStyleSheet(f"""
            background-color: {color}22;
            color: {color};
            padding: 4px 8px;
            border-radius: 10px;
            font-size: 12pt;
        """)
        return badge
    
    def update_style(self):
        if self.selected:
            self.setStyleSheet("""
                QFrame#keywordCard {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 rgba(122, 162, 247, 0.3), stop:1 rgba(187, 154, 247, 0.3));
                    border: 2px solid #7aa2f7;
                    border-radius: 12px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame#keywordCard {
                    background-color: #1f2335;
                    border: 2px solid #3b4261;
                    border-radius: 12px;
                }
                QFrame#keywordCard:hover {
                    border: 2px solid #565f89;
                    background-color: #292e42;
                }
            """)
    
    def set_selected(self, selected: bool):
        self.selected = selected
        self.update_style()
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.index)
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.index)
        super().mouseDoubleClickEvent(event)


class KeywordEditDialog(QDialog):
    """Modern dialog for editing keyword configuration"""
    
    def __init__(self, keyword: SearchKeyword = None, parent=None):
        super().__init__(parent)
        self.keyword = keyword or SearchKeyword(keyword="")
        self.setup_ui()
        self.load_keyword()
    
    def setup_ui(self):
        self.setWindowTitle("키워드 설정")
        self.setMinimumWidth(500)
        self.setStyleSheet("QDialog { background-color: #1a1b26; }")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title = QLabel("🔍 키워드 설정")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #7aa2f7;")
        layout.addWidget(title)
        
        # Keyword input group
        keyword_group = QGroupBox("기본 정보")
        keyword_layout = QFormLayout(keyword_group)
        keyword_layout.setSpacing(12)
        
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("예: 맥북 에어 M2")
        self.keyword_edit.setMinimumHeight(40)
        keyword_layout.addRow("검색어", self.keyword_edit)
        
        self.enabled_check = QCheckBox("활성화")
        self.enabled_check.setChecked(True)
        keyword_layout.addRow("", self.enabled_check)
        
        layout.addWidget(keyword_group)
        
        # Price filter group
        price_group = QGroupBox("💰 가격 필터")
        price_layout = QHBoxLayout(price_group)
        price_layout.setSpacing(12)
        
        self.min_price_spin = QSpinBox()
        self.min_price_spin.setRange(0, 100000000)
        self.min_price_spin.setSingleStep(10000)
        self.min_price_spin.setSpecialValueText("최소")
        self.min_price_spin.setSuffix(" 원")
        self.min_price_spin.setMinimumHeight(40)
        price_layout.addWidget(QLabel("최소"))
        price_layout.addWidget(self.min_price_spin)
        
        price_layout.addWidget(QLabel("~"))
        
        self.max_price_spin = QSpinBox()
        self.max_price_spin.setRange(0, 100000000)
        self.max_price_spin.setSingleStep(10000)
        self.max_price_spin.setSpecialValueText("최대")
        self.max_price_spin.setSuffix(" 원")
        self.max_price_spin.setMinimumHeight(40)
        price_layout.addWidget(QLabel("최대"))
        price_layout.addWidget(self.max_price_spin)
        
        layout.addWidget(price_group)
        
        # Location and exclude in a row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(16)
        
        # Location
        location_group = QGroupBox("📍 지역 (당근)")
        location_layout = QVBoxLayout(location_group)
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("예: 강남구")
        self.location_edit.setMinimumHeight(40)
        location_layout.addWidget(self.location_edit)
        filter_row.addWidget(location_group)
        
        # Exclude keywords
        exclude_group = QGroupBox("🚫 제외 키워드")
        exclude_layout = QVBoxLayout(exclude_group)
        self.exclude_edit = QTextEdit()
        self.exclude_edit.setMaximumHeight(80)
        self.exclude_edit.setPlaceholderText("케이스\n부품\n택포X")
        exclude_layout.addWidget(self.exclude_edit)
        filter_row.addWidget(exclude_group)
        
        layout.addLayout(filter_row)
        
        # Platform selection
        platform_group = QGroupBox("📦 검색 플랫폼")
        platform_layout = QHBoxLayout(platform_group)
        platform_layout.setSpacing(16)
        
        self.danggeun_check = QCheckBox("🥕 당근마켓")
        self.danggeun_check.setChecked(True)
        self.danggeun_check.setStyleSheet("font-size: 11pt;")
        platform_layout.addWidget(self.danggeun_check)
        
        self.bunjang_check = QCheckBox("⚡ 번개장터")
        self.bunjang_check.setChecked(True)
        self.bunjang_check.setStyleSheet("font-size: 11pt;")
        platform_layout.addWidget(self.bunjang_check)
        
        self.joonggonara_check = QCheckBox("🛒 중고나라")
        self.joonggonara_check.setChecked(True)
        self.joonggonara_check.setStyleSheet("font-size: 11pt;")
        platform_layout.addWidget(self.joonggonara_check)
        
        platform_layout.addStretch()
        layout.addWidget(platform_group)
        
        # Buttons
        layout.addStretch()
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        cancel_btn = QPushButton("취소")
        cancel_btn.setObjectName("secondary")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 저장")
        save_btn.setObjectName("success")
        save_btn.setMinimumWidth(100)
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def load_keyword(self):
        self.keyword_edit.setText(self.keyword.keyword)
        self.enabled_check.setChecked(self.keyword.enabled)
        
        if self.keyword.min_price:
            self.min_price_spin.setValue(self.keyword.min_price)
        if self.keyword.max_price:
            self.max_price_spin.setValue(self.keyword.max_price)
        
        self.location_edit.setText(self.keyword.location or "")
        self.exclude_edit.setPlainText("\n".join(self.keyword.exclude_keywords))
        
        self.danggeun_check.setChecked("danggeun" in self.keyword.platforms)
        self.bunjang_check.setChecked("bunjang" in self.keyword.platforms)
        self.joonggonara_check.setChecked("joonggonara" in self.keyword.platforms)
    
    def get_keyword(self) -> SearchKeyword:
        platforms = []
        if self.danggeun_check.isChecked():
            platforms.append("danggeun")
        if self.bunjang_check.isChecked():
            platforms.append("bunjang")
        if self.joonggonara_check.isChecked():
            platforms.append("joonggonara")
        
        exclude_text = self.exclude_edit.toPlainText().strip()
        exclude_keywords = [k.strip() for k in exclude_text.split("\n") if k.strip()]
        
        return SearchKeyword(
            keyword=self.keyword_edit.text().strip(),
            min_price=self.min_price_spin.value() if self.min_price_spin.value() > 0 else None,
            max_price=self.max_price_spin.value() if self.max_price_spin.value() > 0 else None,
            location=self.location_edit.text().strip() or None,
            exclude_keywords=exclude_keywords,
            platforms=platforms,
            enabled=self.enabled_check.isChecked()
        )


class KeywordManagerWidget(QWidget):
    """Modern card-based keyword manager"""
    
    keywords_changed = pyqtSignal()
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.selected_index = -1
        self.cards = []
        self.setup_ui()
        self.refresh_list()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🔍 검색 키워드")
        title.setObjectName("title")
        header_layout.addWidget(title)
        
        # Badge showing count
        self.count_badge = QLabel("0")
        self.count_badge.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7aa2f7, stop:1 #bb9af7);
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 11pt;
        """)
        header_layout.addWidget(self.count_badge)
        
        header_layout.addStretch()
        
        add_btn = QPushButton("+ 새 키워드")
        add_btn.setObjectName("success")
        add_btn.setMinimumWidth(120)
        add_btn.clicked.connect(self.add_keyword)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Subtitle
        subtitle = QLabel("모니터링할 검색어를 추가하고 필터를 설정하세요")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)
        
        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(12)
        self.cards_layout.setContentsMargins(0, 0, 8, 0)
        self.cards_layout.addStretch()
        
        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)
        
        edit_btn = QPushButton("✏️ 수정")
        edit_btn.setObjectName("secondary")
        edit_btn.clicked.connect(self.edit_keyword)
        action_layout.addWidget(edit_btn)
        
        toggle_btn = QPushButton("⏯️ 활성화 토글")
        toggle_btn.setObjectName("secondary")
        toggle_btn.clicked.connect(self.toggle_keyword)
        action_layout.addWidget(toggle_btn)
        
        delete_btn = QPushButton("🗑️ 삭제")
        delete_btn.setObjectName("danger")
        delete_btn.clicked.connect(self.delete_keyword)
        action_layout.addWidget(delete_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
    
    def refresh_list(self):
        # Clear existing cards
        for card in self.cards:
            card.deleteLater()
        self.cards.clear()
        
        # Remove stretch
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Create new cards
        keywords = self.settings.settings.keywords
        for i, kw in enumerate(keywords):
            card = KeywordCard(i, kw)
            card.clicked.connect(self.on_card_clicked)
            card.double_clicked.connect(self.on_card_double_clicked)
            self.cards.append(card)
            self.cards_layout.addWidget(card)
        
        # Add empty state if no keywords
        if not keywords:
            empty_label = QLabel("키워드가 없습니다.\n위의 '새 키워드' 버튼을 눌러 추가하세요.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #565f89; font-size: 12pt; padding: 40px;")
            self.cards_layout.addWidget(empty_label)
        
        self.cards_layout.addStretch()
        
        # Update count badge
        self.count_badge.setText(str(len(keywords)))
        
        self.selected_index = -1
    
    def on_card_clicked(self, index: int):
        # Deselect previous
        if 0 <= self.selected_index < len(self.cards):
            self.cards[self.selected_index].set_selected(False)
        
        # Select new
        self.selected_index = index
        if 0 <= index < len(self.cards):
            self.cards[index].set_selected(True)
    
    def on_card_double_clicked(self, index: int):
        self.selected_index = index
        self.edit_keyword()
    
    def add_keyword(self):
        dialog = KeywordEditDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            keyword = dialog.get_keyword()
            if keyword.keyword:
                self.settings.add_keyword(keyword)
                self.refresh_list()
                self.keywords_changed.emit()
    
    def edit_keyword(self):
        if self.selected_index < 0:
            QMessageBox.information(self, "알림", "수정할 키워드를 선택하세요.")
            return
        
        keyword = self.settings.settings.keywords[self.selected_index]
        dialog = KeywordEditDialog(keyword, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_keyword = dialog.get_keyword()
            if new_keyword.keyword:
                self.settings.update_keyword(self.selected_index, new_keyword)
                self.refresh_list()
                self.keywords_changed.emit()
    
    def toggle_keyword(self):
        if self.selected_index < 0:
            QMessageBox.information(self, "알림", "토글할 키워드를 선택하세요.")
            return
        
        keyword = self.settings.settings.keywords[self.selected_index]
        keyword.enabled = not keyword.enabled
        self.settings.update_keyword(self.selected_index, keyword)
        self.refresh_list()
        self.keywords_changed.emit()
    
    def delete_keyword(self):
        if self.selected_index < 0:
            QMessageBox.information(self, "알림", "삭제할 키워드를 선택하세요.")
            return
        
        keyword = self.settings.settings.keywords[self.selected_index]
        
        reply = QMessageBox.question(
            self, "삭제 확인",
            f"'{keyword.keyword}' 키워드를 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings.remove_keyword(self.selected_index)
            self.refresh_list()
            self.keywords_changed.emit()
