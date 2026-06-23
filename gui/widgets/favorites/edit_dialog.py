# gui/favorites_widget.py
"""Favorites management widget"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QMessageBox, QMenu, QDialog,
    QFormLayout, QLineEdit, QSpinBox, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QFont
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
