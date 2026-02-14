import os
import tempfile
import unittest
from datetime import datetime, timedelta

from db import DatabaseManager


class TestCleanupPreview(unittest.TestCase):
    def test_cleanup_preview_counts_old_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            db = DatabaseManager(db_path)
            try:
                old_dt = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")
                new_dt = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")

                with db.lock:
                    cur = db.conn.cursor()
                    cur.execute(
                        "INSERT INTO listings (platform, article_id, title, created_at) VALUES (?, ?, ?, ?)",
                        ("danggeun", "old1", "old", old_dt),
                    )
                    cur.execute(
                        "INSERT INTO listings (platform, article_id, title, created_at) VALUES (?, ?, ?, ?)",
                        ("danggeun", "new1", "new", new_dt),
                    )
                    db.conn.commit()

                preview = db.get_cleanup_preview(days=30, exclude_favorites=True, exclude_noted=True)
                self.assertEqual(preview["total_count"], 2)
                self.assertEqual(preview["delete_count"], 1)
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()

