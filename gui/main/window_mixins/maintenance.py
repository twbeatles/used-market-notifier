# pyright: reportAttributeAccessIssue=false
"""Startup maintenance: auto-cleanup thread and auto-backup check."""

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget

from gui.main.threads import MaintenanceCleanupThread


class MaintenanceMixin(QWidget):
    """Runs one-shot startup cleanup/backup after the UI is shown."""

    def _run_startup_maintenance(self):
        s = self.settings_manager.settings

        # Auto cleanup: run once on startup (user preference).
        if getattr(s, "auto_cleanup_enabled", False):
            try:
                # Prevent racing with monitoring start/clicks.
                if hasattr(self, "start_btn") and self.start_btn:
                    self.start_btn.setEnabled(False)
                self.status_bar.showMessage("🧹 오래된 매물 정리 중...")
                if hasattr(self, "log_widget") and self.log_widget:
                    self.log_widget.append_log("자동 클린업을 시작합니다...", "INFO")

                self._startup_cleanup_thread = MaintenanceCleanupThread(
                    db_path=s.db_path,
                    days=s.cleanup_days,
                    exclude_favorites=s.cleanup_exclude_favorites,
                    exclude_noted=s.cleanup_exclude_noted,
                )
                self._startup_cleanup_thread.completed.connect(self._on_startup_cleanup_done)
                self._startup_cleanup_thread.failed.connect(self._on_startup_cleanup_failed)
                self._startup_cleanup_thread.start()
                return
            except Exception as e:
                self._on_startup_cleanup_failed(str(e))

        # No cleanup, proceed with auto-start if enabled.
        if s.auto_start_monitoring:
            QTimer.singleShot(1000, self.start_monitoring)

    def _on_startup_cleanup_done(self, deleted_count: int):
        msg = f"🧹 클린업 완료: {deleted_count:,}개 삭제"
        self.status_bar.showMessage(msg)
        if hasattr(self, "log_widget") and self.log_widget:
            self.log_widget.append_log(msg, "INFO")

        # Existing engine connection may have cached stats.
        try:
            if hasattr(self, "engine") and self.engine and hasattr(self.engine, "db"):
                self.engine.db._invalidate_cache()
        except Exception:
            pass

        try:
            if hasattr(self, "stats_widget") and self.stats_widget:
                self.stats_widget.refresh_stats(force=True)
            if hasattr(self, "listings_widget") and self.listings_widget:
                self.listings_widget.refresh_listings(force=True)
            self._live_data_dirty = {"stats": False, "listings": False}
        except Exception:
            pass

        if hasattr(self, "start_btn") and self.start_btn:
            self.start_btn.setEnabled(True)

        if self.settings_manager.settings.auto_start_monitoring:
            QTimer.singleShot(500, self.start_monitoring)

    def _on_startup_cleanup_failed(self, error: str):
        msg = f"⚠️ 자동 클린업 실패: {error}"
        self.status_bar.showMessage(msg)
        if hasattr(self, "log_widget") and self.log_widget:
            self.log_widget.append_log(msg, "WARNING")
        if hasattr(self, "start_btn") and self.start_btn:
            self.start_btn.setEnabled(True)

        if self.settings_manager.settings.auto_start_monitoring:
            QTimer.singleShot(500, self.start_monitoring)

    def _check_auto_backup(self):
        """Check and create auto backup if needed"""
        try:
            backup_path = self.backup_manager.auto_backup_if_needed(
                max_age_days=self.settings_manager.settings.auto_backup_interval_days,
                db_path=self.settings_manager.settings.db_path
            )
            if backup_path:
                self.backup_manager.cleanup_old_backups(
                    keep_count=self.settings_manager.settings.backup_keep_count
                )
                print(f"Auto backup created: {backup_path}")
        except Exception as e:
            print(f"Auto backup failed: {e}")


__all__ = ["MaintenanceMixin"]
