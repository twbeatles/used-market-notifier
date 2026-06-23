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

class GlassCard(QFrame):
    """
    Modern glass-morphism styled card with hover lift effect.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glassCard")
        self._setup_shadow()
        self._base_shadow_blur = 15
        self._hover_shadow_blur = 25
        
    def _setup_shadow(self):
        """Setup drop shadow effect"""
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.shadow.setOffset(0, 4)
        self.setGraphicsEffect(self.shadow)
    
    def enterEvent(self, event):
        """Animate shadow on hover"""
        self._animate_shadow(self._hover_shadow_blur, -2)
        super().enterEvent(event)
    
    def leaveEvent(self, a0):
        """Reset shadow on leave"""
        self._animate_shadow(self._base_shadow_blur, 4)
        super().leaveEvent(a0)
    
    def _animate_shadow(self, blur: int, offset_y: int):
        """Animate shadow properties"""
        # Simple animation by directly setting (for performance)
        self.shadow.setBlurRadius(blur)
        self.shadow.setOffset(0, offset_y)


class StatCard(QFrame):
    """
    Statistics display card with gradient background.
    """
    
    def __init__(
        self, 
        title: str, 
        value: str = "0", 
        icon: str = "📊",
        color: str = "#89b4fa",
        parent=None
    ):
        super().__init__(parent)
        self.setObjectName("statCard")
        self._color = color
        self._setup_ui(title, value, icon)
        self._setup_shadow()
    
    def _setup_ui(self, title: str, value: str, icon: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Icon and title row
        header = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20pt; background: transparent;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 11pt; 
            color: #a6adc8; 
            background: transparent;
        """)
        header.addWidget(title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            font-size: 28pt; 
            font-weight: bold; 
            color: {self._color};
            background: transparent;
        """)
        layout.addWidget(self.value_label)
    
    def _setup_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
    
    def set_value(self, value: str):
        """Update the displayed value"""
        self.value_label.setText(value)
