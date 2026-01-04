# gui/keyword_manager.py
"""Enhanced keyword management widget with modern card-based design"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QDialog, QFormLayout, QLineEdit, QSpinBox, QComboBox,
    QCheckBox, QLabel, QGroupBox, QMessageBox, QTextEdit, QFrame,
    QScrollArea, QGridLayout, QSizePolicy, QGraphicsDropShadowEffect,
    QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QFont, QColor
from models import SearchKeyword, KeywordPreset


class KeywordCard(QFrame):
    """Individual keyword card with modern glassmorphism design and hover effects"""
    
    clicked = pyqtSignal(int)
    double_clicked = pyqtSignal(int)
    
    def __init__(self, index: int, keyword: SearchKeyword, parent=None):
        super().__init__(parent)
        self.index = index
        self.keyword = keyword
        self.selected = False
        self._setup_shadow()
        self.setup_ui()
    
    def _setup_shadow(self):
        """Setup drop shadow effect for card lift"""
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 50))
        self.shadow.setOffset(0, 4)
        self.setGraphicsEffect(self.shadow)
    
    def setup_ui(self):
        self.setObjectName("keywordCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(18, 14, 18, 14)
        
        # Header row
        header = QHBoxLayout()
        
        # Status indicator with animation-ready style
        status = "🟢" if self.keyword.enabled else "⏸️"
        status_label = QLabel(status)
        status_label.setStyleSheet("font-size: 16pt; background: transparent;")
        header.addWidget(status_label)
        
        # Keyword name with accent color
        name_label = QLabel(self.keyword.keyword)
        name_label.setStyleSheet("""
            font-size: 14pt; 
            font-weight: bold; 
            color: #cdd6f4;
            background: transparent;
        """)
        header.addWidget(name_label)
        
        header.addStretch()
        
        # Platform badges with gradient
        for platform in self.keyword.platforms:
            badge = self.create_platform_badge(platform)
            header.addWidget(badge)
        
        layout.addLayout(header)
        
        # Details row
        details = QHBoxLayout()
        details.setSpacing(16)
        
        # Price range with icon
        if self.keyword.min_price or self.keyword.max_price:
            min_str = f"{self.keyword.min_price:,}" if self.keyword.min_price else "0"
            max_str = f"{self.keyword.max_price:,}" if self.keyword.max_price else "∞"
            price_label = QLabel(f"💰 {min_str} ~ {max_str}원")
            price_label.setStyleSheet("""
                color: #a6e3a1; 
                font-size: 9pt;
                background: transparent;
            """)
            details.addWidget(price_label)
        
        # Location
        if self.keyword.location:
            loc_label = QLabel(f"📍 {self.keyword.location}")
            loc_label.setStyleSheet("""
                color: #fab387; 
                font-size: 9pt;
                background: transparent;
            """)
            details.addWidget(loc_label)
        
        # Excludes
        if self.keyword.exclude_keywords:
            ex_label = QLabel(f"🚫 {len(self.keyword.exclude_keywords)}개 제외")
            ex_label.setStyleSheet("""
                color: #f38ba8; 
                font-size: 9pt;
                background: transparent;
            """)
            details.addWidget(ex_label)
        
        # Notification status
        notify_enabled = getattr(self.keyword, 'notify_enabled', True)
        notify_icon = "🔔" if notify_enabled else "🔕"
        notify_label = QLabel(notify_icon)
        notify_label.setStyleSheet("""
            font-size: 9pt;
            background: transparent;
        """)
        notify_label.setToolTip("알림 " + ("켜짐" if notify_enabled else "꺼짐"))
        details.addWidget(notify_label)
        
        details.addStretch()
        layout.addLayout(details)
    
    def create_platform_badge(self, platform: str) -> QLabel:
        """Create gradient platform badge"""
        colors = {
            'danggeun': ('#FF6F00', '#FF9800', '🥕'),
            'bunjang': ('#7B68EE', '#9575CD', '⚡'),
            'joonggonara': ('#00C853', '#69F0AE', '🛒')
        }
        base_color, light_color, emoji = colors.get(platform, ('#89b4fa', '#b4befe', '📦'))
        
        badge = QLabel(emoji)
        badge.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 {base_color}, stop:1 {light_color});
            color: white;
            padding: 5px 10px;
            border-radius: 12px;
            font-size: 12pt;
        """)
        return badge
    
    def update_style(self):
        if self.selected:
            self.setStyleSheet("""
                QFrame#keywordCard {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(49, 50, 68, 0.95), stop:1 rgba(69, 71, 90, 0.8));
                    border: 2px solid #89b4fa;
                    border-radius: 16px;
                }
            """)
            self.shadow.setBlurRadius(25)
            self.shadow.setOffset(0, 6)
        else:
            self.setStyleSheet("""
                QFrame#keywordCard {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(30, 30, 46, 0.9), stop:1 rgba(49, 50, 68, 0.7));
                    border: 1px solid rgba(69, 71, 90, 0.5);
                    border-radius: 16px;
                }
                QFrame#keywordCard:hover {
                    border: 1px solid rgba(137, 180, 250, 0.5);
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(37, 37, 53, 0.95), stop:1 rgba(49, 50, 68, 0.85));
                }
            """)
            self.shadow.setBlurRadius(15)
            self.shadow.setOffset(0, 4)
    
    def set_selected(self, selected: bool):
        self.selected = selected
        self.update_style()
    
    def enterEvent(self, event):
        """Lift card on hover"""
        if not self.selected:
            self.shadow.setBlurRadius(22)
            self.shadow.setOffset(0, 6)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Reset card on leave"""
        if not self.selected:
            self.shadow.setBlurRadius(15)
            self.shadow.setOffset(0, 4)
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.index)
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.index)
        super().mouseDoubleClickEvent(event)


class KeywordEditDialog(QDialog):
    """Modern dialog for editing keyword configuration"""
    
    def __init__(self, keyword: SearchKeyword = None, settings_manager=None, parent=None):
        super().__init__(parent)
        self.keyword = keyword or SearchKeyword(keyword="")
        self.settings_manager = settings_manager
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
        
        # Preset dropdown
        preset_row = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("📁 프리셋 선택...")
        self._load_presets()
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        self.preset_combo.setMinimumHeight(36)
        preset_row.addWidget(self.preset_combo)
        
        save_preset_btn = QPushButton("💾 프리셋 저장")
        save_preset_btn.setMinimumHeight(36)
        save_preset_btn.clicked.connect(self._save_as_preset)
        preset_row.addWidget(save_preset_btn)
        keyword_layout.addRow("프리셋", preset_row)
        
        self.enabled_check = QCheckBox("🔍 키워드 모니터링 활성화")
        self.enabled_check.setChecked(True)
        keyword_layout.addRow("", self.enabled_check)
        
        self.notify_check = QCheckBox("🔔 이 키워드 알림 받기")
        self.notify_check.setChecked(True)
        keyword_layout.addRow("", self.notify_check)
        
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
        self.notify_check.setChecked(getattr(self.keyword, 'notify_enabled', True))
        
        if self.keyword.min_price:
            self.min_price_spin.setValue(self.keyword.min_price)
        if self.keyword.max_price:
            self.max_price_spin.setValue(self.keyword.max_price)
        
        self.location_edit.setText(self.keyword.location or "")
        self.exclude_edit.setPlainText("\n".join(self.keyword.exclude_keywords))
        
        self.danggeun_check.setChecked("danggeun" in self.keyword.platforms)
        self.bunjang_check.setChecked("bunjang" in self.keyword.platforms)
        self.joonggonara_check.setChecked("joonggonara" in self.keyword.platforms)
    
    def _load_presets(self):
        """Load presets into combo box"""
        if self.settings_manager:
            for preset in self.settings_manager.get_presets():
                self.preset_combo.addItem(f"📋 {preset.name}", preset)
    
    def _on_preset_selected(self, index: int):
        """Apply selected preset"""
        if index <= 0:
            return
        preset = self.preset_combo.itemData(index)
        if preset:
            if preset.min_price:
                self.min_price_spin.setValue(preset.min_price)
            else:
                self.min_price_spin.setValue(0)
            if preset.max_price:
                self.max_price_spin.setValue(preset.max_price)
            else:
                self.max_price_spin.setValue(0)
            self.location_edit.setText(preset.location or "")
            self.exclude_edit.setPlainText("\n".join(preset.exclude_keywords))
            self.danggeun_check.setChecked("danggeun" in preset.platforms)
            self.bunjang_check.setChecked("bunjang" in preset.platforms)
            self.joonggonara_check.setChecked("joonggonara" in preset.platforms)
    
    def _save_as_preset(self):
        """Save current settings as preset"""
        if not self.settings_manager:
            QMessageBox.warning(self, "오류", "설정 관리자 없음")
            return
        
        name, ok = QInputDialog.getText(self, "프리셋 저장", "프리셋 이름:")
        if not ok or not name.strip():
            return
        
        platforms = []
        if self.danggeun_check.isChecked():
            platforms.append("danggeun")
        if self.bunjang_check.isChecked():
            platforms.append("bunjang")
        if self.joonggonara_check.isChecked():
            platforms.append("joonggonara")
        
        exclude_text = self.exclude_edit.toPlainText().strip()
        exclude_keywords = [k.strip() for k in exclude_text.split("\n") if k.strip()]
        
        preset = KeywordPreset(
            name=name.strip(),
            min_price=self.min_price_spin.value() if self.min_price_spin.value() > 0 else None,
            max_price=self.max_price_spin.value() if self.max_price_spin.value() > 0 else None,
            location=self.location_edit.text().strip() or None,
            exclude_keywords=exclude_keywords,
            platforms=platforms,
        )
        self.settings_manager.add_preset(preset)
        
        # Refresh combo
        self.preset_combo.addItem(f"📋 {name}", preset)
        QMessageBox.information(self, "성공", f"프리셋 '{name}'이(가) 저장되었습니다!")
    
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
            enabled=self.enabled_check.isChecked(),
            notify_enabled=self.notify_check.isChecked(),
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
        add_btn.setToolTip("새로운 검색 키워드를 추가합니다")
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
        edit_btn.setToolTip("선택한 키워드 설정을 수정합니다 (더블클릭으로도 가능)")
        edit_btn.clicked.connect(self.edit_keyword)
        action_layout.addWidget(edit_btn)
        
        toggle_btn = QPushButton("⏯️ 활성화 토글")
        toggle_btn.setObjectName("secondary")
        toggle_btn.setToolTip("키워드 모니터링 활성화/비활성화 전환")
        toggle_btn.clicked.connect(self.toggle_keyword)
        action_layout.addWidget(toggle_btn)
        
        up_btn = QPushButton("⬆️ 위로")
        up_btn.setObjectName("secondary")
        up_btn.setToolTip("키워드 순서를 위로 이동")
        up_btn.clicked.connect(self.move_keyword_up)
        action_layout.addWidget(up_btn)
        
        down_btn = QPushButton("⬇️ 아래로")
        down_btn.setObjectName("secondary")
        down_btn.setToolTip("키워드 순서를 아래로 이동")
        down_btn.clicked.connect(self.move_keyword_down)
        action_layout.addWidget(down_btn)
        
        delete_btn = QPushButton("🗑️ 삭제")
        delete_btn.setObjectName("danger")
        delete_btn.setToolTip("선택한 키워드를 삭제합니다")
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
            empty_label = QLabel("🔍 아직 키워드가 없어요\n\n위의 '+ 새 키워드' 버튼을 눌러\n모니터링할 검색어를 추가하세요!")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #6c7086; font-size: 12pt; padding: 40px; line-height: 1.6;")
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

    def move_keyword_up(self):
        """Move selected keyword up"""
        if self.selected_index <= 0:
            return
        self.move_keyword(self.selected_index, self.selected_index - 1)
        
    def move_keyword_down(self):
        """Move selected keyword down"""
        if self.selected_index < 0 or self.selected_index >= len(self.cards) - 1:
            return
        self.move_keyword(self.selected_index, self.selected_index + 1)
        
    def move_keyword(self, old_idx, new_idx):
        """Swap keywords and refresh"""
        keywords = self.settings.settings.keywords
        if not (0 <= old_idx < len(keywords) and 0 <= new_idx < len(keywords)):
            return
            
        # Swap
        keywords[old_idx], keywords[new_idx] = keywords[new_idx], keywords[old_idx]
        self.settings.save()
        self.refresh_list()
        
        # Reselect the moved item
        self.on_card_clicked(new_idx)
    
    def add_keyword(self):
        dialog = KeywordEditDialog(settings_manager=self.settings, parent=self)
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
        dialog = KeywordEditDialog(keyword, settings_manager=self.settings, parent=self)
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
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("삭제 확인")
        msg_box.setText(f"'{keyword.keyword}' 키워드를 삭제하시겠습니까?")
        msg_box.setIcon(QMessageBox.Icon.Question)
        yes_btn = msg_box.addButton("예", QMessageBox.ButtonRole.YesRole)
        msg_box.addButton("아니오", QMessageBox.ButtonRole.NoRole)
        msg_box.exec()
        
        if msg_box.clickedButton() == yes_btn:
            self.settings.remove_keyword(self.selected_index)
            self.refresh_list()
            self.keywords_changed.emit()
