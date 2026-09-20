# pyright: reportAttributeAccessIssue=false
"""Search-event recording and lookup (StatisticsMixin part)."""

from ..common import *


class StatsRecordMixin:
    def record_search_stats(self, keyword: str, platform: str, items_found: int, new_items: int):
        """Record search statistics"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO search_stats (keyword, platform, items_found, new_items)
                VALUES (?, ?, ?, ?)
            ''', (keyword, platform, items_found, new_items))
            self.conn.commit()
            self._invalidate_cache()

    def get_last_search_time(self, keyword: str) -> Optional[datetime]:
        """Get last search time for a keyword"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT MAX(checked_at) FROM search_stats WHERE keyword = ?
            ''', (keyword,))
            row = cursor.fetchone()
            if row and row[0]:
                return datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
            return None


__all__ = ["StatsRecordMixin"]
