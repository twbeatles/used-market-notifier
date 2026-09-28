"""Regression: unknown-price placeholders, stale price_numeric, sticky sale status (ISSUE-004/011)."""

import os
import tempfile
import unittest

from db import DatabaseManager
from engine.metadata import MetadataEnrichmentMixin
from models import Item


def _jn(price: str, article_id: str = "123456") -> Item:
    return Item(
        platform="joonggonara",
        article_id=article_id,
        title="아이패드 프로 11 팝니다",
        price=price,
        link=f"https://cafe.naver.com/joonggonara/{article_id}",
        keyword="아이패드",
    )


def _bj(status):
    return Item(
        platform="bunjang",
        article_id="555",
        title="맥북 에어 M2",
        price="90만원",
        link="https://m.bunjang.co.kr/products/555",
        keyword="맥북",
        sale_status=status,
    )


class ListingPriceStatusRulesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = DatabaseManager(os.path.join(self.tmp.name, "t.db"))

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def _row(self, article_id: str) -> dict:
        row = self.db.conn.execute(
            "SELECT price, price_numeric, sale_status FROM listings WHERE article_id = ?", (article_id,)
        ).fetchone()
        return dict(row)

    def _history_count(self) -> int:
        return self.db.conn.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]

    def test_placeholder_round_trip_records_no_price_change(self):
        changes = []
        for price in ("35만원", "가격문의", "35만원", "가격문의", ""):
            _, change, _ = self.db.add_listing(_jn(price))
            changes.append(change)
        self.assertEqual(changes, [None] * 5)
        self.assertEqual(self._history_count(), 0)
        self.assertEqual(self._row("123456")["price"], "35만원")
        self.assertEqual(self._row("123456")["price_numeric"], 350000)

    def test_unknown_to_known_fills_price_silently(self):
        self.db.add_listing(_jn("가격문의"))
        _, change, _ = self.db.add_listing(_jn("35만원"))
        self.assertIsNone(change)
        self.assertEqual(self._history_count(), 0)
        self.assertEqual(self._row("123456"), {"price": "35만원", "price_numeric": 350000, "sale_status": "for_sale"})

    def test_known_to_free_is_a_real_price_change(self):
        self.db.add_listing(_jn("1만원"))
        _, change, _ = self.db.add_listing(_jn("무료나눔"))
        self.assertIsNotNone(change)
        self.assertEqual(change["new_numeric"], 0)
        self.assertEqual(self._history_count(), 1)

    def test_known_to_known_change_still_recorded(self):
        self.db.add_listing(_jn("35만원"))
        _, change, _ = self.db.add_listing(_jn("30만원"))
        self.assertEqual((change["old_numeric"], change["new_numeric"]), (350000, 300000))

    def test_enrichment_refreshes_stale_price_numeric(self):
        before = _jn("가격문의", "777")
        before.parse_price()  # SearchKeyword.matches() caches 0 before postfilter enrichment
        after = _jn("35만원", "777")
        after.price_numeric = before.price_numeric  # scrapers carry the cached value over
        refreshed = MetadataEnrichmentMixin._refresh_price_numeric(before, after)
        self.db.add_listing(refreshed)
        self.assertEqual(self._row("777")["price_numeric"], 350000)

    def test_explicit_sold_status_is_sticky_without_new_evidence(self):
        self.db.add_listing(_bj(None))
        self.db.add_listing(_bj("SOLD_OUT"))
        self.db.add_listing(_bj(None))
        self.assertEqual(self._row("555")["sale_status"], "sold")
        history = self.db.conn.execute("SELECT old_status, new_status FROM sale_status_history").fetchall()
        self.assertEqual([tuple(r) for r in history], [("for_sale", "sold")])

    def test_title_evidence_still_changes_status(self):
        self.db.add_listing(_bj(None))
        item = _bj(None)
        item.title = "[판매완료] 맥북 에어 M2"
        self.db.add_listing(item)
        self.assertEqual(self._row("555")["sale_status"], "sold")

    def test_new_listing_without_evidence_defaults_to_for_sale(self):
        self.db.add_listing(_bj(None))
        self.assertEqual(self._row("555")["sale_status"], "for_sale")


if __name__ == "__main__":
    unittest.main()
