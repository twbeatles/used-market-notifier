# pyright: reportAttributeAccessIssue=false
"""시작 시 업데이트 확인, 다운로드, 적용."""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtWidgets import QMessageBox, QWidget

from gui.update_workers import UpdateCheckThread, UpdateDownloadThread
from updater.manifest import ReleaseManifest
from updater.service import UpdateService
from version import __version__

logger = logging.getLogger("Updater")


class UpdaterMixin(QWidget):
    """MainWindow에 붙는 업데이트 조율."""

    def _start_auto_update_check_if_enabled(self) -> None:
        enabled = bool(getattr(self.settings_manager.settings, "auto_check_update", True))
        if not enabled:
            return
        self.request_update_check(interactive=False)

    def _show_last_update_result(self) -> None:
        try:
            result = UpdateService().check_last_result()
        except Exception:
            logger.exception("이전 업데이트 결과를 읽지 못했습니다.")
            return
        if not result:
            return
        status = str(result.get("status", ""))
        if status == "applied":
            text = "업데이트가 적용되었습니다."
            QMessageBox.information(self, "업데이트", text)
            self._log_update(text, "INFO")
            return
        if status == "rolled_back":
            text = "업데이트에 실패하여 이전 버전으로 되돌렸습니다."
        else:
            error = str(result.get("error", "") or "알 수 없는 오류")
            text = f"업데이트를 적용하지 못했습니다.\n{error}"
        QMessageBox.warning(self, "업데이트", text)
        self._log_update(text.replace("\n", " "), "WARNING")

    def attach_update_ui(self, hooks: object) -> None:
        self._update_ui_hooks = hooks

    def detach_update_ui(self, hooks: object) -> None:
        if getattr(self, "_update_ui_hooks", None) is hooks:
            self._update_ui_hooks = None

    def request_update_check(self, *, interactive: bool) -> None:
        if self._update_thread_running():
            if interactive:
                self._publish_update_status("이미 업데이트 작업을 진행 중입니다.", "warning")
            return
        self._update_interactive = interactive
        if interactive:
            self._publish_update_status("업데이트 확인 중...", "normal")
            self._publish_update_busy(checking=True, downloading=False)
        thread = UpdateCheckThread(self)
        thread.found.connect(self._on_update_found)
        thread.up_to_date.connect(self._on_update_up_to_date)
        thread.failed.connect(self._on_update_check_failed)
        self._update_check_thread = thread
        thread.start()

    def cancel_update_download(self) -> None:
        thread = getattr(self, "_update_download_thread", None)
        event = getattr(thread, "cancel_event", None)
        if event is not None:
            event.set()
        self._publish_update_status("다운로드 취소를 요청했습니다.", "warning")

    def _update_thread_running(self) -> bool:
        for name in ("_update_check_thread", "_update_download_thread"):
            thread = getattr(self, name, None)
            is_running = getattr(thread, "isRunning", None)
            if callable(is_running) and is_running():
                return True
        return False

    def _on_update_found(self, manifest: object) -> None:
        if not isinstance(manifest, ReleaseManifest):
            self._on_update_check_failed("업데이트 정보 형식이 올바르지 않습니다.")
            return
        self._publish_update_busy(checking=False, downloading=False)
        self._pending_manifest = manifest
        size_mb = manifest.artifact_size / (1024 * 1024)
        expires = manifest.expires_at.strftime("%Y-%m-%d")
        self._publish_update_status(f"새 버전 v{manifest.version}", "accent", force=True)
        proceed = QMessageBox.question(
            self,
            "업데이트",
            (
                f"v{manifest.version} 업데이트가 있습니다.\n"
                f"크기: {size_mb:.1f} MB\n"
                f"만료: {expires}\n\n"
                "지금 다운로드할까요?"
            ),
        )
        if proceed == QMessageBox.StandardButton.Yes:
            self._start_update_download(manifest)

    def _on_update_up_to_date(self) -> None:
        self._publish_update_busy(checking=False, downloading=False)
        self._publish_update_status(f"최신 버전입니다 (v{__version__}).", "success")
        if getattr(self, "_update_interactive", False):
            QMessageBox.information(
                self,
                "업데이트",
                f"이미 최신 버전입니다.\nv{__version__}",
            )

    def _on_update_check_failed(self, error_message: str) -> None:
        self._publish_update_busy(checking=False, downloading=False)
        if not getattr(self, "_update_interactive", False):
            logger.warning("자동 업데이트 확인 실패: %s", error_message)
            return
        self._publish_update_status(f"확인 실패: {error_message}", "warning", force=True)
        QMessageBox.warning(
            self,
            "업데이트 확인 실패",
            f"업데이트 정보를 가져오지 못했습니다.\n{error_message}",
        )

    def _start_update_download(self, manifest: ReleaseManifest) -> None:
        service = UpdateService()
        self._update_service = service
        self._pending_manifest = manifest
        self._publish_update_busy(checking=False, downloading=True)
        self._publish_update_status("다운로드하고 서명을 검증하는 중...", "accent", force=True)
        thread = UpdateDownloadThread(manifest, service, self)
        thread.progress.connect(self._on_update_progress)
        thread.completed.connect(self._on_update_download_complete)
        thread.cancelled.connect(self._on_update_download_cancelled)
        thread.failed.connect(self._on_update_download_failed)
        self._update_download_thread = thread
        thread.start()

    def _on_update_progress(self, current: int, total: int) -> None:
        current_mb = current / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        self._publish_update_status(
            f"다운로드 중... {current_mb:.1f} / {total_mb:.1f} MB",
            "accent",
            force=True,
        )

    def _on_update_download_cancelled(self) -> None:
        self._publish_update_busy(checking=False, downloading=False)
        self._publish_update_status("다운로드를 취소했습니다.", "muted", force=True)

    def _on_update_download_failed(self, error_message: str) -> None:
        self._publish_update_busy(checking=False, downloading=False)
        self._publish_update_status(f"다운로드 실패: {error_message}", "warning", force=True)
        QMessageBox.critical(
            self,
            "업데이트 실패",
            f"업데이트를 받지 못했습니다.\n{error_message}",
        )

    def _on_update_download_complete(self, staged_path: str) -> None:
        self._publish_update_busy(checking=False, downloading=False)
        manifest = getattr(self, "_pending_manifest", None)
        service = getattr(self, "_update_service", None)
        if not isinstance(manifest, ReleaseManifest) or not isinstance(service, UpdateService):
            self._on_update_download_failed("다운로드 결과를 확인할 수 없습니다.")
            return
        self._publish_update_status(f"v{manifest.version} 검증이 끝났습니다.", "success", force=True)
        import sys

        if not getattr(sys, "frozen", False):
            QMessageBox.information(
                self,
                "개발 환경",
                "패키징된 실행 파일에서만 교체합니다.\n"
                f"검증된 파일: {staged_path}",
            )
            return
        apply_now = QMessageBox.question(
            self,
            "업데이트 준비됨",
            f"v{manifest.version} 설치를 위해 앱을 다시 시작할까요?",
        )
        if apply_now != QMessageBox.StandardButton.Yes:
            return
        try:
            service.launch_update_and_exit(
                Path(staged_path),
                manifest,
                before_exit=self._prepare_process_exit_for_update,
            )
        except Exception as exc:
            QMessageBox.critical(self, "업데이트 적용 실패", f"업데이트를 시작하지 못했습니다.\n{exc}")

    def _prepare_process_exit_for_update(self) -> None:
        self._is_quitting = True
        stop_monitoring = getattr(self, "stop_monitoring", None)
        if callable(stop_monitoring):
            stop_monitoring()
        database = getattr(self, "db", None)
        close = getattr(database, "close", None)
        if callable(close):
            close()
        tray = getattr(self, "tray_icon", None)
        hide = getattr(tray, "hide", None)
        if callable(hide):
            hide()

    def _publish_update_status(self, text: str, kind: str, *, force: bool = False) -> None:
        hooks = getattr(self, "_update_ui_hooks", None)
        setter = getattr(hooks, "set_update_status", None)
        if callable(setter):
            setter(text, kind)
        if force or getattr(self, "_update_interactive", False):
            level = "WARNING" if kind == "warning" else "INFO"
            self._log_update(text, level)

    def _publish_update_busy(self, *, checking: bool, downloading: bool) -> None:
        hooks = getattr(self, "_update_ui_hooks", None)
        setter = getattr(hooks, "set_update_busy", None)
        if callable(setter):
            setter(checking, downloading)

    def _log_update(self, message: str, level: str) -> None:
        status_bar = getattr(self, "status_bar", None)
        show_message = getattr(status_bar, "showMessage", None)
        if callable(show_message):
            show_message(message)
        log_widget = getattr(self, "log_widget", None)
        append_log = getattr(log_widget, "append_log", None)
        if callable(append_log):
            append_log(message, level)


__all__ = ["UpdaterMixin"]
