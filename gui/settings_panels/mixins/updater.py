# pyright: reportAttributeAccessIssue=false, reportArgumentType=false
"""설정 창의 소프트웨어 업데이트 카드."""

from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from gui.link_utils import open_external_url
from updater.constants import UPDATE_RELEASES_URL
from version import __version__

_UPDATE_COLORS = {
    "muted": "#a6adc8",
    "normal": "#cdd6f4",
    "accent": "#89b4fa",
    "success": "#a6e3a1",
    "warning": "#f9e2af",
}


if TYPE_CHECKING:
    from gui.settings_panels.dialog import SettingsDialog
    _HostBase_UpdateSettingsMixin = SettingsDialog
else:
    _HostBase_UpdateSettingsMixin = object

class UpdateSettingsMixin(_HostBase_UpdateSettingsMixin):
    """유지보수 탭에 업데이트 확인 UI를 붙입니다."""

    def _add_update_group(self, layout: QVBoxLayout) -> None:
        group = QGroupBox("🔄 소프트웨어 업데이트")
        inner = QVBoxLayout(group)
        inner.setSpacing(10)

        version_row = QHBoxLayout()
        version_label = QLabel("현재 버전")
        self.current_version_label = QLabel(f"v{__version__}")
        self.current_version_label.setStyleSheet("color: #89b4fa; font-weight: bold;")
        version_row.addWidget(version_label)
        version_row.addWidget(self.current_version_label)
        version_row.addStretch()

        self.check_update_btn = QPushButton("업데이트 확인")
        self.check_update_btn.setMinimumHeight(34)
        self.check_update_btn.clicked.connect(self._on_check_update_clicked)
        version_row.addWidget(self.check_update_btn)

        self.cancel_download_btn = QPushButton("취소")
        self.cancel_download_btn.setMinimumHeight(34)
        self.cancel_download_btn.setVisible(False)
        self.cancel_download_btn.clicked.connect(self._on_cancel_download_clicked)
        version_row.addWidget(self.cancel_download_btn)
        inner.addLayout(version_row)

        option_row = QHBoxLayout()
        self.auto_check_update_check = QCheckBox("시작할 때 업데이트 확인")
        self.auto_check_update_check.toggled.connect(self._save_auto_check_update)
        option_row.addWidget(self.auto_check_update_check)
        option_row.addStretch()

        releases_btn = QPushButton("릴리즈 노트")
        releases_btn.setObjectName("secondary")
        releases_btn.clicked.connect(self._open_update_releases)
        option_row.addWidget(releases_btn)
        inner.addLayout(option_row)

        self.update_status_label = QLabel("서명된 릴리즈 매니페스트를 확인해 새 버전을 받습니다.")
        self.update_status_label.setWordWrap(True)
        self.update_status_label.setStyleSheet(f"color: {_UPDATE_COLORS['muted']};")
        inner.addWidget(self.update_status_label)

        layout.addWidget(group)
        parent = self.parent()
        attach = getattr(parent, "attach_update_ui", None)
        if callable(attach):
            attach(self)

    def done(self, a0: int) -> None:
        parent = self.parent()
        detach = getattr(parent, "detach_update_ui", None)
        if callable(detach):
            detach(self)
        super().done(a0)  # type: ignore[misc]

    def set_update_status(self, text: str, kind: str) -> None:
        label = getattr(self, "update_status_label", None)
        if label is None:
            return
        color = _UPDATE_COLORS.get(kind, _UPDATE_COLORS["normal"])
        label.setText(text)
        label.setStyleSheet(f"color: {color};")

    def set_update_busy(self, checking: bool, downloading: bool) -> None:
        check_button = getattr(self, "check_update_btn", None)
        cancel_button = getattr(self, "cancel_download_btn", None)
        if check_button is not None:
            check_button.setEnabled(not checking and not downloading)
        if cancel_button is not None:
            cancel_button.setVisible(downloading)

    def _save_auto_check_update(self, checked: bool) -> None:
        self.settings.settings.auto_check_update = bool(checked)
        self.settings.save()

    def _on_check_update_clicked(self) -> None:
        parent = self.parent()
        request = getattr(parent, "request_update_check", None)
        if not callable(request):
            QMessageBox.warning(self, "업데이트", "이 화면에서는 업데이트를 확인할 수 없습니다.")
            return
        request(interactive=True)

    def _on_cancel_download_clicked(self) -> None:
        parent = self.parent()
        cancel = getattr(parent, "cancel_update_download", None)
        if callable(cancel):
            cancel()

    def _open_update_releases(self) -> None:
        parent = self.parent()
        engine = getattr(parent, "engine", None)
        open_external_url(self, engine, UPDATE_RELEASES_URL, "릴리즈 페이지")


__all__ = ["UpdateSettingsMixin"]
