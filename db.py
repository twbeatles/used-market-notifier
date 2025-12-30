# db.py
"""Enhanced database manager with price tracking and statistics"""

import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Optional
from scrapers.base import Item


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
            
            # Statistics table for aggregated data
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
            (is_new, price_change_info)
            - is_new: True if this is a new listing
            - price_change_info: Dict with old/new price if price changed, else None
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
                    }
                
                return False, None
            
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
                self.conn.commit()
                return True, None
            except sqlite3.IntegrityError:
                return False, None
    
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
    
    def close(self):
        """Close database connection"""
        self.conn.close()


if __name__ == "__main__":
    db = DatabaseManager()
    print("Database initialized successfully!")
    print(f"Total listings: {db.get_total_listings()}")
    print(f"By platform: {db.get_listings_by_platform()}")
    db.close()
