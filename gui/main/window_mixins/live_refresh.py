# pyright: reportAttributeAccessIssue=false
"""Coalesced live-data refresh for stats/listings pages."""

import contextlib

from PySide6.QtWidgets import QWidget


class LiveRefreshMixin(QWidget):
    """Marks live data dirty and flushes it for the visible page."""

    def _mark_live_data_dirty(self, reason: str = ""):
        self._live_data_dirty["stats"] = True
        self._live_data_dirty["listings"] = True
        self._ui_refresh_request_count += 1
        if self._ui_refresh_request_count % 20 == 0 and hasattr(self, "log_widget") and self.log_widget:
            self.log_widget.append_log(
                f"[perf] UI refresh requests={self._ui_refresh_request_count}, reason={reason or 'event'}",
                "INFO",
            )
        if not self._ui_refresh_timer.isActive():
            self._ui_refresh_timer.start(400)

    def _flush_live_data_refresh(self, force: bool = False):
        current = self.stackedWidget.currentWidget()

        if self._live_data_dirty.get("listings") and (force or current is self.listings_page):
            with contextlib.suppress(Exception):
                self.listings_widget.refresh_listings(force=True)
                self._live_data_dirty["listings"] = False

        if self._live_data_dirty.get("stats") and (force or current is self.stats_page):
            with contextlib.suppress(Exception):
                self.stats_widget.refresh_stats(force=True)
                self._live_data_dirty["stats"] = False

    def _on_tab_changed(self, index: int):
        self._flush_live_data_refresh(force=False)

    def refresh_current_tab(self):
        """Refresh data in current page"""
        current = self.stackedWidget.currentWidget()
        if current is None:
            self.publish_status("새로고침 완료")
            return
        content = getattr(current, "content", current)
        refresh_listings = getattr(content, "refresh_listings", None)
        refresh_stats = getattr(content, "refresh_stats", None)
        refresh_list = getattr(content, "refresh_list", None)
        refresh = getattr(content, "refresh", None)

        if callable(refresh_listings):
            refresh_listings(force=True)
        elif callable(refresh_stats):
            refresh_stats(force=True)
        elif callable(refresh_list):
            refresh_list()
        elif callable(refresh):
            refresh()
        self.publish_status("새로고침 완료")


__all__ = ["LiveRefreshMixin"]
