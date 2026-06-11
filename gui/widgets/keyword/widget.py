"""Keyword manager widget."""

from .common import *
from .cards import KeywordCard
from .dialog import KeywordEditDialog


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
        # Clear existing cards - proper cleanup to prevent memory leaks
        for card in self.cards:
            try:
                card.clicked.disconnect()
                card.double_clicked.disconnect()
            except Exception:
                pass  # Already disconnected
            card.hide()
            card.setParent(None)
            card.deleteLater()
        self.cards.clear()

        # Remove stretch and other widgets
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

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
