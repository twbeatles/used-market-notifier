"""모니터링 홈 페이지: 조건 Card + Action Bar + 상태 (KTrain §14-15)."""

from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    HeaderCardWidget,
    PrimaryPushButton,
    ProgressRing,
    SubtitleLabel,
)

from gui.design_tokens import (
    CARD_VIEW_MARGINS,
    DEFAULT_SPACING,
    PAGE_MARGIN,
    PROGRESS_RING_SIZE,
)


class MonitorPage(QWidget):
    """모니터링 시작/중지와 현재 상태를 보여주는 홈 페이지."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("monitorInterface")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
        layout.setSpacing(DEFAULT_SPACING)

        layout.addWidget(SubtitleLabel("모니터링"))

        card = HeaderCardWidget(self)
        card.setTitle("작업 조건")
        card.viewLayout.setContentsMargins(*CARD_VIEW_MARGINS)
        layout.addWidget(card)

        status_row = QHBoxLayout()
        status_row.setSpacing(DEFAULT_SPACING)

        self.progress_ring = ProgressRing(self)
        self.progress_ring.setFixedSize(PROGRESS_RING_SIZE, PROGRESS_RING_SIZE)
        self.progress_ring.hide()
        status_row.addWidget(self.progress_ring)

        self.status_label = BodyLabel("대기 중", self)
        status_row.addWidget(self.status_label)
        status_row.addStretch()

        self.last_search_label = CaptionLabel("마지막 검색: -", self)
        status_row.addWidget(self.last_search_label)

        card.viewLayout.addLayout(status_row)

        action_row = QHBoxLayout()
        action_row.setSpacing(DEFAULT_SPACING)

        self.start_btn = PrimaryPushButton("모니터링 시작", self)
        self.start_btn.setToolTip("모니터링 시작/중지 (Ctrl+S)")
        action_row.addWidget(self.start_btn)
        action_row.addStretch()

        card.viewLayout.addLayout(action_row)
        layout.addStretch()

    def set_running(self, is_running: bool) -> None:
        self.start_btn.setText("모니터링 중지" if is_running else "모니터링 시작")
        if is_running:
            self.progress_ring.show()
        else:
            self.progress_ring.hide()

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def set_last_search(self, text: str) -> None:
        self.last_search_label.setText(text)


__all__ = ["MonitorPage"]
