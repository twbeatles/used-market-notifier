# pyright: reportAttributeAccessIssue=false
"""Coalesced live-data refresh for stats/listings tabs."""

from PyQt6.QtWidgets import QWidget


class LiveRefreshMixin(QWidget):
    """Marks live data dirty and flushes it for the visible tab."""

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
        if not hasattr(self, "tabs") or not self.tabs:
            return
        current = self.tabs.currentIndex()

        if self._live_data_dirty.get("listings") and (force or current == 1):
            try:
                self.listings_widget.refresh_listings(force=True)
                self._live_data_dirty["listings"] = False
            except Exception:
                pass

        if self._live_data_dirty.get("stats") and (force or current == 2):
            try:
                self.stats_widget.refresh_stats(force=True)
                self._live_data_dirty["stats"] = False
            except Exception:
                pass

    def _on_tab_changed(self, index: int):
        self._flush_live_data_refresh(force=False)

    def refresh_current_tab(self):
        """Refresh data in current tab"""
        current = self.tabs.currentWidget()
        if current is None:
            self.status_bar.showMessage("새로고침 완료")
            return
        refresh_listings = getattr(current, "refresh_listings", None)
        refresh_stats = getattr(current, "refresh_stats", None)
        refresh_list = getattr(current, "refresh_list", None)
        refresh = getattr(current, "refresh", None)

        if callable(refresh_listings):
            refresh_listings(force=True)
        elif callable(refresh_stats):
            refresh_stats(force=True)
        elif callable(refresh_list):
            refresh_list()
        elif callable(refresh):
            refresh()
        self.status_bar.showMessage("새로고침 완료")


__all__ = ["LiveRefreshMixin"]
