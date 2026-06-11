# pyright: reportAttributeAccessIssue=false
"""SellerFilterMixin for DatabaseManager."""

from .common import *


class SellerFilterMixin:
    def add_seller_filter(self, seller_name: str, platform: str, is_blocked: bool = True, notes: str = ""):
        """Add or update a seller filter"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO seller_filters (seller_name, platform, is_blocked, notes)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(seller_name, platform) DO UPDATE SET
                is_blocked=excluded.is_blocked,
                notes=excluded.notes,
                created_at=CURRENT_TIMESTAMP
            ''', (seller_name, platform, is_blocked, notes))
            self.conn.commit()
            self._invalidate_cache()

    def remove_seller_filter(self, seller_name: str, platform: str):
        """Remove a seller filter"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                DELETE FROM seller_filters
                WHERE seller_name = ? AND platform = ?
            ''', (seller_name, platform))
            self.conn.commit()
            self._invalidate_cache()

    def get_blocked_sellers(self) -> list:
        """Get list of blocked sellers"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT seller_name, platform, created_at
                FROM seller_filters
                WHERE is_blocked = 1
                ORDER BY created_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def get_seller_filters(self) -> list:
        """Get all seller filters"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM seller_filters ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]
