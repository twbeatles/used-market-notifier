# pyright: reportAttributeAccessIssue=false
"""Dashboard snapshot and sale-status history (StatisticsMixin part)."""

from ..common import *


class StatsDashboardMixin:
    def get_dashboard_snapshot(
        self,
        recent_limit: int = 20,
        price_change_limit: int = 20,
        price_change_days: int = 20,
        daily_days: int = 7,
    ) -> dict:
        """
        Get dashboard statistics in one call.
        Uses TTL cache to avoid repeated read bursts from the UI.
        """
        cache_key = f"dashboard:{recent_limit}:{price_change_limit}:{price_change_days}:{daily_days}"
        now = datetime.now()

        with self.lock:
            if (
                self._cache_time is not None
                and (now - self._cache_time).total_seconds() < self._cache_ttl
                and cache_key in self._stats_cache
            ):
                return self._stats_cache[cache_key]

            cursor = self.conn.cursor()

            cursor.execute('SELECT COUNT(*) as count FROM listings')
            total = cursor.fetchone()['count']

            cursor.execute('''
                SELECT platform, COUNT(*) as count
                FROM listings
                GROUP BY platform
            ''')
            by_platform = {row['platform']: row['count'] for row in cursor.fetchall()}

            cursor.execute('''
                SELECT * FROM listings
                ORDER BY created_at DESC
                LIMIT ?
            ''', (recent_limit,))
            recent = [dict(row) for row in cursor.fetchall()]

            cursor.execute('''
                SELECT
                    l.platform, l.article_id, l.title, l.url, l.thumbnail,
                    ph.old_price, ph.new_price, ph.changed_at
                FROM price_history ph
                JOIN listings l ON ph.listing_id = l.id
                WHERE ph.changed_at >= datetime('now', ?)
                ORDER BY ph.changed_at DESC
                LIMIT ?
            ''', (f'-{price_change_days} days', price_change_limit))
            price_changes = [dict(row) for row in cursor.fetchall()]

            cursor.execute('''
                SELECT
                    keyword,
                    COUNT(*) as count,
                    MIN(price_numeric) as min_price,
                    CAST(AVG(price_numeric) as INTEGER) as avg_price,
                    MAX(price_numeric) as max_price
                FROM listings
                WHERE price_numeric > 0
                GROUP BY keyword
                ORDER BY count DESC
            ''')
            analysis = [dict(row) for row in cursor.fetchall()]

            cursor.execute('''
                SELECT
                    DATE(checked_at) as date,
                    SUM(items_found) as items_found,
                    SUM(new_items) as new_items
                FROM search_stats
                WHERE checked_at >= datetime('now', ?)
                GROUP BY DATE(checked_at)
                ORDER BY date
            ''', (f'-{daily_days} days',))
            daily = [dict(row) for row in cursor.fetchall()]

            cursor.execute(
                '''
                SELECT
                    l.platform,
                    l.title,
                    ssh.old_status,
                    ssh.new_status,
                    ssh.changed_at,
                    l.url
                FROM sale_status_history ssh
                JOIN listings l ON ssh.listing_id = l.id
                ORDER BY ssh.changed_at DESC
                LIMIT 20
                '''
            )
            status_history = [dict(row) for row in cursor.fetchall()]

            snapshot = {
                'total': total,
                'by_platform': by_platform,
                'recent': recent,
                'price_changes': price_changes,
                'analysis': analysis,
                'daily_stats': daily,
                'status_history': status_history,
            }
            self._stats_cache[cache_key] = snapshot
            self._cache_time = now
            return snapshot

    def get_status_history(self, limit: int = 20) -> list:
        """Get recent sale status changes."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                '''
                SELECT
                    l.platform,
                    l.title,
                    l.url,
                    ssh.old_status,
                    ssh.new_status,
                    ssh.changed_at
                FROM sale_status_history ssh
                JOIN listings l ON ssh.listing_id = l.id
                ORDER BY ssh.changed_at DESC
                LIMIT ?
                ''',
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]


__all__ = ["StatsDashboardMixin"]
