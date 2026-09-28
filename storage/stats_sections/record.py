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

    def get_last_search_time(self, keyword: str, platforms: Optional[list[str]] = None) -> Optional[datetime]:
        """Get last search time for a keyword (naive UTC, as stored by CURRENT_TIMESTAMP).

        ``platforms`` limits the lookup to those platforms; the oldest of their latest
        search times is returned so every platform of the keyword is due together.
        """
        with self.lock:
            cursor = self.conn.cursor()
            if platforms:
                placeholders = ",".join("?" for _ in platforms)
                cursor.execute(
                    f'''
                    SELECT MIN(last_checked) FROM (
                        SELECT MAX(checked_at) AS last_checked FROM search_stats
                        WHERE keyword = ? AND platform IN ({placeholders})
                        GROUP BY platform
                    )
                    ''',
                    (keyword, *platforms),
                )
            else:
                cursor.execute('''
                    SELECT MAX(checked_at) FROM search_stats WHERE keyword = ?
                ''', (keyword,))
            row = cursor.fetchone()
            if row and row[0]:
                return datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
            return None


__all__ = ["StatsRecordMixin"]
