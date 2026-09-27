# pyright: reportAttributeAccessIssue=false
"""Monitor thread lifecycle and engine event slots (Fluent)."""

from PySide6.QtWidgets import QWidget
from qfluentwidgets import InfoBar, InfoBarPosition

from gui.main.threads import MonitorThread
from monitor_engine import MonitorEngine


class MonitoringMixin(QWidget):
    """Owns the monitor thread lifecycle and engine event slots."""

    def toggle_monitoring(self):
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def start_monitoring(self):
        if self.monitor_thread and self.monitor_thread.isRunning():
            return

        # Check if there are keywords
        if not self.settings_manager.settings.keywords:
            InfoBar.warning(
                "키워드 없음",
                "모니터링할 키워드가 없습니다. 키워드 페이지에서 먼저 추가해주세요.",
                parent=self.window(),
                position=InfoBarPosition.TOP,
            )
            self.switchTo(self.keyword_page)
            return

        self.engine = MonitorEngine(self.settings_manager, db=self.db)
        self.stats_widget.set_engine(self.engine)
        self.listings_widget.set_engine(self.engine)
        if hasattr(self, "favorites_widget") and self.favorites_widget:
            self.favorites_widget.set_engine(self.engine)
        if hasattr(self, "history_widget") and self.history_widget:
            self.history_widget.set_engine(self.engine)

        self.monitor_thread = MonitorThread(self.engine)
        self.monitor_thread.status_update.connect(self.on_status_update)
        self.monitor_thread.new_item.connect(self.on_new_item)
        self.monitor_thread.price_change.connect(self.on_price_change)
        self.monitor_thread.error.connect(self.on_error)
        # Handle thread termination to reset UI
        self.monitor_thread.finished.connect(self.on_monitor_finished)
        self.monitor_thread.start()

        self.update_ui_state(True)

    def on_monitor_finished(self):
        """Called when monitor thread finishes (unexpectedly or normally)"""
        if self.monitor_thread and self.monitor_thread.isRunning():
            # Thread ended unexpectedly
            self.on_status_update("모니터링이 종료되었습니다. 다시 시작하려면 버튼을 눌러주세요.")

    def stop_monitoring(self):
        if self.monitor_thread:
            self.monitor_thread.stop()
            self.monitor_thread.wait(5000)
            self.monitor_thread = None

        self.update_ui_state(False)

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
        # Skip NOTIFICATIONS during initial crawl, but still update UI
        skip_notification = hasattr(self.engine, 'is_first_run') and self.engine.is_first_run

        if not skip_notification:
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

        # Restart if running
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.stop_monitoring()
            self.start_monitoring()


__all__ = ["MonitoringMixin"]
