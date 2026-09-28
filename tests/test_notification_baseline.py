"""Regression: per-(search signature, platform) notification baseline and burst limit (ISSUE-002)."""

import asyncio
import concurrent.futures
import os
import tempfile
import unittest

from db import DatabaseManager
from models import AppSettings, Item, SearchKeyword
from monitor_engine import MonitorEngine
from storage.baselines import keyword_search_signature


class _Settings:
    def __init__(self, keywords):
        self.settings = AppSettings(notifications_enabled=True, scraper_mode="selenium_only")
        self.settings.keywords = keywords


class _CatalogScraper:
    """Returns `catalog[keyword]` items; tests mutate the catalog between cycles."""

    def __init__(self, catalog):
        self.catalog = catalog
        self.fail = False

    def safe_search(self, keyword, location=None):
        if self.fail:
            raise RuntimeError("temporary network failure")
        return [Item(**vars_) for vars_ in self.catalog.get(keyword, [])]

    def enrich_item(self, item):
        return item

    def is_healthy(self):
        return True

    def close(self):
        return None


def _entry(keyword: str, i: int) -> dict:
    return dict(
        platform="bunjang",
        article_id=f"{keyword}-{i}",
        title=f"{keyword} 판매합니다 상태 좋은 매물 번호 {i}",
        price=f"{(i + 1) * 13_579:,}원",
        link=f"https://m.bunjang.co.kr/products/{abs(hash(keyword)) % 10_000}{i:04d}",
        keyword=keyword,
        seller=f"seller{i}",
        location="서울",
    )


class NotificationBaselineTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = DatabaseManager(os.path.join(self.tmp.name, "t.db"))
        self.catalog = {"아이폰": [_entry("아이폰", i) for i in range(5)]}
        self.scraper = _CatalogScraper(self.catalog)
        self.sent: list[tuple[str, bool]] = []
        self.system: list[str] = []

    async def asyncTearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def _engine(self, keywords, suppress_initial=True) -> MonitorEngine:
        engine = MonitorEngine(_Settings(keywords), db=self.db, suppress_initial_notifications=suppress_initial)
        engine._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        engine.primary_scrapers["bunjang"] = self.scraper
        engine.primary_scraper_kind["bunjang"] = "selenium"

        async def _ensure(platform, use_fallback=False):
            return not use_fallback

        async def _send(item, is_price_change=False, old_price=None, new_price=None, listing_id=None):
            self.sent.append((item.article_id, is_price_change))

        async def _system(text):
            self.system.append(text)

        async def _no_sleep(_seconds):
            return None

        engine._ensure_scraper = _ensure
        engine.send_notifications = _send
        engine._send_system_message = _system
        engine._sleep_or_stop = _no_sleep
        return engine

    def _shutdown(self, engine):
        if engine._executor is not None:
            engine._executor.shutdown(wait=True, cancel_futures=True)

    async def test_keyword_added_mid_session_does_not_flood(self):
        keywords = [SearchKeyword(keyword="아이폰", platforms=["bunjang"])]
        engine = self._engine(keywords)
        await engine.run_cycle()
        await engine.run_cycle()
        self.assertEqual(self.sent, [])

        self.catalog["맥북"] = [_entry("맥북", i) for i in range(40)]
        keywords.append(SearchKeyword(keyword="맥북", platforms=["bunjang"]))
        await engine.run_cycle()
        self.assertEqual(self.sent, [], "existing listings of a new keyword must be a silent baseline")

        self.catalog["맥북"].append(_entry("맥북", 99))
        await engine.run_cycle()
        self.assertEqual(self.sent, [("맥북-99", False)])
        self._shutdown(engine)

    async def test_failed_first_search_does_not_establish_baseline(self):
        keywords = [SearchKeyword(keyword="아이폰", platforms=["bunjang"])]
        engine = self._engine(keywords, suppress_initial=False)
        self.scraper.fail = True
        await engine.run_cycle()
        sig = keyword_search_signature(keywords[0])
        self.assertFalse(self.db.has_search_baseline(sig, "bunjang"))

        self.scraper.fail = False
        await engine.run_cycle()
        self.assertEqual(self.sent, [])
        self.assertTrue(self.db.has_search_baseline(sig, "bunjang"))
        self._shutdown(engine)

    async def test_restarted_engine_notifies_items_that_appeared_meanwhile(self):
        keywords = [SearchKeyword(keyword="아이폰", platforms=["bunjang"])]
        first = self._engine(keywords)
        await first.run_cycle()
        self._shutdown(first)

        self.catalog["아이폰"].append(_entry("아이폰", 50))
        restarted = self._engine(keywords, suppress_initial=False)
        await restarted.run_cycle()
        self.assertEqual(self.sent, [("아이폰-50", False)])
        self._shutdown(restarted)

    async def test_filter_change_creates_new_baseline(self):
        kw = SearchKeyword(keyword="아이폰", platforms=["bunjang"], max_price=30_000)
        engine = self._engine([kw])
        await engine.run_cycle()
        kw.max_price = 0  # widen the filter: previously filtered-out listings become visible
        await engine.run_cycle()
        self.assertEqual(self.sent, [])
        self._shutdown(engine)

    async def test_burst_limit_sends_summary(self):
        keywords = [SearchKeyword(keyword="아이폰", platforms=["bunjang"])]
        engine = self._engine(keywords, suppress_initial=False)
        await engine.run_cycle()  # baseline
        self.catalog["아이폰"].extend(_entry("아이폰", 100 + i) for i in range(20))
        await engine.run_cycle()
        self.assertEqual(len(self.sent), engine.NOTIFICATION_BURST_LIMIT)
        self.assertEqual(len(self.system), 1)
        self.assertIn("5", self.system[0])
        self._shutdown(engine)

    async def test_new_item_callback_marks_suppressed_items(self):
        keywords = [SearchKeyword(keyword="아이폰", platforms=["bunjang"])]
        engine = self._engine(keywords, suppress_initial=False)
        seen: list[bool] = []
        engine.on_new_item = lambda item: seen.append(item.notification_suppressed)
        await engine.run_cycle()
        self.assertTrue(seen and all(seen))
        self.catalog["아이폰"].append(_entry("아이폰", 77))
        seen.clear()
        await engine.run_cycle()
        self.assertEqual(seen, [False])
        self._shutdown(engine)


if __name__ == "__main__":
    unittest.main()
