import os
import tempfile
import unittest

from db import DatabaseManager


class TestBlockedSellers(unittest.TestCase):
    def test_get_blocked_sellers_has_created_at(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            db = DatabaseManager(db_path)
            try:
                db.add_seller_filter("seller1", "danggeun", is_blocked=True)
                sellers = db.get_blocked_sellers()
                self.assertTrue(sellers)
                self.assertIn("created_at", sellers[0])
                self.assertTrue(sellers[0]["created_at"])
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()

