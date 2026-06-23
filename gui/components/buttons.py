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

class AnimatedButton(QPushButton):
    """
    Button with press animation effect.
    """
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._setup_animation()
    
    def _setup_animation(self):
        """Setup press animation"""
        self.press_anim = QPropertyAnimation(self, b"geometry")
        self.press_anim.setDuration(100)
        self.press_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def mousePressEvent(self, e):
        """Slight scale down on press"""
        super().mousePressEvent(e)
    
    def mouseReleaseEvent(self, e):
        """Scale back up on release"""
        super().mouseReleaseEvent(e)


class PulsingDot(QLabel):
    """
    Animated pulsing status indicator dot.
    """
    
    def __init__(self, color: str = "#a6e3a1", parent=None):
        super().__init__("●", parent)
        self._color = color
        self._is_pulsing = False
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse_step)
        self._pulse_state = 0
        self._update_style()
    
    def _update_style(self):
        self.setStyleSheet(f"""
            color: {self._color}; 
            font-size: 12pt; 
            background: transparent;
        """)
    
    def set_color(self, color: str):
        """Set dot color"""
        self._color = color
        self._update_style()
    
    def start_pulsing(self):
        """Start pulse animation"""
        if not self._is_pulsing:
            self._is_pulsing = True
            self._pulse_timer.start(500)  # Toggle every 500ms
    
    def stop_pulsing(self):
        """Stop pulse animation"""
        self._is_pulsing = False
        self._pulse_timer.stop()
        self._update_style()
    
    def _pulse_step(self):
        """Toggle opacity for pulse effect"""
        self._pulse_state = 1 - self._pulse_state
        opacity = "1.0" if self._pulse_state else "0.4"
        self.setStyleSheet(f"""
            color: {self._color}; 
            font-size: 12pt; 
            background: transparent;
            opacity: {opacity};
        """)
