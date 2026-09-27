# gui/note_dialog.py
"""Dialog for adding/editing notes on listings"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGroupBox
from qfluentwidgets import ComboBox, PrimaryPushButton, PushButton, SubtitleLabel, TextEdit
from PySide6.QtCore import Qt


STATUS_TAGS = {
    "interested": ("관심있음", "#89b4fa"),
    "contacted": ("연락함", "#f9e2af"),
    "negotiating": ("거래중", "#fab387"),
    "completed": ("거래완료", "#a6e3a1"),
    "cancelled": ("취소됨", "#f38ba8"),
}


class NoteDialog(QDialog):
    """Dialog for editing listing notes with status tags"""
    
    def __init__(self, note: str = "", status_tag: str = "interested", parent=None):
        super().__init__(parent)
        self.note = note
        self.status_tag = status_tag
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("메모 편집")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        layout.addWidget(SubtitleLabel("매물 메모", self))
        
        # Status tag selector
        status_group = QGroupBox("상태 태그")
        status_layout = QHBoxLayout(status_group)
        
        self.status_combo = ComboBox(self)
        for key, (label, _) in STATUS_TAGS.items():
            self.status_combo.addItem(label, userData=key)
        
        # Set current status
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == self.status_tag:
                self.status_combo.setCurrentIndex(i)
                break
        
        self.status_combo.setMinimumWidth(150)
        status_layout.addWidget(self.status_combo)
        status_layout.addStretch()
        layout.addWidget(status_group)
        
        # Note text area
        note_group = QGroupBox("메모")
        note_layout = QVBoxLayout(note_group)
        
        self.note_edit = TextEdit(self)
        self.note_edit.setPlainText(self.note)
        self.note_edit.setPlaceholderText("이 매물에 대한 메모를 입력하세요...")
        note_layout.addWidget(self.note_edit)
        layout.addWidget(note_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = PushButton("취소", self)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = PrimaryPushButton("저장", self)
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def get_note(self) -> str:
        return self.note_edit.toPlainText().strip()
    
    def get_status_tag(self) -> str:
        return str(self.status_combo.currentData() or "interested")
