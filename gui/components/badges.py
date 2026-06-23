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

class PlatformBadge(QLabel):
    """
    Platform indicator badge with gradient background.
    """
    
    PLATFORMS = {
        'danggeun': {'color': '#FF6F00', 'emoji': '🥕', 'name': '당근'},
        'bunjang': {'color': '#7B68EE', 'emoji': '⚡', 'name': '번개'},
        'joonggonara': {'color': '#00C853', 'emoji': '🛒', 'name': '중고나라'},
    }
    
    def __init__(self, platform: str, parent=None):
        super().__init__(parent)
        self._setup(platform)
    
    def _setup(self, platform: str):
        info = self.PLATFORMS.get(platform, {'color': '#89b4fa', 'emoji': '🔍', 'name': platform})
        
        self.setText(f"{info['emoji']} {info['name']}")
        
        # Create gradient-like effect with CSS
        base_color = info['color']
        self.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 {base_color}, stop:1 {self._lighten(base_color)});
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 9pt;
            font-weight: bold;
        """)
    
    def _lighten(self, hex_color: str) -> str:
        """Lighten a hex color"""
        # Simple lightening by blending with white
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        factor = 0.3
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        
        return f"#{r:02x}{g:02x}{b:02x}"


class StatusBadge(QLabel):
    """
    Sale status badge with color-coded background.
    """
    
    STATUSES = {
        'for_sale': {'color': '#a6e3a1', 'bg': 'rgba(166, 227, 161, 0.2)', 'text': '판매중', 'icon': '🟢'},
        'reserved': {'color': '#f9e2af', 'bg': 'rgba(249, 226, 175, 0.2)', 'text': '예약중', 'icon': '🟡'},
        'sold': {'color': '#f38ba8', 'bg': 'rgba(243, 139, 168, 0.2)', 'text': '판매완료', 'icon': '🔴'},
        'unknown': {'color': '#6c7086', 'bg': 'rgba(108, 112, 134, 0.2)', 'text': '알수없음', 'icon': '⚪'},
    }
    
    def __init__(self, status: str = 'for_sale', parent=None):
        super().__init__(parent)
        self.set_status(status)
    
    def set_status(self, status: str):
        info = self.STATUSES.get(status, self.STATUSES['unknown'])
        self.setText(f"{info['icon']} {info['text']}")
        self.setStyleSheet(f"""
            background-color: {info['bg']};
            color: {info['color']};
            padding: 4px 10px;
            border-radius: 10px;
            font-size: 9pt;
            font-weight: bold;
        """)
