"""백그라운드 업데이트 확인/다운로드 스레드."""

from __future__ import annotations

import threading

from PyQt6.QtCore import QThread, pyqtSignal

from updater.installer import UpdateCancelledError
from updater.manifest import ReleaseManifest
from updater.service import UpdateService


class UpdateCheckThread(QThread):
    """원격 매니페스트를 확인하고 결과만 시그널로 전달합니다."""

    found = pyqtSignal(object)
    up_to_date = pyqtSignal()
    failed = pyqtSignal(str)

    def run(self) -> None:
        try:
            manifest = UpdateService().check_for_update()
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        if manifest is None:
            self.up_to_date.emit()
        else:
            self.found.emit(manifest)


class UpdateDownloadThread(QThread):
    """검증된 스테이징 파일을 만들 때까지 다운로드합니다."""

    progress = pyqtSignal(int, int)
    completed = pyqtSignal(str)
    cancelled = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, manifest: ReleaseManifest, service: UpdateService, parent=None):
        super().__init__(parent)
        self.manifest = manifest
        self.service = service
        self.cancel_event = threading.Event()

    def run(self) -> None:
        try:
            staged = self.service.download_and_stage(
                self.manifest,
                progress_callback=lambda current, total: self.progress.emit(current, total),
                cancel_event=self.cancel_event,
            )
            self.completed.emit(str(staged))
        except UpdateCancelledError:
            self.cancelled.emit()
        except Exception as exc:
            self.failed.emit(str(exc))
