# db.py
"""Enhanced database manager with price tracking and statistics"""

import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Optional
from models import Item, FavoriteItem, NotificationLog, SellerFilter
import difflib



class DatabaseManager:
    """SQLite database manager with price history tracking - Thread Safe"""
    
    def __init__(self, db_path: str = "listings.db"):
        self.db_path = db_path
        # check_same_thread=False allowed but we handle locking manually
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        
        # Enable WAL mode for better concurrency
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.create_tables()
    
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
    
    def add_listing(self, item: Item) -> tuple[bool, Optional[dict]]:
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
            
            if existing:
                # Check for price change
                old_price = existing['price']
                old_price_numeric = existing['price_numeric'] or 0
                
                if old_price != item.price and old_price_numeric != price_numeric:
                    # Price changed - record in history
                    cursor.execute('''
                        INSERT INTO price_history 
                        (listing_id, old_price, old_price_numeric, new_price, new_price_numeric)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (existing['id'], old_price, old_price_numeric, item.price, price_numeric))
                    
                    # Update listing
                    cursor.execute('''
                        UPDATE listings 
                        SET price = ?, price_numeric = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (item.price, price_numeric, existing['id']))
                    
                    self.conn.commit()
                    
                    return False, {
                        'old_price': old_price,
                        'new_price': item.price,
                        'old_numeric': old_price_numeric,
                        'new_numeric': price_numeric
                    }, existing['id']
                
                return False, None, existing['id']
            
            # New listing
            try:
                cursor.execute('''
                    INSERT INTO listings 
                    (platform, article_id, keyword, title, price, price_numeric, url, thumbnail, seller, location)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.platform, item.article_id, item.keyword, item.title,
                    item.price, price_numeric, item.link, item.thumbnail,
                    item.seller, item.location
                ))
                new_id = cursor.lastrowid
                self.conn.commit()
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
    
    # Statistics methods - all read operations also need locks if sharing connection
    def get_total_listings(self) -> int:
        """Get total number of listings"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM listings')
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

    def is_fuzzy_duplicate(self, item: Item, threshold: float = 0.9) -> bool:
        """Check if item is a fuzzy duplicate of recent items"""
        with self.lock:
            cursor = self.conn.cursor()
            # Check last 3 days, same platform
            cursor.execute('''
                SELECT title, price, seller 
                FROM listings 
                WHERE platform = ? 
                AND created_at >= datetime('now', '-3 days')
            ''', (item.platform,))
            
            candidates = cursor.fetchall()
            
            for row in candidates:
                # Check price string exact match (simplest heuristics)
                # Or price_numeric if available? 'price' field is string in DB? 
                # DB schema has price (str) and price_numeric (int).
                # Selecting price (str).
                if row['price'] != item.price:
                    continue
                
                # Check similarity
                ratio = difflib.SequenceMatcher(None, item.title, row['title']).ratio()
                if ratio >= threshold:
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

    def add_favorite(self, listing_id: int, notes: str = "", target_price: int = None) -> bool:
        """Add a listing to favorites"""
        with self.lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO favorites (listing_id, notes, target_price)
                    VALUES (?, ?, ?)
                ''', (listing_id, notes, target_price))
                self.conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def update_favorite(self, listing_id: int, notes: str = None, target_price: int = None):
        """Update favorite details"""
        with self.lock:
            cursor = self.conn.cursor()
            updates = []
            params = []
            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)
            if target_price is not None:
                updates.append("target_price = ?")
                params.append(target_price)
            
            if not updates:
                return

            params.append(listing_id)
            cursor.execute(f'''
                UPDATE favorites SET {", ".join(updates)} WHERE listing_id = ?
            ''', tuple(params))
            self.conn.commit()

    def remove_favorite(self, listing_id: int):
        """Remove a listing from favorites"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM favorites WHERE listing_id = ?', (listing_id,))
            self.conn.commit()
    
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

    def remove_seller_filter(self, seller_name: str, platform: str):
        """Remove a seller filter"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                DELETE FROM seller_filters 
                WHERE seller_name = ? AND platform = ?
            ''', (seller_name, platform))
            self.conn.commit()

    def get_blocked_sellers(self) -> list:
        """Get list of blocked sellers"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT seller_name, platform 
                FROM seller_filters 
                WHERE is_blocked = 1
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


if __name__ == "__main__":
    db = DatabaseManager()
    print("Database initialized successfully!")
    print(f"Total listings: {db.get_total_listings()}")
    print(f"By platform: {db.get_listings_by_platform()}")
    db.close()
