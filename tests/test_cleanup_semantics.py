import os
import tempfile
import unittest
from datetime import datetime, timedelta

from db import DatabaseManager
from models import Item


class TestCleanupSemantics(unittest.TestCase):
    def test_auto_tags_do_not_protect_listing_but_notes_do(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = DatabaseManager(os.path.join(tmp, "test.db"))
            try:
                old_time = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")

                tagged = Item(
                    platform="danggeun",
                    article_id="a1",
                    title="old tagged",
                    price="10,000원",
                    link="https://example.com/a1",
                    keyword="test",
                )
                noted = Item(
                    platform="danggeun",
                    article_id="a2",
                    title="old noted",
                    price="20,000원",
                    link="https://example.com/a2",
                    keyword="test",
                )

                _, _, tagged_id = db.add_listing(tagged)
                _, _, noted_id = db.add_listing(noted)
                assert tagged_id is not None
                assert noted_id is not None

                db.add_auto_tags(tagged_id, ["auto"])
                db.add_listing_note(noted_id, note="keep", status_tag="interested")
                db.log_notification(tagged_id, "telegram", "sent")
                db.log_notification_delivery(tagged_id, "telegram", "failed", attempt=1, error_message="oops")
                db.update_sale_status(tagged_id, "sold")

                with db.lock:
                    cur = db.conn.cursor()
                    cur.execute("UPDATE listings SET created_at = ? WHERE id = ?", (old_time, tagged_id))
                    cur.execute("UPDATE listings SET created_at = ? WHERE id = ?", (old_time, noted_id))
                    db.conn.commit()

                deleted = db.cleanup_old_listings(days=30, exclude_favorites=True, exclude_noted=True)
                self.assertEqual(deleted, 1)
                self.assertIsNone(db.get_listing("danggeun", "a1"))
                self.assertIsNotNone(db.get_listing("danggeun", "a2"))

                with db.lock:
                    cur = db.conn.cursor()
                    cur.execute("SELECT COUNT(*) AS count FROM listing_auto_tags WHERE listing_id = ?", (tagged_id,))
                    self.assertEqual(cur.fetchone()["count"], 0)
                    cur.execute("SELECT COUNT(*) AS count FROM notification_log WHERE listing_id = ?", (tagged_id,))
                    self.assertEqual(cur.fetchone()["count"], 0)
                    cur.execute(
                        "SELECT COUNT(*) AS count FROM notification_delivery_log WHERE listing_id = ?",
                        (tagged_id,),
                    )
                    self.assertEqual(cur.fetchone()["count"], 0)
                    cur.execute("SELECT COUNT(*) AS count FROM sale_status_history WHERE listing_id = ?", (tagged_id,))
                    self.assertEqual(cur.fetchone()["count"], 0)
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
