import os
import tempfile
import unittest

from db import DatabaseManager


class TestExistingArticleIds(unittest.TestCase):
    def test_existing_article_ids_chunked(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            db = DatabaseManager(db_path)
            try:
                with db.lock:
                    cur = db.conn.cursor()
                    rows = [
                        ("danggeun", f"id{i}", f"title{i}", "1,000원")
                        for i in range(1200)
                    ]
                    cur.executemany(
                        "INSERT INTO listings (platform, article_id, title, price) VALUES (?, ?, ?, ?)",
                        rows,
                    )
                    db.conn.commit()

                candidates = [f"id{i}" for i in range(0, 1200, 50)] + ["missing-1", "missing-2"]
                existing = db.get_existing_article_ids("danggeun", candidates, chunk_size=200)

                self.assertIn("id0", existing)
                self.assertIn("id1150", existing)
                self.assertNotIn("missing-1", existing)
                self.assertNotIn("missing-2", existing)
                self.assertEqual(existing, set(candidates) - {"missing-1", "missing-2"})
            finally:
                db.close()

    def test_existing_article_ids_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            db = DatabaseManager(db_path)
            try:
                self.assertEqual(db.get_existing_article_ids("danggeun", []), set())
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
