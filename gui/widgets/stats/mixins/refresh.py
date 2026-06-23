"""Mixin module: refresh."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFileDialog,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
)

from export_manager import ExportManager
from models import Item

from ....charts import DailyChart, PlatformChart
from ....components import StatCard
from ....link_utils import open_external_url


class StatsRefreshMixin:
    """Refresh behavior."""

    def _signature_recent(self, recent: list[dict]):
        return tuple(
            (item.get("id"), item.get("platform"), item.get("title"), item.get("price"), item.get("keyword"))
            for item in recent
        )


    def _signature_changes(self, changes: list[dict]):
        return tuple(
            (
                row.get("platform"),
                row.get("article_id"),
                row.get("title"),
                row.get("old_price"),
                row.get("new_price"),
                row.get("changed_at"),
            )
            for row in changes
        )


    def _signature_analysis(self, analysis: list[dict]):
        return tuple(
            (
                row.get("keyword"),
                row.get("count"),
                row.get("min_price"),
                row.get("avg_price"),
                row.get("max_price"),
            )
            for row in analysis
        )


    def _signature_status_history(self, history: list[dict]):
        return tuple(
            (
                row.get("platform"),
                row.get("title"),
                row.get("old_status"),
                row.get("new_status"),
                row.get("changed_at"),
            )
            for row in history
        )


    def refresh_stats(self, force: bool = False):
        """Refresh statistics."""
        db = None
        if self.engine and hasattr(self.engine, "db"):
            db = self.engine.db
        elif self._standalone_db:
            db = self._standalone_db
        if not db:
            return

        try:
            snap = db.get_dashboard_snapshot(
                recent_limit=20,
                price_change_limit=20,
                price_change_days=20,
                daily_days=7,
            )
            total = snap["total"]
            by_platform = snap["by_platform"]
            recent = snap["recent"]
            changes = snap["price_changes"]
            analysis = snap["analysis"]
            daily_stats = snap["daily_stats"]
            status_history = snap.get("status_history", [])

            self.total_card.set_value(str(total))
            self.danggeun_card.set_value(str(by_platform.get("danggeun", 0)))
            self.bunjang_card.set_value(str(by_platform.get("bunjang", 0)))
            self.joonggonara_card.set_value(str(by_platform.get("joonggonara", 0)))

            recent_sig = self._signature_recent(recent)
            if force or recent_sig != self._last_recent_signature:
                self.recent_table.setRowCount(len(recent))
                for row_index, item in enumerate(recent):
                    platform_item = QTableWidgetItem(item.get("platform", ""))
                    platform_item.setData(Qt.ItemDataRole.UserRole, item.get("url"))
                    platform_item.setData(Qt.ItemDataRole.UserRole + 1, item.get("id"))
                    platform_item.setData(Qt.ItemDataRole.UserRole + 2, item.get("seller"))
                    platform_item.setData(Qt.ItemDataRole.UserRole + 3, item.get("platform"))
                    self.recent_table.setItem(row_index, 0, platform_item)
                    self.recent_table.setItem(row_index, 1, QTableWidgetItem(item.get("title", "")))
                    self.recent_table.setItem(row_index, 2, QTableWidgetItem(item.get("price", "")))
                    self.recent_table.setItem(row_index, 3, QTableWidgetItem(item.get("keyword", "")))
                    created = item.get("created_at", "")
                    self.recent_table.setItem(
                        row_index,
                        4,
                        QTableWidgetItem(created[11:16] if len(created) > 16 else created),
                    )
                self._last_recent_signature = recent_sig

            changes_sig = self._signature_changes(changes)
            if force or changes_sig != self._last_changes_signature:
                self.price_table.setRowCount(len(changes))
                for row_index, change in enumerate(changes):
                    title_item = QTableWidgetItem(change.get("title", "")[:40])
                    title_item.setData(Qt.ItemDataRole.UserRole, change.get("url"))
                    self.price_table.setItem(row_index, 0, title_item)
                    self.price_table.setItem(row_index, 1, QTableWidgetItem(str(change.get("old_price", ""))))
                    self.price_table.setItem(row_index, 2, QTableWidgetItem(str(change.get("new_price", ""))))
                    changed_at = change.get("changed_at", "")
                    self.price_table.setItem(
                        row_index,
                        3,
                        QTableWidgetItem(changed_at[11:16] if len(changed_at) > 16 else changed_at),
                    )
                self._last_changes_signature = changes_sig

            analysis_sig = self._signature_analysis(analysis)
            if force or analysis_sig != self._last_analysis_signature:
                self.analysis_table.setRowCount(len(analysis))
                for row_index, row in enumerate(analysis):
                    self.analysis_table.setItem(row_index, 0, QTableWidgetItem(row.get("keyword", "")))
                    self.analysis_table.setItem(row_index, 1, QTableWidgetItem(str(row.get("count", 0))))
                    min_p = row.get("min_price", 0)
                    avg_p = row.get("avg_price", 0)
                    max_p = row.get("max_price", 0)
                    self.analysis_table.setItem(
                        row_index,
                        2,
                        QTableWidgetItem(f"{min_p:,}원" if min_p else "-"),
                    )
                    self.analysis_table.setItem(
                        row_index,
                        3,
                        QTableWidgetItem(f"{avg_p:,}원" if avg_p else "-"),
                    )
                    self.analysis_table.setItem(
                        row_index,
                        4,
                        QTableWidgetItem(f"{max_p:,}원" if max_p else "-"),
                    )
                self._last_analysis_signature = analysis_sig

            status_sig = self._signature_status_history(status_history)
            if force or status_sig != self._last_status_signature:
                self.status_history_table.setRowCount(len(status_history))
                for row_index, row in enumerate(status_history):
                    platform_item = QTableWidgetItem(row.get("platform", ""))
                    platform_item.setData(Qt.ItemDataRole.UserRole, row.get("url"))
                    self.status_history_table.setItem(row_index, 0, platform_item)
                    self.status_history_table.setItem(row_index, 1, QTableWidgetItem(row.get("title", "")))
                    self.status_history_table.setItem(
                        row_index, 2, QTableWidgetItem(str(row.get("old_status", "")))
                    )
                    self.status_history_table.setItem(
                        row_index, 3, QTableWidgetItem(str(row.get("new_status", "")))
                    )
                    self.status_history_table.setItem(
                        row_index, 4, QTableWidgetItem(row.get("changed_at", ""))
                    )
                self._last_status_signature = status_sig

            platform_sig = tuple(sorted(by_platform.items()))
            daily_sig = tuple((row.get("date"), row.get("items_found"), row.get("new_items")) for row in daily_stats)
            if force or platform_sig != self._last_platform_signature:
                self.platform_chart.update_chart(by_platform)
                self._last_platform_signature = platform_sig
            if force or daily_sig != self._last_daily_signature:
                self.daily_chart.update_chart(daily_stats)
                self._last_daily_signature = daily_sig
            self._pending_refresh = False
        except Exception as e:
            print(f"Error refreshing stats: {e}")
            import traceback

            traceback.print_exc()
