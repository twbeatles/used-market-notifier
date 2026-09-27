"""업데이트 페이지 (하단 Navigation, KTrain update_page 대응)."""

from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    HeaderCardWidget,
    PrimaryPushButton,
    ProgressRing,
    PushButton,
    SubtitleLabel,
)

from gui.design_tokens import (
    CARD_VIEW_MARGINS,
    DEFAULT_SPACING,
    PAGE_MARGIN,
    PROGRESS_RING_SIZE,
)
from version import __version__


class UpdatePage(QWidget):
    """서명 릴리즈 확인/다운로드 페이지. window의 update hooks 대상."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("updateInterface")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
        layout.setSpacing(DEFAULT_SPACING)

        layout.addWidget(SubtitleLabel("업데이트"))

        card = HeaderCardWidget(self)
        card.setTitle(f"현재 버전 v{__version__}")
        card.viewLayout.setContentsMargins(*CARD_VIEW_MARGINS)
        layout.addWidget(card)

        status_row = QHBoxLayout()
        status_row.setSpacing(DEFAULT_SPACING)

        self.progress_ring = ProgressRing(self)
        self.progress_ring.setFixedSize(PROGRESS_RING_SIZE, PROGRESS_RING_SIZE)
        self.progress_ring.hide()
        status_row.addWidget(self.progress_ring)

        self.status_label = BodyLabel("서명된 릴리즈 매니페스트를 확인해 새 버전을 받습니다.", self)
        self.status_label.setWordWrap(True)
        status_row.addWidget(self.status_label, 1)

        card.viewLayout.addLayout(status_row)

        action_row = QHBoxLayout()
        action_row.setSpacing(DEFAULT_SPACING)

        self.check_btn = PrimaryPushButton("업데이트 확인", self)
        self.check_btn.clicked.connect(self._on_check_clicked)
        action_row.addWidget(self.check_btn)

        self.cancel_btn = PushButton("다운로드 취소", self)
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        action_row.addWidget(self.cancel_btn)
        action_row.addStretch()

        card.viewLayout.addLayout(action_row)
        layout.addStretch()

    def attach_to_window(self) -> None:
        """생성 이후 window가 확정되면 hooks를 등록한다."""
        host = self.window()
        if not hasattr(host, "attach_update_ui"):
            host = self.parent()
        attach = getattr(host, "attach_update_ui", None)
        if callable(attach):
            attach(self)

    # -- window update hooks -------------------------------------------------
    def set_update_status(self, text: str, kind: str) -> None:
        self.status_label.setText(text)

    def set_update_busy(self, checking: bool, downloading: bool) -> None:
        self.check_btn.setEnabled(not checking and not downloading)
        self.cancel_btn.setVisible(downloading)
        if checking or downloading:
            self.progress_ring.show()
        else:
            self.progress_ring.hide()

    # -- actions --------------------------------------------------------------
    def _host(self):
        window = self.window()
        if hasattr(window, "request_update_check"):
            return window
        return self.parent()

    def _on_check_clicked(self) -> None:
        request = getattr(self._host(), "request_update_check", None)
        if callable(request):
            request(interactive=True)

    def _on_cancel_clicked(self) -> None:
        cancel = getattr(self._host(), "cancel_update_download", None)
        if callable(cancel):
            cancel()


__all__ = ["UpdatePage"]
