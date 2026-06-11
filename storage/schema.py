# pyright: reportAttributeAccessIssue=false
"""SchemaMixin for DatabaseManager."""

from .common import *


class SchemaMixin:
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
                    normalized_url TEXT,
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

            # Migrations for existing databases.
            self._add_column_if_missing(cursor, "listings", "sale_status", 'TEXT DEFAULT "for_sale"')
            self._add_column_if_missing(cursor, "listings", "price_numeric", "INTEGER DEFAULT 0")
            self._add_column_if_missing(cursor, "listings", "normalized_url", "TEXT")
            self._add_column_if_missing(cursor, "price_history", "old_price_numeric", "INTEGER")
            self._add_column_if_missing(cursor, "price_history", "new_price_numeric", "INTEGER")
            self._add_column_if_missing(cursor, "listing_notes", "auto_tags", 'TEXT DEFAULT "[]"')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_listings_platform_normalized_url ON listings(platform, normalized_url)')

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
            try:
                self._migrate_normalized_urls(cursor)
            except Exception as e:
                self.logger.warning(f"URL normalization migration skipped/failed: {e}")
            try:
                self._verify_schema_integrity(cursor)
                self._set_meta(cursor, "schema_version", str(self.SCHEMA_VERSION))
                self.conn.commit()
            except Exception as e:
                self.logger.warning(f"Schema integrity check failed: {e}")

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

    def _column_exists(self, cursor: sqlite3.Cursor, table: str, column: str) -> bool:
        cursor.execute(f"PRAGMA table_info({table})")
        return any(str(row["name"]) == column for row in cursor.fetchall())

    def _add_column_if_missing(
        self,
        cursor: sqlite3.Cursor,
        table: str,
        column: str,
        definition: str,
    ) -> None:
        if self._column_exists(cursor, table, column):
            return
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                return
            self.logger.warning("Schema migration failed: %s.%s (%s)", table, column, e)
            raise

    def _migrate_normalized_urls(self, cursor: sqlite3.Cursor) -> None:
        key = "normalized_url_migrated_v1"
        if self._get_meta(cursor, key) == "1":
            return
        cursor.execute("SELECT id, url FROM listings WHERE COALESCE(normalized_url, '') = ''")
        rows = cursor.fetchall()
        if rows:
            cursor.executemany(
                "UPDATE listings SET normalized_url = ? WHERE id = ?",
                [(self.normalize_url(row["url"]), row["id"]) for row in rows],
            )
        self._set_meta(cursor, key, "1")
        self.conn.commit()
        self.logger.info("Normalized URL migration complete. listings updated=%s.", len(rows))

    def _verify_schema_integrity(self, cursor: sqlite3.Cursor) -> None:
        required = {
            "listings": {"platform", "article_id", "url", "normalized_url", "sale_status", "price_numeric"},
            "notification_delivery_log": {"listing_id", "notification_type", "status", "attempt"},
            "meta": {"key", "value"},
        }
        missing: list[str] = []
        for table, columns in required.items():
            cursor.execute(f"PRAGMA table_info({table})")
            present = {str(row["name"]) for row in cursor.fetchall()}
            missing.extend(f"{table}.{column}" for column in columns if column not in present)
        if missing:
            raise RuntimeError(f"Missing required database columns: {', '.join(sorted(missing))}")

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
