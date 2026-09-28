"""Regression: numeric price migration processes every row (ISSUE-007)."""

import os
import tempfile
import unittest

from db import DatabaseManager


class PriceMigrationBatchesTest(unittest.TestCase):
    def test_migration_recomputes_all_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "m.db")
            db = DatabaseManager(path)
            db.conn.executemany(
                "INSERT INTO listings (platform, article_id, title, price, price_numeric) VALUES (?, ?, ?, ?, 0)",
                [("bunjang", str(i), f"t{i}", "10만원") for i in range(1200)],
            )
            listing_ids = [row[0] for row in db.conn.execute("SELECT id FROM listings")]
            db.conn.executemany(
                "INSERT INTO price_history (listing_id, old_price, old_price_numeric, new_price, new_price_numeric) "
                "VALUES (?, '12만원', 0, '10만원', 0)",
                [(lid,) for lid in listing_ids],
            )
            db.conn.execute("UPDATE meta SET value = '1' WHERE key = 'price_parse_version'")
            db.conn.commit()
            db.close()

            db = DatabaseManager(path)
            try:
                fixed = db.conn.execute("SELECT COUNT(*) FROM listings WHERE price_numeric = 100000").fetchone()[0]
                history_fixed = db.conn.execute(
                    "SELECT COUNT(*) FROM price_history WHERE old_price_numeric = 120000 AND new_price_numeric = 100000"
                ).fetchone()[0]
                version = db.conn.execute("SELECT value FROM meta WHERE key = 'price_parse_version'").fetchone()[0]
            finally:
                db.close()

        self.assertEqual(fixed, 1200)
        self.assertEqual(history_fixed, 1200)
        self.assertEqual(int(version), DatabaseManager.PRICE_PARSE_VERSION)
        self.assertGreaterEqual(DatabaseManager.PRICE_PARSE_VERSION, 3)


if __name__ == "__main__":
    unittest.main()
