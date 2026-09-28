"""Regression: cleanup keeps listings that are still being seen in search results."""

import os
import tempfile
import unittest

from db import DatabaseManager
from models import Item


def _item(article_id: str) -> Item:
    return Item(
        platform="bunjang",
        article_id=article_id,
        title=f"매물 {article_id}",
        price="10,000원",
        link=f"https://m.bunjang.co.kr/products/{article_id}",
        keyword="k",
    )


class CleanupLastSeenTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = DatabaseManager(os.path.join(self.tmp.name, "t.db"))
        _, _, self.still_listed = self.db.add_listing(_item("1"))
        _, _, self.gone = self.db.add_listing(_item("2"))
        _, _, self.fresh = self.db.add_listing(_item("3"))
        self.db.conn.execute(
            "UPDATE listings SET created_at = datetime('now', '-40 days') WHERE id IN (?, ?)",
            (self.still_listed, self.gone),
        )
        self.db.conn.commit()
        self.db.touch_listings_seen([self.still_listed])  # seen again today
        self.db.conn.execute(
            "INSERT INTO listing_last_seen (listing_id, last_seen_at) VALUES (?, datetime('now', '-35 days'))",
            (self.gone,),
        )
        self.db.conn.commit()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_preview_and_cleanup_use_last_seen(self):
        preview = self.db.get_cleanup_preview(days=30, exclude_favorites=True, exclude_noted=True)
        self.assertEqual(preview["delete_count"], 1)

        deleted = self.db.cleanup_old_listings(days=30, exclude_favorites=True, exclude_noted=True)
        self.assertEqual(deleted, 1)
        remaining = {row[0] for row in self.db.conn.execute("SELECT id FROM listings")}
        self.assertEqual(remaining, {self.still_listed, self.fresh})
        orphan = self.db.conn.execute(
            "SELECT COUNT(*) FROM listing_last_seen WHERE listing_id = ?", (self.gone,)
        ).fetchone()[0]
        self.assertEqual(orphan, 0)

    def test_touch_is_idempotent_and_updates(self):
        self.db.touch_listings_seen([self.gone, self.gone])
        preview = self.db.get_cleanup_preview(days=30, exclude_favorites=True, exclude_noted=True)
        self.assertEqual(preview["delete_count"], 0)


if __name__ == "__main__":
    unittest.main()
