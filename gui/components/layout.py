# gui/components.py
"""
Reusable modern UI components with animations and effects.
"""

from PyQt6.QtWidgets import (
    QFrame, QPushButton, QLabel, QWidget,
    QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, 
    QTimer
)
from PyQt6.QtGui import QColor, QFont

class SectionHeader(QWidget):
    """
    Section header with icon and title.
    """
    
    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(8)
        
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 16pt; background: transparent;")
            layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 14pt;
            font-weight: bold;
            color: #89b4fa;
            background: transparent;
        """)
        layout.addWidget(title_label)
        layout.addStretch()


class EmptyState(QWidget):
    """
    Empty state placeholder with icon, message, and optional action button.
    """
    
    def __init__(
        self, 
        icon: str = "📭", 
        title: str = "데이터가 없습니다",
        message: str = "",
        action_text: str | None = None,
        parent=None
    ):
        super().__init__(parent)
        self.action_callback = None
        self._setup_ui(icon, title, message, action_text)
    
    def _setup_ui(self, icon: str, title: str, message: str, action_text: str | None):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 60, 40, 60)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("""
            font-size: 48pt;
            background: transparent;
            color: #6c7086;
        """)
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 16pt;
            font-weight: bold;
            color: #cdd6f4;
            background: transparent;
        """)
        layout.addWidget(title_label)
        
        # Message
        if message:
            msg_label = QLabel(message)
            msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg_label.setWordWrap(True)
            msg_label.setStyleSheet("""
                font-size: 11pt;
                color: #6c7086;
                background: transparent;
                line-height: 1.5;
            """)
            layout.addWidget(msg_label)
        
        # Action button
        if action_text:
            self.action_btn = QPushButton(action_text)
            self.action_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #89b4fa, stop:1 #74c7ec);
                    color: #1e1e2e;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #b4befe, stop:1 #89b4fa);
                }
            """)
            layout.addWidget(self.action_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def set_action(self, callback):
        """Set callback for action button"""
        self.action_callback = callback
        if hasattr(self, 'action_btn'):
            self.action_btn.clicked.connect(callback)
