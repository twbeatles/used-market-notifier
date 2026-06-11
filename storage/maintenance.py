# pyright: reportAttributeAccessIssue=false
"""MaintenanceMixin for DatabaseManager."""

from .common import *


class MaintenanceMixin:
    def add_search_history(self, keyword: str):
        """Add or update search history entry"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO search_history (keyword)
                VALUES (?)
                ON CONFLICT(keyword) DO UPDATE SET
                use_count = use_count + 1,
                last_used = CURRENT_TIMESTAMP
            ''', (keyword,))
            self.conn.commit()
            self._invalidate_cache()

    def get_search_history(self, limit: int = 10) -> list:
        """Get recent search keywords, ordered by last used"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT keyword, use_count, last_used
                FROM search_history
                ORDER BY last_used DESC
                LIMIT ?
            ''', (limit,))
            return [row['keyword'] for row in cursor.fetchall()]

    def clear_search_history(self):
        """Clear all search history"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM search_history')
            self.conn.commit()
            self._invalidate_cache()

    def get_cleanup_preview(self, days: int = 30,
                            exclude_favorites: bool = True,
                            exclude_noted: bool = True) -> dict:
        """Preview how many listings would be deleted"""
        with self.lock:
            cursor = self.conn.cursor()

            query = '''
                SELECT COUNT(*) as count FROM listings
                WHERE created_at < datetime('now', ?)
            '''
            params = [f'-{days} days']

            if exclude_favorites:
                query += ' AND id NOT IN (SELECT listing_id FROM favorites)'

            if exclude_noted:
                query += ' AND id NOT IN (SELECT listing_id FROM listing_notes)'

            cursor.execute(query, params)
            delete_count = cursor.fetchone()['count']

            # Get total count
            cursor.execute('SELECT COUNT(*) as count FROM listings')
            total_count = cursor.fetchone()['count']

            return {
                'delete_count': delete_count,
                'total_count': total_count,
                'days': days,
                'exclude_favorites': exclude_favorites,
                'exclude_noted': exclude_noted
            }

    def cleanup_old_listings(self, days: int = 30,
                             exclude_favorites: bool = True,
                             exclude_noted: bool = True) -> int:
        """Delete old listings and return count deleted"""
        with self.lock:
            cursor = self.conn.cursor()

            # First, delete related records
            subquery = '''
                SELECT id FROM listings
                WHERE created_at < datetime('now', ?)
            '''
            params = [f'-{days} days']

            if exclude_favorites:
                subquery += ' AND id NOT IN (SELECT listing_id FROM favorites)'

            if exclude_noted:
                subquery += ' AND id NOT IN (SELECT listing_id FROM listing_notes)'

            # Delete price history for these listings
            cursor.execute(f'''
                DELETE FROM price_history WHERE listing_id IN ({subquery})
            ''', params)

            # Delete notification logs for these listings
            cursor.execute(f'''
                DELETE FROM notification_log WHERE listing_id IN ({subquery})
            ''', params)

            cursor.execute(f'''
                DELETE FROM notification_delivery_log WHERE listing_id IN ({subquery})
            ''', params)

            cursor.execute(f'''
                DELETE FROM sale_status_history WHERE listing_id IN ({subquery})
            ''', params)

            cursor.execute(f'''
                DELETE FROM listing_auto_tags WHERE listing_id IN ({subquery})
            ''', params)

            cursor.execute(f'''
                DELETE FROM listing_notes WHERE listing_id IN ({subquery})
            ''', params)

            cursor.execute(f'''
                DELETE FROM favorites WHERE listing_id IN ({subquery})
            ''', params)

            # Delete the listings
            delete_query = f'''
                DELETE FROM listings WHERE id IN ({subquery})
            '''
            cursor.execute(delete_query, params)
            deleted_count = cursor.rowcount

            self.conn.commit()
            self._invalidate_cache()
            return deleted_count

    def add_auto_tags(self, listing_id: int, tags: list):
        """Add or update auto-generated tags for a listing"""
        with self.lock:
            cursor = self.conn.cursor()
            normalized = sorted({str(tag).strip() for tag in tags if str(tag).strip()})
            cursor.execute('DELETE FROM listing_auto_tags WHERE listing_id = ?', (listing_id,))
            if normalized:
                cursor.executemany(
                    '''
                    INSERT INTO listing_auto_tags (listing_id, tag_name)
                    VALUES (?, ?)
                    ''',
                    [(listing_id, tag_name) for tag_name in normalized],
                )
            self.conn.commit()
            self._invalidate_cache()

    def get_auto_tags(self, listing_id: int) -> list:
        """Get auto-generated tags for a listing"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                '''
                SELECT tag_name
                FROM listing_auto_tags
                WHERE listing_id = ?
                ORDER BY tag_name
                ''',
                (listing_id,),
            )
            return [str(row['tag_name']) for row in cursor.fetchall()]

    def get_listings_for_export(
        self,
        platform: str | None = None,
        search: str | None = None,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        include_sold: bool = True,
    ) -> list:
        """Get listings with all filters for export"""
        with self.lock:
            cursor = self.conn.cursor()
            query = '''
                SELECT l.*,
                       COALESCE(ln.note, '') as note,
                       COALESCE(ln.status_tag, '') as user_status,
                       COALESCE(
                           (
                               SELECT json_group_array(tag_name)
                               FROM (
                                   SELECT tag_name
                                   FROM listing_auto_tags lat
                                   WHERE lat.listing_id = l.id
                                   ORDER BY tag_name
                               )
                           ),
                           '[]'
                       ) as auto_tags
                FROM listings l
                LEFT JOIN listing_notes ln ON l.id = ln.listing_id
                WHERE 1=1
            '''
            params = []

            if platform and platform != 'all':
                query += ' AND l.platform = ?'
                params.append(platform)

            if search:
                query += ' AND l.title LIKE ?'
                params.append(f'%{search}%')

            if status and status != 'all':
                query += ' AND l.sale_status = ?'
                params.append(status)

            if not include_sold:
                query += ' AND l.sale_status != ?'
                params.append('sold')

            if date_from:
                query += ' AND l.created_at >= ?'
                params.append(date_from)

            if date_to:
                query += ' AND l.created_at <= ?'
                params.append(date_to)

            query += ' ORDER BY l.created_at DESC'

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
