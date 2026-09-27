"""Keyword card widgets (Fluent CardWidget, no custom QSS)."""

from qfluentwidgets import CaptionLabel, CardWidget, StrongBodyLabel

from .common import *

PLATFORM_SHORT_NAMES = {
    "danggeun": "당근",
    "bunjang": "번개",
    "joonggonara": "중고나라",
}


class KeywordCard(CardWidget):
    """Individual keyword card (selection shown by status text)."""

    clicked = Signal(int)
    double_clicked = Signal(int)

    def __init__(self, index: int, keyword: SearchKeyword, parent=None):
        super().__init__(parent)
        self.index = index
        self.keyword = keyword
        self.selected = False
        self.setClickEnabled(True)
        self.setup_ui()
        super().clicked.connect(lambda: self.clicked.emit(self.index))

    def setup_ui(self):
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        # Header row
        header = QHBoxLayout()

        self.status_label = CaptionLabel(self._status_text(), self)
        header.addWidget(self.status_label)

        name_label = StrongBodyLabel(self.keyword.keyword, self)
        header.addWidget(name_label, 1)

        for platform in self.keyword.platforms:
            header.addWidget(CaptionLabel(PLATFORM_SHORT_NAMES.get(platform, platform), self))

        layout.addLayout(header)

        # Details row
        details = QHBoxLayout()
        details.setSpacing(16)

        parts: list[str] = []
        if self.keyword.min_price or self.keyword.max_price:
            min_str = f"{self.keyword.min_price:,}" if self.keyword.min_price else "0"
            max_str = f"{self.keyword.max_price:,}" if self.keyword.max_price else "∞"
            parts.append(f"{min_str} ~ {max_str}원")
        if self.keyword.location:
            parts.append(str(self.keyword.location))
        if self.keyword.exclude_keywords:
            parts.append(f"{len(self.keyword.exclude_keywords)}개 제외")
        notify_enabled = getattr(self.keyword, "notify_enabled", True)
        parts.append("알림 켜짐" if notify_enabled else "알림 꺼짐")

        details_label = CaptionLabel(" · ".join(parts), self)
        details.addWidget(details_label, 1)
        layout.addLayout(details)

    def _status_text(self) -> str:
        state = "사용 중" if self.keyword.enabled else "사용 안 함"
        if self.selected:
            return f"{state} · 선택됨"
        return state

    def update_style(self):
        self.status_label.setText(self._status_text())

    def set_selected(self, selected: bool):
        self.selected = selected
        self.update_style()

    def mouseDoubleClickEvent(self, a0):
        self.double_clicked.emit(self.index)
        super().mouseDoubleClickEvent(a0)
