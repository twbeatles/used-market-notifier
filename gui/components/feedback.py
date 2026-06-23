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

class Toast(QFrame):
    """
    Toast notification popup.
    """
    
    TYPES = {
        'success': {'color': '#a6e3a1', 'icon': '✅'},
        'error': {'color': '#f38ba8', 'icon': '❌'},
        'warning': {'color': '#f9e2af', 'icon': '⚠️'},
        'info': {'color': '#89b4fa', 'icon': 'ℹ️'},
    }
    
    def __init__(self, message: str, toast_type: str = "info", duration: int = 3000, parent=None):
        super().__init__(parent)
        self.duration = duration
        self._setup_ui(message, toast_type)
        self._setup_animation()
    
    def _setup_ui(self, message: str, toast_type: str):
        type_info = self.TYPES.get(toast_type, self.TYPES['info'])
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(49, 50, 68, 0.95);
                border: 1px solid {type_info['color']};
                border-left: 4px solid {type_info['color']};
                border-radius: 8px;
                padding: 12px 16px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        icon_label = QLabel(type_info['icon'])
        icon_label.setStyleSheet("font-size: 16pt; background: transparent;")
        layout.addWidget(icon_label)
        
        msg_label = QLabel(message)
        msg_label.setStyleSheet(f"color: #cdd6f4; font-size: 10pt; background: transparent;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label, 1)
        
        close_btn = QPushButton("×")
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #6c7086;
                border: none;
                font-size: 16pt;
                padding: 0;
                min-width: 24px;
            }
            QPushButton:hover { color: #cdd6f4; }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        # Setup shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
    
    def _setup_animation(self):
        self.fade_timer = QTimer(self)
        self.fade_timer.setSingleShot(True)
        self.fade_timer.timeout.connect(self.close)
    
    def show(self):
        super().show()
        self.fade_timer.start(self.duration)
