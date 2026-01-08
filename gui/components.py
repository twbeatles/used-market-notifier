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
    QParallelAnimationGroup, pyqtProperty, QTimer
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
    
    def leaveEvent(self, event):
        """Reset shadow on leave"""
        self._animate_shadow(self._base_shadow_blur, 4)
        super().leaveEvent(event)
    
    def _animate_shadow(self, blur: int, offset_y: int):
        """Animate shadow properties"""
        # Simple animation by directly setting (for performance)
        self.shadow.setBlurRadius(blur)
        self.shadow.setOffset(0, offset_y)


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
    
    def mousePressEvent(self, event):
        """Slight scale down on press"""
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Scale back up on release"""
        super().mouseReleaseEvent(event)


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
        action_text: str = None,
        parent=None
    ):
        super().__init__(parent)
        self.action_callback = None
        self._setup_ui(icon, title, message, action_text)
    
    def _setup_ui(self, icon: str, title: str, message: str, action_text: str):
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

