"""기존 QWidget 위젯을 Fluent 페이지로 호스팅하는 얇은 래퍼."""

from PySide6.QtWidgets import QVBoxLayout, QWidget


class HostPage(QWidget):
    """기존 위젯을 그대로 담는 네비게이션 페이지."""

    def __init__(self, content: QWidget, object_name: str, parent=None):
        super().__init__(parent)
        self.setObjectName(object_name)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(content)
        self.content = content


__all__ = ["HostPage"]
