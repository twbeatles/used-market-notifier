# gui/loading_spinner.py
"""Animated loading spinner component"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from qfluentwidgets import (
    CaptionLabel,
    IconWidget,
    PrimaryPushButton,
    SubtitleLabel,
)
from qfluentwidgets import (
    FluentIcon as FIF,
)


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
        self.spinner_label = CaptionLabel(self.FRAMES[0], self)
        self.spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.spinner_label)
        
        # Message
        self.message_label = CaptionLabel(self._message, self)
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
    """Empty state placeholder with Fluent icon, title, and optional action"""

    def __init__(
        self,
        icon: "str | FIF" = FIF.INFO,
        title: str = "데이터 없음",
        message: str = "표시할 항목이 없습니다.",
        action_text: str | None = None,
        action_callback=None,
        parent=None
    ):
        super().__init__(parent)
        self._setup_ui(icon, title, message, action_text, action_callback)

    def _setup_ui(self, icon, title: str, message: str, action_text: str | None, action_callback):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(40, 60, 40, 60)
        layout.setSpacing(16)

        # Icon (FluentIcon preferred; plain strings stay backward compatible)
        if isinstance(icon, FIF):
            icon_widget = IconWidget(icon, self)
            icon_widget.setFixedSize(64, 64)
            layout.addWidget(icon_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            icon_label = QLabel(icon)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)

        # Title
        title_label = SubtitleLabel(title, self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Message
        msg_label = CaptionLabel(message, self)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        # Action button
        if action_text and action_callback:
            action_btn = PrimaryPushButton(action_text, self)
            action_btn.clicked.connect(action_callback)
            layout.addWidget(action_btn, alignment=Qt.AlignmentFlag.AlignCenter)
