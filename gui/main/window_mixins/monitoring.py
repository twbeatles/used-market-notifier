# pyright: reportAttributeAccessIssue=false
"""Monitor thread lifecycle and engine event slots (Fluent)."""

import logging

from PySide6.QtWidgets import QWidget
from qfluentwidgets import InfoBar, InfoBarPosition

from gui.main.threads import MonitorThread
from monitor_engine import MonitorEngine


class MonitoringMixin(QWidget):
    """Owns the monitor thread lifecycle and engine event slots.

    Stopping never blocks the UI thread unless the caller asks for ``wait=True``
    (quit / restore / update). A stopping thread stays referenced in
    ``_stopping_threads`` until its ``finished`` signal fires; a start request
    made meanwhile is deferred via ``_pending_start`` so at most one engine runs.
    """

    def _monitor_state_init(self) -> None:
        if not hasattr(self, "_stopping_threads"):
            self._stopping_threads: list[MonitorThread] = []
        if not hasattr(self, "_pending_start"):
            self._pending_start = False
        if not hasattr(self, "_engine_started_once"):
            self._engine_started_once = False

    def is_monitoring_active(self) -> bool:
        """True while a monitor thread is running or still shutting down."""
        self._monitor_state_init()
        thread = self.monitor_thread
        if thread is not None and thread.isRunning():
            return True
        return any(t.isRunning() for t in self._stopping_threads)

    def toggle_monitoring(self):
        self._monitor_state_init()
        if (self.monitor_thread and self.monitor_thread.isRunning()) or self._pending_start:
            self.stop_monitoring()  # also cancels a start that is waiting for the old thread
        else:
            self.start_monitoring()

    def start_monitoring(self):
        self._monitor_state_init()
        if self.monitor_thread and self.monitor_thread.isRunning():
            return

        # Check if there are keywords
        if not self.settings_manager.settings.keywords:
            self._pending_start = False
            InfoBar.warning(
                "키워드 없음",
                "모니터링할 키워드가 없습니다. 키워드 페이지에서 먼저 추가해주세요.",
                parent=self.window(),
                position=InfoBarPosition.TOP,
            )
            self.switchTo(self.keyword_page)
            return

        self._prune_stopping_threads()
        if self._stopping_threads:
            # Previous engine is still cleaning up; start as soon as it finishes.
            self._pending_start = True
            self.monitor_page.set_running(True)
            self.monitor_page.set_status("이전 모니터링 정리 중... 완료 후 시작합니다")
            return

        self._pending_start = False
        # Only the first engine of this process skips its first-cycle notifications;
        # in-app restarts (e.g. after saving settings) must not drop new-item alerts.
        self.engine = MonitorEngine(
            self.settings_manager,
            db=self.db,
            suppress_initial_notifications=not self._engine_started_once,
        )
        self._engine_started_once = True
        self.stats_widget.set_engine(self.engine)
        self.listings_widget.set_engine(self.engine)
        if hasattr(self, "favorites_widget") and self.favorites_widget:
            self.favorites_widget.set_engine(self.engine)
        if hasattr(self, "history_widget") and self.history_widget:
            self.history_widget.set_engine(self.engine)

        thread = MonitorThread(self.engine)
        thread.status_update.connect(self.on_status_update)
        thread.new_item.connect(self.on_new_item)
        thread.price_change.connect(self.on_price_change)
        thread.error.connect(self.on_error)
        thread.finished.connect(lambda t=thread: self._on_monitor_thread_finished(t))
        self.monitor_thread = thread
        thread.start()

        self.update_ui_state(True)

    def _prune_stopping_threads(self) -> None:
        self._stopping_threads = [t for t in self._stopping_threads if t.isRunning()]

    def _on_monitor_thread_finished(self, thread: MonitorThread) -> None:
        """Runs on the UI thread when a monitor thread has fully exited."""
        self._monitor_state_init()
        if thread in self._stopping_threads:
            self._stopping_threads.remove(thread)
        if thread is self.monitor_thread:
            # Engine stopped on its own (no scrapers, too many errors, ...).
            self.monitor_thread = None
            self.update_ui_state(False)
            self.on_status_update("모니터링이 종료되었습니다. 다시 시작하려면 버튼을 눌러주세요.")
        self._prune_stopping_threads()
        if self._stopping_threads:
            return
        if self._pending_start:
            self._pending_start = False
            self.start_monitoring()
        elif self.monitor_thread is None:
            self.monitor_page.set_status("대기 중")

    def on_monitor_finished(self):
        """Backward-compatible slot (pre-2026-09 API): handle the current thread having exited."""
        thread = self.monitor_thread
        if thread is not None and not thread.isRunning():
            self._on_monitor_thread_finished(thread)

    def _wait_for_stopping_threads(self, timeout_ms: int) -> bool:
        for thread in list(self._stopping_threads):
            if not thread.wait(max(0, int(timeout_ms))):
                logging.getLogger("Main").warning("Monitor thread did not stop within %sms", timeout_ms)
                return False
        self._prune_stopping_threads()
        return True

    def stop_monitoring(self, wait: bool = False, timeout_ms: int = 30000) -> bool:
        """Stop monitoring. Returns False only if ``wait`` was requested and the thread outlived it."""
        self._monitor_state_init()
        self._pending_start = False
        thread = self.monitor_thread
        self.monitor_thread = None
        if thread is not None and thread.isRunning():
            thread.request_stop()
            if thread not in self._stopping_threads:
                self._stopping_threads.append(thread)

        ok = self._wait_for_stopping_threads(timeout_ms) if wait else True
        self.update_ui_state(False)
        self._prune_stopping_threads()
        if self._stopping_threads:
            self.monitor_page.set_status("중지 중...")
        return ok

    def restart_monitoring(self) -> None:
        """Stop the current engine and start a fresh one once the old thread has exited."""
        self.stop_monitoring()
        self._pending_start = True
        self._prune_stopping_threads()
        if not self._stopping_threads:
            self._pending_start = False
            self.start_monitoring()

    def update_ui_state(self, is_running: bool):
        self.monitor_page.set_running(is_running)
        self.monitor_page.set_status("모니터링 중" if is_running else "대기 중")
        self.tray_icon.set_monitoring_state(is_running)

    def on_status_update(self, status: str):
        self.publish_status(status)
        # Update monitor status based on activity
        if "검색 중" in status or "스크래핑" in status:
            self.monitor_page.set_status("검색 중...")
        elif "초기화" in status:
            self.monitor_page.set_status("초기화 중...")
        elif "다음 검색까지" in status:
            self.monitor_page.set_status("모니터링 중")
            # Update last search time
            from datetime import datetime
            self.monitor_page.set_last_search(
                f"마지막 검색: {datetime.now().astimezone().strftime('%H:%M:%S')}"
            )

    def on_new_item(self, item):
        # The engine marks items whose external notification was suppressed
        # (first cycle, new-search baseline, burst limit); keep the tray consistent.
        if not getattr(item, "notification_suppressed", False):
            self.tray_icon.show_notification(
                f"새 상품 - {item.platform}",
                f"{item.title}\n{item.price}"
            )

        self._mark_live_data_dirty(reason="new_item")

    def on_price_change(self, item, old_price: str, new_price: str):
        if hasattr(self.engine, 'is_first_run') and self.engine.is_first_run:
            self._mark_live_data_dirty(reason="price_change")
            return
        self.tray_icon.show_notification(
            "가격 변동",
            f"{item.title}\n{old_price} → {new_price}"
        )
        self._mark_live_data_dirty(reason="price_change")

    def on_error(self, error: str):
        self.publish_status(f"오류: {error}")
        self.monitor_page.set_status("오류 발생")
        InfoBar.error(
            "모니터링 오류",
            error,
            parent=self.window(),
            position=InfoBarPosition.TOP,
        )

    def open_settings(self):
        self.switchTo(self.settings_page)

    def _apply_settings_after_save(self):
        # Apply theme
        self.apply_theme()

        # Update keywords
        self.keyword_widget.refresh_list()

        # Restart if running (non-blocking; the new engine starts after the old thread exits)
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.restart_monitoring()


__all__ = ["MonitoringMixin"]
