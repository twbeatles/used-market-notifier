import os
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


if __name__ == "__main__":
    unittest.main()
