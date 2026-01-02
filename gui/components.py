from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, Qt
from PyQt6.QtGui import QColor

class StatCard(QFrame):
    """Modern statistic card with gradient background and hover effects"""
    
    def __init__(self, title: str, value: str, icon: str = "", 
                 color: str = "#89b4fa", gradient_end: str = None, parent=None):
        super().__init__(parent)
        self.color = color
        self.gradient_end = gradient_end or self._darken_color(color)
        self.setup_ui(title, value, icon)
        self._setup_shadow()
    
    def _darken_color(self, hex_color: str) -> str:
        """Darken a hex color"""
        c = hex_color.lstrip('#')
        rgb = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(max(0, int(v * 0.7)) for v in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
    
    def _setup_shadow(self):
        """Add subtle drop shadow for depth"""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.setGraphicsEffect(shadow)
    
    def setup_ui(self, title: str, value: str, icon: str):
        self.setMinimumSize(180, 110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Dark background with colored border - use specific class selector
        self.setObjectName("statCard")
        self.setStyleSheet(f"""
            QFrame#statCard {{
                background-color: #1e1e2e;
                border: 2px solid {self.color};
                border-radius: 16px;
            }}
            QFrame#statCard:hover {{
                background-color: #313244;
            }}
            QFrame#statCard QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Icon and title row
        header = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20pt; background: transparent;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {self.color}; font-size: 11pt; font-weight: bold; background: transparent;")
        header.addWidget(title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            font-size: 28pt; 
            font-weight: bold; 
            color: #cdd6f4;
            background: transparent;
        """)
        layout.addWidget(self.value_label)
        
        layout.addStretch()
    
    def update_value(self, value: str):
        self.value_label.setText(value)
    
    def set_value(self, value: str):
        self.update_value(value)

