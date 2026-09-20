# pyright: reportAttributeAccessIssue=false
"""Monitoring control: start/stop, engine callbacks, settings dialog."""

from PyQt6.QtWidgets import QMessageBox, QWidget

from gui.main.threads import MonitorThread
from gui.settings_dialog import SettingsDialog
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
            QMessageBox.warning(
                self, "알림",
                "모니터링할 키워드가 없습니다.\n키워드를 먼저 추가해주세요."
            )
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
        self.update_ui_state(False)
        if self.monitor_thread and not self.monitor_thread._stop_requested:
            # Thread ended unexpectedly
            self.on_status_update("모니터링이 종료되었습니다. 다시 시작하려면 버튼을 눌러주세요.")

    def stop_monitoring(self):
        if self.monitor_thread:
            self.monitor_thread.stop()
            self.monitor_thread.wait(5000)
            self.monitor_thread = None

        self.update_ui_state(False)

    def update_ui_state(self, is_running: bool):
        if is_running:
            self.start_btn.setText("⏹️ 중지")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #f38ba8, stop:1 #eba0ac);
                    color: #1e1e2e;
                    border: none;
                    padding: 10px 24px;
                    border-radius: 10px;
                    font-weight: bold;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #eba0ac, stop:1 #f5c2e7);
                }
            """)
            # Update status indicator
            self.status_dot.set_color("#a6e3a1")
            self.status_dot.start_pulsing()
            self.status_text.setText("모니터링 중")
            self.status_text.setStyleSheet("""
                color: #a6e3a1;
                font-size: 10pt;
                font-weight: bold;
                background: transparent;
            """)
        else:
            self.start_btn.setText("▶️ 시작")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #a6e3a1, stop:1 #94e2d5);
                    color: #1e1e2e;
                    border: none;
                    padding: 10px 24px;
                    border-radius: 10px;
                    font-weight: bold;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #94e2d5, stop:1 #89dceb);
                }
            """)
            # Reset status indicator
            self.status_dot.stop_pulsing()
            self.status_dot.set_color("#6c7086")
            self.status_text.setText("대기 중")
            self.status_text.setStyleSheet("""
                color: #a6adc8;
                font-size: 10pt;
                background: transparent;
            """)

        self.tray_icon.set_monitoring_state(is_running)

    def on_status_update(self, status: str):
        self.status_bar.showMessage(status)
        # Update header status based on activity
        if "검색 중" in status or "스크래핑" in status:
            self.status_text.setText("검색 중...")
            self.status_dot.set_color("#f9e2af")
        elif "초기화" in status:
            self.status_text.setText("초기화 중...")
            self.status_dot.set_color("#89b4fa")
        elif "다음 검색까지" in status:
            self.status_text.setText("모니터링 중")
            self.status_dot.set_color("#a6e3a1")
            # Update last search time
            from datetime import datetime
            self.last_search_label.setText(f"마지막 검색: {datetime.now().strftime('%H:%M:%S')}")

    def on_new_item(self, item):
        # Skip NOTIFICATIONS during initial crawl, but still update UI
        skip_notification = hasattr(self.engine, 'is_first_run') and self.engine.is_first_run

        if not skip_notification:
            self.tray_icon.show_notification(
                f"🆕 새 상품 - {item.platform}",
                f"{item.title}\n{item.price}"
            )

        self._mark_live_data_dirty(reason="new_item")

    def on_price_change(self, item, old_price: str, new_price: str):
        if hasattr(self.engine, 'is_first_run') and self.engine.is_first_run:
            self._mark_live_data_dirty(reason="price_change")
            return
        self.tray_icon.show_notification(
            "💰 가격 변동",
            f"{item.title}\n{old_price} → {new_price}"
        )
        self._mark_live_data_dirty(reason="price_change")

    def on_error(self, error: str):
        self.status_bar.showMessage(f"⚠️ 오류: {error}")
        self.status_text.setText("오류 발생")
        self.status_dot.setStyleSheet("color: #f38ba8; font-size: 10pt; background: transparent;")

    def open_settings(self):
        dialog = SettingsDialog(self.settings_manager, self)
        if dialog.exec():
            # SettingsDialog.save_settings() already persists via SettingsManager.save().
            self.settings_manager.save()

            # Apply theme
            self.apply_theme()

            # Update keywords
            self.keyword_widget.refresh_list()

            # Restart if running
            if self.monitor_thread and self.monitor_thread.isRunning():
                self.stop_monitoring()
                self.start_monitoring()


__all__ = ["MonitoringMixin"]
