# pyright: reportAttributeAccessIssue=false
"""ListingPersistenceMixin for DatabaseManager."""

from .common import *


class ListingPersistenceMixin:
    @staticmethod
    def normalize_url(url: str | None) -> str:
        raw = str(url or "").strip()
        if not raw:
            return ""
        try:
            split = urlsplit(raw)
        except Exception:
            return raw.rstrip("/")

        scheme = (split.scheme or "https").lower()
        netloc = split.netloc.lower()
        path = split.path.rstrip("/") or split.path
        filtered_query = [
            (key, value)
            for key, value in parse_qsl(split.query, keep_blank_values=True)
            if not key.lower().startswith("utm_") and key.lower() not in {"fbclid", "gclid"}
        ]
        query = urlencode(sorted(filtered_query), doseq=True)
        return urlunsplit((scheme, netloc, path, query, ""))

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
            normalized_url = self.normalize_url(item.link)

            # Check existing
            cursor.execute(
                'SELECT * FROM listings WHERE platform = ? AND article_id = ?',
                (item.platform, item.article_id)
            )
            row = cursor.fetchone()
            if row is None and normalized_url:
                cursor.execute(
                    '''
                    SELECT * FROM listings
                    WHERE platform = ? AND normalized_url = ?
                    ORDER BY updated_at DESC, id DESC
                    LIMIT 1
                    ''',
                    (item.platform, normalized_url),
                )
                row = cursor.fetchone()
            existing = dict(row) if row else None

            price_numeric = item.parse_price()
            explicit_status = self._normalize_sale_status(item.sale_status)
            detected_status = explicit_status if explicit_status is not None else self.detect_sale_status(item.title)

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
                updated_normalized_url = self._prefer_non_empty(normalized_url, existing.get('normalized_url'))
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
                        updated_normalized_url != existing.get('normalized_url'),
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
                        SET title = ?, price = ?, price_numeric = ?, url = ?, normalized_url = ?, thumbnail = ?,
                            seller = ?, location = ?, sale_status = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        ''',
                        (
                            updated_title,
                            updated_price,
                            updated_price_numeric,
                            updated_url,
                            updated_normalized_url,
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
                    (platform, article_id, keyword, title, price, price_numeric, url, normalized_url, thumbnail, seller, location, sale_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.platform, item.article_id, item.keyword, item.title,
                    item.price, price_numeric, item.link, normalized_url, item.thumbnail,
                    item.seller, item.location, detected_status
                ))
                new_id = cursor.lastrowid
                self.conn.commit()
                self._invalidate_cache()
                return True, None, new_id
            except sqlite3.IntegrityError:
                return False, None, None

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

    @staticmethod
    def _normalize_sale_status(value: str | None) -> str | None:
        raw = str(value or "").strip().lower()
        if not raw:
            return None
        compact = ''.join(ch for ch in raw if ch.isalnum() or ('가' <= ch <= '힣'))
        if compact in {"forsale", "onsale", "sale", "selling", "판매중", "판매", "available", "진행중"}:
            return "for_sale"
        if compact in {"reserved", "reserve", "reservation", "예약", "예약중", "hold"}:
            return "reserved"
        if compact in {"sold", "soldout", "판매완료", "거래완료", "완료", "품절"}:
            return "sold"
        if compact in {"unknown", "미확인", "알수없음"}:
            return "unknown"
        return "unknown"

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
