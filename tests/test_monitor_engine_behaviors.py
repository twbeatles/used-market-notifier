import concurrent.futures
import os
import tempfile
import unittest

from db import DatabaseManager
from models import AppSettings, Item, SearchKeyword
from monitor_engine import MonitorEngine


class _SettingsWrapper:
    def __init__(self, **overrides):
        settings = AppSettings(
            notifications_enabled=overrides.pop("notifications_enabled", True),
            metadata_enrichment_enabled=overrides.pop("metadata_enrichment_enabled", False),
        )
        for key, value in overrides.items():
            setattr(settings, key, value)
        self.settings = settings


class _FakeScraper:
    def __init__(self, items=None):
        self.items = list(items or [])
        self.calls = 0
        self.enrich_calls = 0

    def safe_search(self, keyword: str, location: str | None = None):
        _ = (keyword, location)
        self.calls += 1
        return list(self.items)

    def enrich_item(self, item: Item) -> Item:
        self.enrich_calls += 1
        return Item(
            platform=item.platform,
            article_id=item.article_id,
            title=item.title,
            price=item.price,
            link=item.link,
            keyword=item.keyword,
            thumbnail=item.thumbnail,
            seller=item.seller or f"seller-{item.article_id}",
            location=item.location or "Seoul",
            price_numeric=item.price_numeric,
        )

    def is_healthy(self):
        return True

    def close(self):
        return None


class TestMonitorEngineBehaviors(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        self.db = DatabaseManager(self.db_path)

    async def asyncTearDown(self):
        try:
            self.db.close()
        finally:
            self.tmp.cleanup()

    async def _make_engine(self, **settings_overrides) -> MonitorEngine:
        engine = MonitorEngine(_SettingsWrapper(**settings_overrides), db=self.db)
        engine._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        async def _always_ready(platform: str, use_fallback: bool = False):
            _ = (platform, use_fallback)
            return True

        engine._ensure_scraper = _always_ready
        return engine

    async def test_first_run_skips_new_and_price_change_notifications(self):
        existing = Item(
            platform="danggeun",
            article_id="a1",
            title="existing item",
            price="10,000원",
            link="https://example.com/a1",
            keyword="test",
        )
        self.db.add_listing(existing)

        changed = Item(
            platform="danggeun",
            article_id="a1",
            title="existing item",
            price="9,000원",
            link="https://example.com/a1",
            keyword="test",
        )
        new_item = Item(
            platform="danggeun",
            article_id="a2",
            title="new item",
            price="20,000원",
            link="https://example.com/a2",
            keyword="test",
        )

        engine = await self._make_engine(notifications_enabled=True)
        scraper = _FakeScraper(items=[changed, new_item])
        engine.primary_scrapers["danggeun"] = scraper
        engine.primary_scraper_kind["danggeun"] = "playwright"
        engine.is_first_run = True

        send_calls = []

        async def _capture(*args, **kwargs):
            send_calls.append((args, kwargs))

        engine.send_notifications = _capture

        kw = SearchKeyword(keyword="test", platforms=["danggeun"])
        new_count = await engine.search_keyword(kw, blocked_set=set())
        self.assertEqual(new_count, 1)
        self.assertEqual(send_calls, [])

        if engine._executor is not None:
            engine._executor.shutdown(wait=True, cancel_futures=True)

    async def test_metadata_enrichment_is_limited_to_ten_items(self):
        engine = await self._make_engine(notifications_enabled=False, metadata_enrichment_enabled=True)
        items = [
            Item(
                platform="danggeun",
                article_id=f"a{i}",
                title=f"item number {i}",
                price=f"{10_000 + i:,}원",
                link=f"https://example.com/a{i}",
                keyword="test",
            )
            for i in range(12)
        ]
        scraper = _FakeScraper(items=items)
        engine.primary_scrapers["danggeun"] = scraper
        engine.primary_scraper_kind["danggeun"] = "playwright"

        kw = SearchKeyword(keyword="test", platforms=["danggeun"])
        new_count = await engine.search_keyword(kw, blocked_set=set())
        self.assertEqual(new_count, 12)
        self.assertEqual(scraper.enrich_calls, 10)

        with self.db.lock:
            cur = self.db.conn.cursor()
            cur.execute("SELECT COUNT(*) AS count FROM listings WHERE seller IS NOT NULL")
            enriched_count = cur.fetchone()["count"]
        self.assertEqual(enriched_count, 10)

        if engine._executor is not None:
            engine._executor.shutdown(wait=True, cancel_futures=True)


if __name__ == "__main__":
    unittest.main()
