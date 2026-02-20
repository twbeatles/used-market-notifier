import os
import tempfile
import unittest

from db import DatabaseManager
from models import Item


class TestDashboardSnapshot(unittest.TestCase):
    def test_snapshot_and_cache_invalidation(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            db = DatabaseManager(db_path)
            try:
                item = Item(
                    platform="danggeun",
                    article_id="a1",
                    title="맥북 테스트",
                    price="100,000원",
                    link="https://example.com/a1",
                    keyword="맥북",
                )
                is_new, _, _ = db.add_listing(item)
                self.assertTrue(is_new)

                # Create one price change and one search stat row for snapshot sections.
                item_changed = Item(
                    platform="danggeun",
                    article_id="a1",
                    title="맥북 테스트",
                    price="90,000원",
                    link="https://example.com/a1",
                    keyword="맥북",
                )
                db.add_listing(item_changed)
                db.record_search_stats("맥북", "danggeun", 3, 1)

                snap1 = db.get_dashboard_snapshot()
                snap2 = db.get_dashboard_snapshot()
                self.assertEqual(snap1["total"], 1)
                self.assertIs(snap1, snap2)  # served from TTL cache
                self.assertGreaterEqual(len(snap1["price_changes"]), 1)
                self.assertGreaterEqual(len(snap1["daily_stats"]), 1)

                # Any write should invalidate snapshot cache.
                item2 = Item(
                    platform="bunjang",
                    article_id="b1",
                    title="아이폰 테스트",
                    price="800,000원",
                    link="https://example.com/b1",
                    keyword="아이폰",
                )
                db.add_listing(item2)
                snap3 = db.get_dashboard_snapshot()
                self.assertEqual(snap3["total"], 2)
                self.assertIsNot(snap2, snap3)
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
