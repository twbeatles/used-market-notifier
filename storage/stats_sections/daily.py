# pyright: reportAttributeAccessIssue=false
"""Daily search-volume queries (StatisticsMixin part)."""

from ..common import *


class StatsDailyMixin:
    def get_daily_stats(self, days: int = 7) -> list:
        """Get daily statistics for the past N days"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT
                    DATE(checked_at) as date,
                    SUM(items_found) as items_found,
                    SUM(new_items) as new_items
                FROM search_stats
                WHERE checked_at >= datetime('now', ?)
                GROUP BY DATE(checked_at)
                ORDER BY date
            ''', (f'-{days} days',))
            return [dict(row) for row in cursor.fetchall()]


__all__ = ["StatsDailyMixin"]
