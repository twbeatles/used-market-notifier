# pyright: reportAttributeAccessIssue=false
"""StatisticsMixin for DatabaseManager."""

from .common import *


class StatisticsMixin:
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

    def get_total_listings(self) -> int:
        """Get total number of listings"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM listings')
            return cursor.fetchone()[0]

    def get_listings_paginated(self, platform: str | None = None, search: str | None = None,
                                limit: int = 50, offset: int = 0) -> list:
        """Get listings with pagination and filtering"""
        with self.lock:
            cursor = self.conn.cursor()
            query = 'SELECT * FROM listings WHERE 1=1'
            params = []

            if platform:
                query += ' AND platform = ?'
                params.append(platform)

            if search:
                query += ' AND title LIKE ?'
                params.append(f'%{search}%')

            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_listings_count(
        self,
        platform: str | None = None,
        search: str | None = None,
        status: str | None = None,
    ) -> int:
        """Get total count of listings with filters (platform/title/sale_status)"""
        with self.lock:
            cursor = self.conn.cursor()
            query = 'SELECT COUNT(*) FROM listings WHERE 1=1'
            params = []

            if platform:
                query += ' AND platform = ?'
                params.append(platform)

            if status and status != "all":
                query += ' AND sale_status = ?'
                params.append(status)

            if search:
                query += ' AND title LIKE ?'
                params.append(f'%{search}%')

            cursor.execute(query, params)
            return cursor.fetchone()[0]

    def get_listings_by_platform(self) -> dict:
        """Get listing count by platform"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT platform, COUNT(*) as count
                FROM listings
                GROUP BY platform
            ''')
            return {row['platform']: row['count'] for row in cursor.fetchall()}

    def get_listings_by_keyword(self) -> dict:
        """Get listing count by keyword"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT keyword, COUNT(*) as count
                FROM listings
                GROUP BY keyword
                ORDER BY count DESC
            ''')
            return {row['keyword']: row['count'] for row in cursor.fetchall()}

    def get_keyword_price_stats(self) -> list:
        """Get price statistics by keyword (min, avg, max)"""
        with self.lock:
            cursor = self.conn.cursor()
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
            return [dict(row) for row in cursor.fetchall()]

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

    def get_recent_listings(self, limit: int = 20) -> list:
        """Get most recent listings"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM listings
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_status_counts(self) -> dict:
        """Get count of listings by sale status"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT sale_status, COUNT(*) as count
                FROM listings
                GROUP BY sale_status
            ''')
            return {row['sale_status'] or 'for_sale': row['count'] for row in cursor.fetchall()}

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
