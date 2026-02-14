import os
import tempfile
import unittest

from db import DatabaseManager


class TestListingsCountWithStatus(unittest.TestCase):
    def test_get_listings_count_with_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            db = DatabaseManager(db_path)
            try:
                with db.lock:
                    cur = db.conn.cursor()
                    cur.execute(
                        "INSERT INTO listings (platform, article_id, title, price, sale_status) VALUES (?, ?, ?, ?, ?)",
                        ("danggeun", "a1", "t1", "1만", "for_sale"),
                    )
                    cur.execute(
                        "INSERT INTO listings (platform, article_id, title, price, sale_status) VALUES (?, ?, ?, ?, ?)",
                        ("danggeun", "a2", "t2", "2만", "reserved"),
                    )
                    cur.execute(
                        "INSERT INTO listings (platform, article_id, title, price, sale_status) VALUES (?, ?, ?, ?, ?)",
                        ("danggeun", "a3", "t3", "3만", "sold"),
                    )
                    db.conn.commit()

                self.assertEqual(db.get_listings_count(), 3)
                self.assertEqual(db.get_listings_count(status="for_sale"), 1)
                self.assertEqual(db.get_listings_count(status="reserved"), 1)
                self.assertEqual(db.get_listings_count(status="sold"), 1)
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()

