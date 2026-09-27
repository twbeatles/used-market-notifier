# gui/message_dialog.py
"""Dialog for generating and copying messages to sellers"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QMessageBox
from qfluentwidgets import BodyLabel, ComboBox, PrimaryPushButton, PushButton, SubtitleLabel, TextEdit
from PySide6.QtCore import Qt
from typing import Mapping, Sequence
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from message_templates import MessageTemplateManager
from .link_utils import open_external_url


class MessageDialog(QDialog):
    """Dialog for generating seller messages from templates"""

    def __init__(
        self,
        listing: Mapping[str, object],
        target_price: int | None = None,
        custom_templates: Sequence[object] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.listing = listing
        self.target_price = target_price
        self.engine = getattr(parent, "engine", None)
        self.manager = MessageTemplateManager(custom_templates)
        self.context = self.manager.create_context_from_listing(listing, target_price)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("판매자에게 메시지")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        layout.addWidget(SubtitleLabel("판매자에게 메시지 보내기", self))

        # Listing info
        info_group = QGroupBox("상품 정보", self)
        info_layout = QVBoxLayout(info_group)

        platform_icons = {
            'danggeun': '당근마켓',
            'bunjang': '번개장터',
            'joonggonara': '중고나라'
        }
        platform_key_raw = self.listing.get('platform', '')
        platform_key = platform_key_raw if isinstance(platform_key_raw, str) else str(platform_key_raw or "")
        platform_display = platform_icons.get(
            platform_key,
            platform_key,
        )

        info_text = BodyLabel(
            f"""
            <b>플랫폼:</b> {platform_display}<br>
            <b>제목:</b> {self.listing.get('title', '-')}<br>
            <b>가격:</b> {self.listing.get('price', '-')}<br>
            <b>판매자:</b> {self.listing.get('seller', '-')}<br>
            <b>지역:</b> {self.listing.get('location', '-')}
            """,
            self,
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        layout.addWidget(info_group)

        # Template selection
        template_layout = QHBoxLayout()
        template_label = BodyLabel("템플릿 선택:", self)
        template_layout.addWidget(template_label)

        self.template_combo = ComboBox(self)
        platform_raw = self.listing.get('platform', 'all')
        platform = platform_raw if isinstance(platform_raw, str) else "all"
        templates = self.manager.get_templates(platform)
        for t in templates:
            self.template_combo.addItem(t.name)
        self.template_combo.setMinimumWidth(200)
        self.template_combo.currentIndexChanged.connect(self._on_template_changed)
        template_layout.addWidget(self.template_combo)
        template_layout.addStretch()
        layout.addLayout(template_layout)

        # Message preview/edit
        message_group = QGroupBox("메시지 (편집 가능)", self)
        message_layout = QVBoxLayout(message_group)

        self.message_edit = TextEdit(self)
        self.message_edit.setMinimumHeight(120)
        message_layout.addWidget(self.message_edit)
        layout.addWidget(message_group)

        # Initial render
        self._on_template_changed(0)

        # Action buttons
        button_layout = QHBoxLayout()

        # Open chat button
        open_btn = PushButton("채팅창 열기", self)
        open_btn.setToolTip("링크를 열고 메시지를 클립보드에 복사합니다")
        open_btn.clicked.connect(self._open_and_copy)
        button_layout.addWidget(open_btn)

        button_layout.addStretch()

        # Cancel button
        cancel_btn = PushButton("닫기", self)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        # Copy button
        copy_btn = PrimaryPushButton("클립보드에 복사", self)
        copy_btn.clicked.connect(self._copy_to_clipboard)
        button_layout.addWidget(copy_btn)

        layout.addLayout(button_layout)

    def _on_template_changed(self, index):
        """Update message when template changes"""
        platform_raw = self.listing.get('platform', 'all')
        platform = platform_raw if isinstance(platform_raw, str) else "all"
        templates = self.manager.get_templates(platform)

        if 0 <= index < len(templates):
            template = templates[index]
            rendered = template.render(self.context)
            self.message_edit.setPlainText(rendered)

    def _copy_to_clipboard(self):
        """Copy current message to clipboard"""
        text = self.message_edit.toPlainText()
        if MessageTemplateManager.copy_to_clipboard(text):
            QMessageBox.information(
                self,
                "복사 완료",
                "메시지가 클립보드에 복사되었습니다.\n\n채팅창에 붙여넣기(Ctrl+V) 하세요!"
            )
        else:
            QMessageBox.warning(self, "오류", "클립보드에 복사할 수 없습니다.")

    def _open_and_copy(self):
        """Open the listing URL and copy message to clipboard"""
        text = self.message_edit.toPlainText()
        MessageTemplateManager.copy_to_clipboard(text)

        url = self.listing.get('url') or self.listing.get('link')
        if url:
            open_external_url(self, self.engine, url, str(self.listing.get("title") or url))
            QMessageBox.information(
                self,
                "메시지 복사됨",
                "메시지가 클립보드에 복사되었습니다.\n\n채팅창에서 Ctrl+V로 붙여넣기 하세요!"
            )
        else:
            QMessageBox.warning(self, "알림", "링크를 찾을 수 없습니다.")

    def get_message(self) -> str:
        """Get the current message text"""
        return self.message_edit.toPlainText()
