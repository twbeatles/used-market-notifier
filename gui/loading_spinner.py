# gui/loading_spinner.py
"""Animated loading spinner component"""

from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont


class LoadingSpinner(QWidget):
    """Animated loading spinner with rotating dots"""
    
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self, message: str = "로딩 중...", parent=None):
        super().__init__(parent)
        self._frame_index = 0
        self._message = message
        self._setup_ui()
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_frame)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 40, 20, 40)
        
        # Spinner
        self.spinner_label = QLabel(self.FRAMES[0])
        self.spinner_label.setStyleSheet("""
            font-size: 48pt;
            color: #89b4fa;
            background: transparent;
        """)
        self.spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.spinner_label)
        
        # Message
        self.message_label = QLabel(self._message)
        self.message_label.setStyleSheet("""
            font-size: 12pt;
            color: #a6adc8;
            background: transparent;
            margin-top: 16px;
        """)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)
    
    def _next_frame(self):
        self._frame_index = (self._frame_index + 1) % len(self.FRAMES)
        self.spinner_label.setText(self.FRAMES[self._frame_index])
    
    def start(self):
        self._timer.start(80)
        self.show()
    
    def stop(self):
        self._timer.stop()
        self.hide()
    
    def set_message(self, message: str):
        self._message = message
        self.message_label.setText(message)


class EmptyStateWidget(QWidget):
    """Empty state placeholder with icon, message, and optional action"""
    
    def __init__(
        self, 
        icon: str = "📭", 
        title: str = "데이터 없음",
        message: str = "표시할 항목이 없습니다.",
        action_text: str = None,
        action_callback=None,
        parent=None
    ):
        super().__init__(parent)
        self._setup_ui(icon, title, message, action_text, action_callback)
    
    def _setup_ui(self, icon, title, message, action_text, action_callback):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(40, 60, 40, 60)
        layout.setSpacing(16)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            font-size: 64pt;
            background: transparent;
        """)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 18pt;
            font-weight: bold;
            color: #cdd6f4;
            background: transparent;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet("""
            font-size: 11pt;
            color: #6c7086;
            background: transparent;
        """)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        # Action button
        if action_text and action_callback:
            from PyQt6.QtWidgets import QPushButton
            action_btn = QPushButton(action_text)
            action_btn.setStyleSheet("""
                QPushButton {  
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #89b4fa, stop:1 #74c7ec);
                    color: #1e1e2e;
                    border: none;
                    padding: 12px 32px;
                    border-radius: 10px;
                    font-weight: bold;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #b4befe, stop:1 #89b4fa);
                }
            """)
            action_btn.clicked.connect(action_callback)
            layout.addWidget(action_btn, alignment=Qt.AlignmentFlag.AlignCenter)
