# gui/note_dialog.py
"""Dialog for adding/editing notes on listings"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt


STATUS_TAGS = {
    "interested": ("🤔 관심있음", "#89b4fa"),
    "contacted": ("📞 연락함", "#f9e2af"),
    "negotiating": ("💬 거래중", "#fab387"),
    "completed": ("✅ 거래완료", "#a6e3a1"),
    "cancelled": ("❌ 취소됨", "#f38ba8"),
}


class NoteDialog(QDialog):
    """Dialog for editing listing notes with status tags"""
    
    def __init__(self, note: str = "", status_tag: str = "interested", parent=None):
        super().__init__(parent)
        self.note = note
        self.status_tag = status_tag
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("📝 메모 편집")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        self.setStyleSheet("QDialog { background-color: #1e1e2e; }")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("📝 매물 메모")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #cdd6f4;")
        layout.addWidget(title)
        
        # Status tag selector
        status_group = QGroupBox("📌 상태 태그")
        status_layout = QHBoxLayout(status_group)
        
        self.status_combo = QComboBox()
        for key, (label, _) in STATUS_TAGS.items():
            self.status_combo.addItem(label, key)
        
        # Set current status
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == self.status_tag:
                self.status_combo.setCurrentIndex(i)
                break
        
        self.status_combo.setStyleSheet("""
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 150px;
            }
        """)
        status_layout.addWidget(self.status_combo)
        status_layout.addStretch()
        layout.addWidget(status_group)
        
        # Note text area
        note_group = QGroupBox("✏️ 메모")
        note_layout = QVBoxLayout(note_group)
        
        self.note_edit = QTextEdit()
        self.note_edit.setPlainText(self.note)
        self.note_edit.setPlaceholderText("이 매물에 대한 메모를 입력하세요...")
        self.note_edit.setStyleSheet("""
            QTextEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        note_layout.addWidget(self.note_edit)
        layout.addWidget(note_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("취소")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 저장")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1;
                color: #1e1e2e;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #94e2d5;
            }
        """)
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def get_note(self) -> str:
        return self.note_edit.toPlainText().strip()
    
    def get_status_tag(self) -> str:
        return self.status_combo.currentData()
