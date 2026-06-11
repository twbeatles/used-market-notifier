# pyright: reportAttributeAccessIssue=false
"""FavoritesNotesMixin for DatabaseManager."""

from .common import *


class FavoritesNotesMixin:
    def add_favorite(self, listing_id: int, notes: str = "", target_price: int | None = None) -> bool:
        """Add a listing to favorites"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO favorites (listing_id, notes, target_price)
                    VALUES (?, ?, ?)
                ''', (listing_id, notes, target_price))
                self.conn.commit()
                self._invalidate_cache()
                return True
            except sqlite3.IntegrityError:
                return False

    def update_favorite(
        self,
        listing_id: int,
        notes: str | None = None,
        target_price: int | None | object = _UNSET,
    ) -> bool:
        """Update favorite details"""
        with self.lock:
            cursor = self.conn.cursor()
            updates = []
            params = []
            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)
            if target_price is not _UNSET:
                updates.append("target_price = ?")
                params.append(target_price)

            if not updates:
                return False

            params.append(listing_id)
            cursor.execute(f'''
                UPDATE favorites SET {", ".join(updates)} WHERE listing_id = ?
            ''', tuple(params))
            self.conn.commit()
            self._invalidate_cache()
            return cursor.rowcount > 0

    def remove_favorite(self, listing_id: int):
        """Remove a listing from favorites"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM favorites WHERE listing_id = ?', (listing_id,))
            self.conn.commit()
            self._invalidate_cache()

    def is_favorite(self, listing_id: int) -> bool:
        """Check if a listing is in favorites"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT 1 FROM favorites WHERE listing_id = ?', (listing_id,))
            return cursor.fetchone() is not None

    def get_favorite_details(self, listing_id: int) -> Optional[dict]:
        """Get favorite details (notes, target_price)"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT notes, target_price FROM favorites WHERE listing_id = ?', (listing_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_favorites(self) -> list:
        """Get all favorite listings with details"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT l.*, f.notes, f.target_price, f.added_at as fav_added_at
                FROM favorites f
                JOIN listings l ON f.listing_id = l.id
                ORDER BY f.added_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def add_listing_note(self, listing_id: int, note: str = "", status_tag: str = "interested") -> bool:
        """Add or update a note for a listing"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO listing_notes (listing_id, note, status_tag)
                    VALUES (?, ?, ?)
                    ON CONFLICT(listing_id) DO UPDATE SET
                    note = excluded.note,
                    status_tag = excluded.status_tag,
                    updated_at = CURRENT_TIMESTAMP
                ''', (listing_id, note, status_tag))
                self.conn.commit()
                self._invalidate_cache()
                return True
            except Exception:
                return False

    def get_listing_note(self, listing_id: int) -> Optional[dict]:
        """Get note for a listing"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT note, status_tag, created_at, updated_at
                FROM listing_notes
                WHERE listing_id = ?
            ''', (listing_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_listing_note(self, listing_id: int):
        """Delete a listing note"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM listing_notes WHERE listing_id = ?', (listing_id,))
            self.conn.commit()
            self._invalidate_cache()

    def get_listings_with_notes(self) -> list:
        """Get all listings that have notes"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT l.*, ln.note, ln.status_tag,
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
                       ) as auto_tags,
                       ln.updated_at as note_updated
                FROM listing_notes ln
                JOIN listings l ON ln.listing_id = l.id
                ORDER BY ln.updated_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
