import os
import sqlite3
import tempfile
import unittest

from db import DatabaseManager
from models import Item


class TestDatabaseIntegrityUpdates(unittest.TestCase):
    def test_existing_listing_updates_metadata_and_records_status_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = DatabaseManager(os.path.join(tmp, "test.db"))
            try:
                first = Item(
                    platform="danggeun",
                    article_id="a1",
                    title="Macbook Air",
                    price="100,000원",
                    link="https://example.com/a1",
                    keyword="macbook",
                    thumbnail="https://img/old.png",
                )
                is_new, _, listing_id = db.add_listing(first)
                self.assertTrue(is_new)
                assert listing_id is not None

                updated = Item(
                    platform="danggeun",
                    article_id="a1",
                    title="Macbook Air 예약중",
                    price="100,000원",
                    link="https://example.com/a1",
                    keyword="macbook",
                    thumbnail="https://img/new.png",
                    seller="alice",
                    location="서울 강남구",
                )
                is_new, price_change, _ = db.add_listing(updated)
                self.assertFalse(is_new)
                self.assertIsNone(price_change)

                listing = db.get_listing("danggeun", "a1")
                assert listing is not None
                self.assertEqual(listing["title"], "Macbook Air 예약중")
                self.assertEqual(listing["thumbnail"], "https://img/new.png")
                self.assertEqual(listing["seller"], "alice")
                self.assertEqual(listing["location"], "서울 강남구")
                self.assertEqual(listing["sale_status"], "reserved")

                history = db.get_status_history(limit=10)
                self.assertEqual(len(history), 1)
                self.assertEqual(history[0]["old_status"], "for_sale")
                self.assertEqual(history[0]["new_status"], "reserved")

                blank_update = Item(
                    platform="danggeun",
                    article_id="a1",
                    title="Macbook Air 예약중",
                    price="100,000원",
                    link="https://example.com/a1",
                    keyword="macbook",
                    thumbnail="",
                    seller="",
                    location=None,
                )
                db.add_listing(blank_update)
                listing = db.get_listing("danggeun", "a1")
                assert listing is not None
                self.assertEqual(listing["thumbnail"], "https://img/new.png")
                self.assertEqual(listing["seller"], "alice")
                self.assertEqual(listing["location"], "서울 강남구")
            finally:
                db.close()

    def test_update_favorite_can_clear_target_price(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = DatabaseManager(os.path.join(tmp, "test.db"))
            try:
                item = Item(
                    platform="bunjang",
                    article_id="b1",
                    title="iPhone",
                    price="800,000원",
                    link="https://example.com/b1",
                    keyword="iphone",
                )
                _, _, listing_id = db.add_listing(item)
                assert listing_id is not None
                self.assertTrue(db.add_favorite(listing_id, target_price=750000))

                self.assertTrue(db.update_favorite(listing_id, notes="watch", target_price=None))
                favorite = db.get_favorite_details(listing_id)
                assert favorite is not None
                self.assertIsNone(favorite["target_price"])
                self.assertEqual(favorite["notes"], "watch")
            finally:
                db.close()

    def test_explicit_sale_status_overrides_title_heuristic(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = DatabaseManager(os.path.join(tmp, "test.db"))
            try:
                first = Item(
                    platform="bunjang",
                    article_id="status-1",
                    title="아이폰 15 프로",
                    price="900,000원",
                    link="https://example.com/status-1",
                    keyword="iphone",
                )
                db.add_listing(first)

                updated = Item(
                    platform="bunjang",
                    article_id="status-1",
                    title="아이폰 15 프로 예약중",
                    price="900,000원",
                    link="https://example.com/status-1",
                    keyword="iphone",
                    sale_status="sold",
                )
                db.add_listing(updated)

                listing = db.get_listing("bunjang", "status-1")
                assert listing is not None
                self.assertEqual(listing["sale_status"], "sold")

                history = db.get_status_history(limit=10)
                self.assertEqual(len(history), 1)
                self.assertEqual(history[0]["new_status"], "sold")
            finally:
                db.close()

    def test_same_normalized_url_updates_existing_listing_with_different_article_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = DatabaseManager(os.path.join(tmp, "test.db"))
            try:
                first = Item(
                    platform="danggeun",
                    article_id="hash_old",
                    title="아이폰",
                    price="100,000원",
                    link="HTTPS://Example.com/items/123/?utm_source=x&b=2&a=1#frag",
                    keyword="iphone",
                )
                second = Item(
                    platform="danggeun",
                    article_id="hash_new",
                    title="아이폰 상태좋음",
                    price="90,000원",
                    link="https://example.com/items/123?a=1&b=2",
                    keyword="iphone",
                )

                is_new, _, first_id = db.add_listing(first)
                self.assertTrue(is_new)
                is_new, price_change, second_id = db.add_listing(second)
                self.assertFalse(is_new)
                self.assertEqual(first_id, second_id)
                self.assertIsNotNone(price_change)

                with db.lock:
                    cur = db.conn.cursor()
                    cur.execute("SELECT COUNT(*) AS count FROM listings")
                    self.assertEqual(cur.fetchone()["count"], 1)
                    cur.execute("SELECT normalized_url FROM listings WHERE id = ?", (first_id,))
                    self.assertEqual(cur.fetchone()["normalized_url"], "https://example.com/items/123?a=1&b=2")
            finally:
                db.close()

    def test_old_schema_gets_normalized_url_column_and_version_meta(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "old.db")
            conn = sqlite3.connect(db_path)
            try:
                conn.execute(
                    """
                    CREATE TABLE listings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        platform TEXT NOT NULL,
                        article_id TEXT NOT NULL,
                        keyword TEXT,
                        title TEXT,
                        price TEXT,
                        url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(platform, article_id)
                    )
                    """
                )
                conn.execute(
                    "INSERT INTO listings (platform, article_id, title, price, url) VALUES (?, ?, ?, ?, ?)",
                    ("bunjang", "1", "아이폰", "10,000원", "https://example.com/p/1?utm_medium=x"),
                )
                conn.commit()
            finally:
                conn.close()

            db = DatabaseManager(db_path)
            try:
                with db.lock:
                    cur = db.conn.cursor()
                    cur.execute("PRAGMA table_info(listings)")
                    columns = {row["name"] for row in cur.fetchall()}
                    self.assertIn("normalized_url", columns)
                    cur.execute("SELECT normalized_url FROM listings WHERE article_id = '1'")
                    self.assertEqual(cur.fetchone()["normalized_url"], "https://example.com/p/1")
                    cur.execute("SELECT value FROM meta WHERE key = 'schema_version'")
                    self.assertEqual(cur.fetchone()["value"], str(DatabaseManager.SCHEMA_VERSION))
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
