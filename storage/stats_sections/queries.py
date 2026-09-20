# pyright: reportAttributeAccessIssue=false
"""Listing/aggregate read queries (StatisticsMixin part)."""

from ..common import *


class StatsQueryMixin:
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


__all__ = ["StatsQueryMixin"]
