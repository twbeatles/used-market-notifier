# gui/favorites_widget.py
"""Favorites management widget"""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QDialog, QFormLayout
from qfluentwidgets import PrimaryPushButton, PushButton, SpinBox, TextEdit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont
from db import DatabaseManager
from ...link_utils import open_external_url

class FavoritesEditDialog(QDialog):
    """Dialog to edit favorite notes and target price"""
    def __init__(self, notes: str, target_price: int | None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("즐겨찾기 수정")
        self.setFixedWidth(300)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.target_price_spin = SpinBox(self)
        self.target_price_spin.setRange(0, 1000000000)
        self.target_price_spin.setSingleStep(1000)
        self.target_price_spin.setSpecialValueText("설정 안함")
        self.target_price_spin.setValue(target_price if target_price else 0)

        self.notes_edit = TextEdit(self)
        self.notes_edit.setPlaceholderText("메모를 입력하세요...")
        self.notes_edit.setText(notes)
        self.notes_edit.setMaximumHeight(100)

        form_layout.addRow("목표 가격:", self.target_price_spin)
        form_layout.addRow("메모:", self.notes_edit)

        layout.addLayout(form_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = PrimaryPushButton("저장", self)
        save_btn.clicked.connect(self.accept)
        cancel_btn = PushButton("취소", self)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_data(self):
        tp = self.target_price_spin.value()
        return {
            'target_price': tp if tp > 0 else None,
            'notes': self.notes_edit.toPlainText()
        }
