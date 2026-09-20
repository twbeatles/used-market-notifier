# pyright: reportAttributeAccessIssue=false
"""Price-change history queries (StatisticsMixin part)."""

from ..common import *


class StatsPriceMixin:
    def get_price_changes(self, days: int = 7) -> list:
        """Get recent price changes"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT
                    l.platform, l.article_id, l.title, l.url, l.thumbnail,
                    ph.old_price, ph.new_price, ph.changed_at
                FROM price_history ph
                JOIN listings l ON ph.listing_id = l.id
                WHERE ph.changed_at >= datetime('now', ?)
                ORDER BY ph.changed_at DESC
                LIMIT 50
            ''', (f'-{days} days',))
            return [dict(row) for row in cursor.fetchall()]


__all__ = ["StatsPriceMixin"]
