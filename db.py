# db.py
"""Enhanced database manager with price tracking and statistics"""

import difflib
import json
import logging
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Any, Optional

from models import Item, FavoriteItem, NotificationLog, SellerFilter


_UNSET = object()



class DatabaseManager:
    """SQLite database manager with price history tracking - Thread Safe"""

    PRICE_PARSE_VERSION = 2

    def __init__(self, db_path: str = "listings.db"):
        self.db_path = db_path
        # check_same_thread=False allowed but we handle locking manually
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        self.logger = logging.getLogger("DatabaseManager")
        
        # Stats cache with TTL (reduce redundant queries)
        self._stats_cache = {}
        self._cache_ttl = 30  # 30 seconds cache
        self._cache_time = None
        
        # Enable WAL mode and other optimizations for better concurrency
        self.conn.execute('PRAGMA foreign_keys=ON')
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.execute('PRAGMA synchronous=NORMAL')  # Faster writes
        self.conn.execute('PRAGMA cache_size=-64000')  # 64MB cache
        self.create_tables()
    
    def _invalidate_cache(self):
        """Invalidate stats cache on write operations"""
        self._cache_time = None
        self._stats_cache = {}
    
    def create_tables(self):
        """Create all required tables"""
        with self.lock:
            cursor = self.conn.cursor()
            
            # Main listings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    article_id TEXT NOT NULL,
                    keyword TEXT,
                    title TEXT,
                    price TEXT,
                    price_numeric INTEGER DEFAULT 0,
                    url TEXT,
                    thumbnail TEXT,
                    seller TEXT,
                    location TEXT,
                    sale_status TEXT DEFAULT 'for_sale',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(platform, article_id)
                )
            ''')
            
            # Price history table for tracking changes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id INTEGER NOT NULL,
                    old_price TEXT,
                    old_price_numeric INTEGER,
                    new_price TEXT,
                    new_price_numeric INTEGER,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (listing_id) REFERENCES listings(id)
                )
            ''')
            
            # Search Statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    items_found INTEGER DEFAULT 0,
                    new_items INTEGER DEFAULT 0,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Favorites table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id INTEGER NOT NULL UNIQUE,
                    notes TEXT,
                    target_price INTEGER,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (listing_id) REFERENCES listings(id)
                )
            ''')

            # Notification Log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id INTEGER NOT NULL,
                    notification_type TEXT NOT NULL,
                    message_preview TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT 0,
                    FOREIGN KEY (listing_id) REFERENCES listings(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_delivery_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id INTEGER NOT NULL,
                    notification_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempt INTEGER DEFAULT 1,
                    error_message TEXT,
                    rate_limited BOOLEAN DEFAULT 0,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (listing_id) REFERENCES listings(id)
                )
            ''')

            # Seller Filter table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS seller_filters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    seller_name TEXT NOT NULL,
                    platform TEXT,
                    is_blocked BOOLEAN DEFAULT 1,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(seller_name, platform)
                )
            ''')
            
            # Create indexes for better query performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_listings_platform ON listings(platform)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_listings_keyword ON listings(keyword)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_listings_created ON listings(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_listing ON price_history(listing_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_search_stats_date ON search_stats(checked_at)')
            # Composite index for duplicate checking (most frequent query)
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_listings_platform_article ON listings(platform, article_id)')
            # Additional indexes for new features
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_favorites_listing ON favorites(listing_id)')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_search_stats_keyword_checked '
                'ON search_stats(keyword, checked_at DESC)'
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_price_history_changed_at '
                'ON price_history(changed_at DESC)'
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_notification_log_sent_at '
                'ON notification_log(sent_at DESC)'
            )
            
            # Search history table for keyword suggestions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL UNIQUE,
                    use_count INTEGER DEFAULT 1,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Meta table for one-time migrations / feature flags
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')

            # Listing notes table for user annotations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listing_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id INTEGER NOT NULL UNIQUE,
                    note TEXT,
                    status_tag TEXT DEFAULT 'interested',
                    auto_tags TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (listing_id) REFERENCES listings(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listing_auto_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id INTEGER NOT NULL,
                    tag_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(listing_id, tag_name),
                    FOREIGN KEY (listing_id) REFERENCES listings(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sale_status_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id INTEGER NOT NULL,
                    old_status TEXT,
                    new_status TEXT NOT NULL,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (listing_id) REFERENCES listings(id)
                )
            ''')
            
            # Index for listing_notes (created after table exists)
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_listing_notes_listing ON listing_notes(listing_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_listing_auto_tags_listing ON listing_auto_tags(listing_id)')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_sale_status_history_listing_changed '
                'ON sale_status_history(listing_id, changed_at DESC)'
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_notification_delivery_log_sent_at '
                'ON notification_delivery_log(sent_at DESC)'
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_notification_delivery_log_type_sent_at '
                'ON notification_delivery_log(notification_type, sent_at DESC)'
            )
            
            # Migration: Add sale_status column if not exists (for existing databases)
            try:
                cursor.execute('ALTER TABLE listings ADD COLUMN sale_status TEXT DEFAULT "for_sale"')
            except Exception:
                pass  # Column already exists

            # Index for sale_status (must be created after column exists for older DBs)
            try:
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_listings_sale_status ON listings(sale_status)')
            except Exception:
                pass
            try:
                cursor.execute(
                    'CREATE INDEX IF NOT EXISTS idx_listings_status_platform_created '
                    'ON listings(sale_status, platform, created_at DESC)'
                )
            except Exception:
                pass

            # Migration: Add price_numeric column if not exists (older DBs)
            try:
                cursor.execute('ALTER TABLE listings ADD COLUMN price_numeric INTEGER DEFAULT 0')
            except Exception:
                pass

            # Migration: Add numeric columns in price_history if not exists (older DBs)
            try:
                cursor.execute('ALTER TABLE price_history ADD COLUMN old_price_numeric INTEGER')
            except Exception:
                pass
            try:
                cursor.execute('ALTER TABLE price_history ADD COLUMN new_price_numeric INTEGER')
            except Exception:
                pass

            # Migration: Add auto_tags column if not exists
            try:
                cursor.execute('ALTER TABLE listing_notes ADD COLUMN auto_tags TEXT DEFAULT "[]"')
            except Exception:
                pass  # Column already exists
            
            self.conn.commit()

            # One-time migration: recompute numeric prices with the current parser.
            try:
                self._migrate_price_parse_version(cursor)
            except Exception as e:
                self.logger.warning(f"Price parse migration skipped/failed: {e}")
            try:
                self._migrate_auto_tags_table(cursor)
            except Exception as e:
                self.logger.warning(f"Auto-tag migration skipped/failed: {e}")

    def _get_meta(self, cursor: sqlite3.Cursor, key: str) -> Optional[str]:
        cursor.execute("SELECT value FROM meta WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None

    def _set_meta(self, cursor: sqlite3.Cursor, key: str, value: str) -> None:
        cursor.execute(
            '''
            INSERT INTO meta (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            ''',
            (key, value),
        )

    def _migrate_price_parse_version(self, cursor: sqlite3.Cursor) -> None:
        """
        Recompute numeric price columns when the parsing logic changes.
        This is intentionally best-effort and runs once per DB.
        """
        key = "price_parse_version"
        current = 0
        raw = self._get_meta(cursor, key)
        if raw is not None:
            try:
                current = int(str(raw).strip() or "0")
            except Exception:
                current = 0

        if current >= self.PRICE_PARSE_VERSION:
            return

        from price_utils import parse_price_kr

        self.logger.info(
            f"Recomputing numeric prices (version {current} -> {self.PRICE_PARSE_VERSION})..."
        )

        # listings.price_numeric
        cursor.execute("SELECT id, price FROM listings")
        batch = []
        updated = 0
        while True:
            rows = cursor.fetchmany(500)
            if not rows:
                break
            for row in rows:
                batch.append((parse_price_kr(row["price"]), row["id"]))
            cursor.executemany("UPDATE listings SET price_numeric = ? WHERE id = ?", batch)
            self.conn.commit()
            updated += len(batch)
            batch.clear()

        # price_history numeric columns (best effort; table may be empty)
        try:
            cursor.execute("SELECT id, old_price, new_price FROM price_history")
            ph_batch = []
            ph_updated = 0
            while True:
                rows = cursor.fetchmany(500)
                if not rows:
                    break
                for row in rows:
                    ph_batch.append(
                        (parse_price_kr(row["old_price"]), parse_price_kr(row["new_price"]), row["id"])
                    )
                cursor.executemany(
                    "UPDATE price_history SET old_price_numeric = ?, new_price_numeric = ? WHERE id = ?",
                    ph_batch,
                )
                self.conn.commit()
                ph_updated += len(ph_batch)
                ph_batch.clear()
        except Exception:
            # Older DBs might not have this table or the numeric columns even after ALTER attempts.
            ph_updated = 0

        self._set_meta(cursor, key, str(self.PRICE_PARSE_VERSION))
        self.conn.commit()
        self.logger.info(
            f"Numeric price migration complete. listings updated={updated}, price_history updated={ph_updated}."
        )

    def _migrate_auto_tags_table(self, cursor: sqlite3.Cursor) -> None:
        """Move legacy listing_notes.auto_tags JSON into listing_auto_tags once."""
        key = "auto_tags_table_migrated_v1"
        if self._get_meta(cursor, key) == "1":
            return

        cursor.execute("SELECT listing_id, note, status_tag, auto_tags FROM listing_notes")
        rows = cursor.fetchall()
        for row in rows:
            listing_id = row["listing_id"]
            raw_tags = row["auto_tags"]
            tags: list[str] = []
            if raw_tags:
                try:
                    parsed = json.loads(raw_tags)
                    if isinstance(parsed, list):
                        tags = [str(tag).strip() for tag in parsed if str(tag).strip()]
                except Exception:
                    tags = []

            for tag_name in tags:
                cursor.execute(
                    '''
                    INSERT INTO listing_auto_tags (listing_id, tag_name)
                    VALUES (?, ?)
                    ON CONFLICT(listing_id, tag_name) DO NOTHING
                    ''',
                    (listing_id, tag_name),
                )

            note = str(row["note"] or "").strip()
            status_tag = str(row["status_tag"] or "interested").strip() or "interested"
            if tags and not note and status_tag == "interested":
                cursor.execute("DELETE FROM listing_notes WHERE listing_id = ?", (listing_id,))

        self._set_meta(cursor, key, "1")
        self.conn.commit()
    
    def is_duplicate(self, platform: str, article_id: str) -> bool:
        """Check if listing already exists"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                'SELECT 1 FROM listings WHERE platform = ? AND article_id = ?', 
                (platform, article_id)
            )
            return cursor.fetchone() is not None
    
    def get_listing_by_id(self, listing_id: int) -> Optional[dict]:
        """Get listing by its ID"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM listings WHERE id = ?', (listing_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_listing(self, platform: str, article_id: str) -> Optional[dict]:
        """Get existing listing"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                'SELECT * FROM listings WHERE platform = ? AND article_id = ?', 
                (platform, article_id)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def _prefer_non_empty(new_value: Any, current_value: Any) -> Any:
        """Keep existing values when the new scrape result is empty."""
        if new_value is None:
            return current_value
        if isinstance(new_value, str) and not new_value.strip():
            return current_value
        return new_value

    def _record_sale_status_change(
        self,
        cursor: sqlite3.Cursor,
        listing_id: int,
        old_status: str | None,
        new_status: str,
    ) -> None:
        old_value = old_status or "for_sale"
        new_value = new_status or "for_sale"
        if old_value == new_value:
            return
        cursor.execute(
            '''
            INSERT INTO sale_status_history (listing_id, old_status, new_status)
            VALUES (?, ?, ?)
            ''',
            (listing_id, old_value, new_value),
        )
    
    def add_listing(self, item: Item) -> tuple[bool, Optional[dict], Optional[int]]:
        """
        Add or update a listing.
        
        Returns:
            (is_new, price_change_info, listing_id)
            - is_new: True if this is a new listing
            - price_change_info: Dict with old/new price if price changed, else None
            - listing_id: ID of the listing in database
        """
        # Internal lock usage to ensure atomicity of check-then-act
        with self.lock:
            cursor = self.conn.cursor()
            
            # Check existing
            cursor.execute(
                'SELECT * FROM listings WHERE platform = ? AND article_id = ?', 
                (item.platform, item.article_id)
            )
            row = cursor.fetchone()
            existing = dict(row) if row else None
            
            price_numeric = item.parse_price()
            detected_status = self.detect_sale_status(item.title)
            
            if existing:
                # Check for price change
                old_price = existing['price']
                old_price_numeric = existing['price_numeric'] or 0
                old_status = existing.get('sale_status') or 'for_sale'
                new_status = detected_status or old_status

                price_change_info: Optional[dict] = None
                if old_price != item.price and old_price_numeric != price_numeric:
                    # Price changed - record in history
                    cursor.execute('''
                        INSERT INTO price_history 
                        (listing_id, old_price, old_price_numeric, new_price, new_price_numeric)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (existing['id'], old_price, old_price_numeric, item.price, price_numeric))

                    price_change_info = {
                        'old_price': old_price,
                        'new_price': item.price,
                        'old_numeric': old_price_numeric,
                        'new_numeric': price_numeric
                    }

                updated_title = self._prefer_non_empty(item.title, existing.get('title'))
                updated_url = self._prefer_non_empty(item.link, existing.get('url'))
                updated_thumbnail = self._prefer_non_empty(item.thumbnail, existing.get('thumbnail'))
                updated_seller = self._prefer_non_empty(item.seller, existing.get('seller'))
                updated_location = self._prefer_non_empty(item.location, existing.get('location'))
                updated_price = self._prefer_non_empty(item.price, existing.get('price'))
                updated_price_numeric = (
                    price_numeric if isinstance(updated_price, str) and updated_price == item.price
                    else existing.get('price_numeric') or 0
                )

                if new_status != old_status:
                    self._record_sale_status_change(cursor, existing['id'], old_status, new_status)

                fields_changed = any(
                    (
                        updated_title != existing.get('title'),
                        updated_url != existing.get('url'),
                        updated_thumbnail != existing.get('thumbnail'),
                        updated_seller != existing.get('seller'),
                        updated_location != existing.get('location'),
                        updated_price != existing.get('price'),
                        updated_price_numeric != (existing.get('price_numeric') or 0),
                        new_status != old_status,
                    )
                )

                if fields_changed:
                    cursor.execute(
                        '''
                        UPDATE listings
                        SET title = ?, price = ?, price_numeric = ?, url = ?, thumbnail = ?,
                            seller = ?, location = ?, sale_status = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        ''',
                        (
                            updated_title,
                            updated_price,
                            updated_price_numeric,
                            updated_url,
                            updated_thumbnail,
                            updated_seller,
                            updated_location,
                            new_status,
                            existing['id'],
                        ),
                    )
                    self.conn.commit()
                    self._invalidate_cache()

                return False, price_change_info, existing['id']
            
            # New listing
            try:
                cursor.execute('''
                    INSERT INTO listings 
                    (platform, article_id, keyword, title, price, price_numeric, url, thumbnail, seller, location, sale_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.platform, item.article_id, item.keyword, item.title,
                    item.price, price_numeric, item.link, item.thumbnail,
                    item.seller, item.location, detected_status
                ))
                new_id = cursor.lastrowid
                self.conn.commit()
                self._invalidate_cache()
                return True, None, new_id
            except sqlite3.IntegrityError:
                return False, None, None
    
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
    
    # Statistics methods - all read operations also need locks if sharing connection
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

    def get_existing_article_ids(self, platform: str, article_ids: list[str], chunk_size: int = 500) -> set[str]:
        """Get existing article IDs for a platform in chunks (SQLite variable-safe)."""
        if not article_ids:
            return set()

        normalized = [str(aid) for aid in article_ids if aid is not None and str(aid).strip()]
        if not normalized:
            return set()

        existing: set[str] = set()
        with self.lock:
            cursor = self.conn.cursor()
            for i in range(0, len(normalized), chunk_size):
                chunk = normalized[i:i + chunk_size]
                placeholders = ",".join(["?"] * len(chunk))
                query = (
                    f"SELECT article_id FROM listings WHERE platform = ? "
                    f"AND article_id IN ({placeholders})"
                )
                cursor.execute(query, [platform, *chunk])
                existing.update(str(row["article_id"]) for row in cursor.fetchall())
        return existing

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

    def is_fuzzy_duplicate(self, item: Item, threshold: float = 0.9) -> bool:
        """
        Check if item is a fuzzy duplicate of recent items.
        Optimized with price-based pre-filtering and quick_ratio pre-check.
        """
        with self.lock:
            cursor = self.conn.cursor()
            # Optimized: First filter by exact price match (reduces candidates significantly)
            cursor.execute('''
                SELECT title FROM listings 
                WHERE platform = ? 
                AND price = ?
                AND created_at >= datetime('now', '-3 days')
                LIMIT 20
            ''', (item.platform, item.price))
            
            candidates = cursor.fetchall()
            
            for row in candidates:
                # Use quick_ratio first (faster approximation)
                matcher = difflib.SequenceMatcher(None, item.title, row['title'])
                if matcher.quick_ratio() >= threshold:
                    # Only compute full ratio if quick_ratio passes
                    if matcher.ratio() >= threshold:
                        return True
            
            return False

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

    # Favorites Management
    def get_listing_id(self, platform: str, article_id: str) -> Optional[int]:
        """Get listing ID by platform and article_id"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                'SELECT id FROM listings WHERE platform = ? AND article_id = ?', 
                (platform, article_id)
            )
            row = cursor.fetchone()
            return row['id'] if row else None

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

    # Notification Logging
    def log_notification(self, listing_id: int, notification_type: str, message: str):
        """Log a sent notification"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO notification_log (listing_id, notification_type, message_preview)
                VALUES (?, ?, ?)
            ''', (listing_id, notification_type, message[:200]))  # store preview
            self.conn.commit()
            self._invalidate_cache()

    def log_notification_delivery(
        self,
        listing_id: int,
        notification_type: str,
        status: str,
        attempt: int = 1,
        error_message: str | None = None,
        rate_limited: bool = False,
    ) -> None:
        """Log delivery attempt results for operational visibility."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                '''
                INSERT INTO notification_delivery_log
                (listing_id, notification_type, status, attempt, error_message, rate_limited)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (
                    listing_id,
                    notification_type,
                    status,
                    max(1, int(attempt)),
                    (error_message or "")[:500] or None,
                    1 if rate_limited else 0,
                ),
            )
            self.conn.commit()
            self._invalidate_cache()

    def get_notification_logs(self, limit: int = 50, offset: int = 0) -> list:
        """Get notification logs"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT nl.*, l.title, l.platform, l.price, l.url
                FROM notification_log nl
                JOIN listings l ON nl.listing_id = l.id
                ORDER BY nl.sent_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    def get_notification_delivery_summary(self, days: int = 7) -> dict[str, dict[str, Any]]:
        """Summarize delivery success/failure and last events per channel."""
        with self.lock:
            cursor = self.conn.cursor()
            channels = ("telegram", "discord", "slack")
            summary: dict[str, dict[str, Any]] = {
                channel: {
                    "success_count": 0,
                    "failed_count": 0,
                    "success_rate": 0.0,
                    "last_success_at": None,
                    "last_failure_at": None,
                    "last_failure_message": None,
                    "last_rate_limited_at": None,
                }
                for channel in channels
            }

            cursor.execute(
                '''
                SELECT
                    notification_type,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count,
                    MAX(CASE WHEN status = 'success' THEN sent_at END) AS last_success_at,
                    MAX(CASE WHEN status = 'failed' THEN sent_at END) AS last_failure_at,
                    MAX(CASE WHEN rate_limited = 1 THEN sent_at END) AS last_rate_limited_at
                FROM notification_delivery_log
                WHERE sent_at >= datetime('now', ?)
                GROUP BY notification_type
                ''',
                (f'-{days} days',),
            )
            for row in cursor.fetchall():
                channel = str(row["notification_type"] or "")
                if channel not in summary:
                    continue
                success_count = int(row["success_count"] or 0)
                failed_count = int(row["failed_count"] or 0)
                total = success_count + failed_count
                summary[channel].update(
                    {
                        "success_count": success_count,
                        "failed_count": failed_count,
                        "success_rate": round((success_count / total) * 100.0, 1) if total else 0.0,
                        "last_success_at": row["last_success_at"],
                        "last_failure_at": row["last_failure_at"],
                        "last_rate_limited_at": row["last_rate_limited_at"],
                    }
                )

            for channel in channels:
                cursor.execute(
                    '''
                    SELECT error_message
                    FROM notification_delivery_log
                    WHERE notification_type = ?
                      AND status = 'failed'
                      AND sent_at >= datetime('now', ?)
                    ORDER BY sent_at DESC
                    LIMIT 1
                    ''',
                    (channel, f'-{days} days'),
                )
                row = cursor.fetchone()
                summary[channel]["last_failure_message"] = row["error_message"] if row else None

            return summary

    # Seller Management
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
    
    def close(self):
        """Close database connection"""
        self.conn.close()
    
    # Search History Methods
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
    
    # Listing Notes Methods
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
    
    # ===== Feature #12: Sale Status =====
    
    def update_sale_status(self, listing_id: int, status: str):
        """Update sale status of a listing"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT sale_status FROM listings WHERE id = ?', (listing_id,))
            row = cursor.fetchone()
            if row is None:
                return
            old_status = row['sale_status'] or 'for_sale'
            new_status = status or 'for_sale'
            if old_status == new_status:
                return
            self._record_sale_status_change(cursor, listing_id, old_status, new_status)
            cursor.execute(
                '''
                UPDATE listings SET sale_status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''',
                (new_status, listing_id),
            )
            self.conn.commit()
            self._invalidate_cache()
    
    def detect_sale_status(self, title: str) -> str:
        """Detect sale status from title text"""
        title_lower = title.lower() if title else ""
        if any(keyword in title_lower for keyword in ["판매완료", "거래완료", "sold"]):
            return "sold"
        elif any(keyword in title_lower for keyword in ["예약중", "예약", "reserved"]):
            return "reserved"
        return "for_sale"
    
    def get_listings_by_status(
        self,
        status: str | None = None,
        platform: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list:
        """Get listings filtered by sale status"""
        with self.lock:
            cursor = self.conn.cursor()
            query = 'SELECT * FROM listings WHERE 1=1'
            params = []
            
            if status and status != 'all':
                query += ' AND sale_status = ?'
                params.append(status)
            
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
    
    # ===== Feature #18: Cleanup =====
    
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
    
    # ===== Feature #28: Auto Tags =====
    
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
    
    # ===== Feature #16: Enhanced Export =====
    
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


if __name__ == "__main__":
    db = DatabaseManager()
    print("Database initialized successfully!")
    print(f"Total listings: {db.get_total_listings()}")
    print(f"By platform: {db.get_listings_by_platform()}")
    db.close()
