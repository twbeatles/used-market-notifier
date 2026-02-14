import os
import sqlite3
import tempfile
import unittest

from db import DatabaseManager


class TestPriceMigration(unittest.TestCase):
    def test_migration_recomputes_price_numeric(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "old.db")

            # Create an "old" schema without price_numeric/meta tables.
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
                        UNIQUE(platform, article_id)
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE price_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        listing_id INTEGER NOT NULL,
                        old_price TEXT,
                        new_price TEXT,
                        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                conn.execute(
                    "INSERT INTO listings (platform, article_id, title, price) VALUES (?, ?, ?, ?)",
                    ("danggeun", "x1", "t", "10만원"),
                )
                conn.execute(
                    "INSERT INTO price_history (listing_id, old_price, new_price) VALUES (?, ?, ?)",
                    (1, "2만", "1.2만"),
                )
                conn.commit()
            finally:
                conn.close()

            # Opening via DatabaseManager should run schema + price migrations.
            db = DatabaseManager(db_path)
            try:
                with db.lock:
                    cur = db.conn.cursor()
                    cur.execute("SELECT price_numeric FROM listings WHERE article_id = ?", ("x1",))
                    price_numeric = cur.fetchone()[0]
                    self.assertEqual(price_numeric, 100000)

                    cur.execute(
                        "SELECT old_price_numeric, new_price_numeric FROM price_history WHERE id = 1"
                    )
                    row = cur.fetchone()
                    self.assertEqual(row[0], 20000)
                    self.assertEqual(row[1], 12000)
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()

