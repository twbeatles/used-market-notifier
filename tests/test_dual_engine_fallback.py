import asyncio
import concurrent.futures
import os
import tempfile
import unittest

from db import DatabaseManager
from models import AppSettings, Item, SearchKeyword
from monitor_engine import MonitorEngine


class _SettingsWrapper:
    def __init__(self, fallback_on_empty_results: bool = True):
        self.settings = AppSettings(
            notifications_enabled=False,
            scraper_mode="playwright_primary",
            fallback_on_empty_results=fallback_on_empty_results,
            max_fallback_per_cycle=3,
        )


class _FakeScraper:
    def __init__(self, items=None, exc: Exception | None = None):
        self.items = list(items or [])
        self.exc = exc
        self.calls = 0

    def safe_search(self, keyword: str, location: str | None = None):
        self.calls += 1
        if self.exc is not None:
            raise self.exc
        return list(self.items)

    def enrich_item(self, item: Item):
        return item

    def is_healthy(self):
        return True

    def close(self):
        return None


def _item(platform: str, article_id: str, title: str, link: str) -> Item:
    return Item(
        platform=platform,
        article_id=article_id,
        title=title,
        price="10,000원",
        link=link,
        keyword="테스트",
    )


class TestDualEngineFallback(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        self.db = DatabaseManager(self.db_path)

    async def asyncTearDown(self):
        try:
            self.db.close()
        finally:
            self.tmp.cleanup()

    async def _make_engine(self) -> MonitorEngine:
        engine = MonitorEngine(_SettingsWrapper(), db=self.db)
        engine._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        async def _always_ready(platform: str, use_fallback: bool = False):
            return True

        engine._ensure_scraper = _always_ready
        return engine

    async def _make_engine_with_settings(self, settings_wrapper: _SettingsWrapper) -> MonitorEngine:
        engine = MonitorEngine(settings_wrapper, db=self.db)
        engine._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        async def _always_ready(platform: str, use_fallback: bool = False):
            return True

        engine._ensure_scraper = _always_ready
        return engine

    async def test_primary_success_no_fallback(self):
        engine = await self._make_engine()
        primary = _FakeScraper(items=[_item("danggeun", "a1", "아이폰", "https://e/a1")])
        fallback = _FakeScraper(items=[_item("danggeun", "a2", "맥북", "https://e/a2")])

        engine.primary_scrapers["danggeun"] = primary
        engine.primary_scraper_kind["danggeun"] = "playwright"
        engine.fallback_scrapers["danggeun"] = fallback
        engine.fallback_scraper_kind["danggeun"] = "selenium"

        kw = SearchKeyword(keyword="아이폰", platforms=["danggeun"])
        new_count = await engine.search_keyword(kw, blocked_set=set())

        self.assertEqual(new_count, 1)
        self.assertEqual(primary.calls, 1)
        self.assertEqual(fallback.calls, 0)
        if engine._executor is not None:
            engine._executor.shutdown(wait=True, cancel_futures=True)

    async def test_primary_exception_fallback_success(self):
        engine = await self._make_engine()
        primary = _FakeScraper(exc=RuntimeError("primary failed"))
        fallback = _FakeScraper(items=[_item("danggeun", "a10", "아이폰", "https://e/a10")])

        engine.primary_scrapers["danggeun"] = primary
        engine.primary_scraper_kind["danggeun"] = "playwright"
        engine.fallback_scrapers["danggeun"] = fallback
        engine.fallback_scraper_kind["danggeun"] = "selenium"

        kw = SearchKeyword(keyword="아이폰", platforms=["danggeun"])
        new_count = await engine.search_keyword(kw, blocked_set=set())

        self.assertEqual(new_count, 1)
        self.assertEqual(primary.calls, 1)
        self.assertEqual(fallback.calls, 1)
        if engine._executor is not None:
            engine._executor.shutdown(wait=True, cancel_futures=True)

    async def test_primary_exception_fallback_even_when_empty_fallback_disabled(self):
        engine = await self._make_engine_with_settings(_SettingsWrapper(fallback_on_empty_results=False))
        primary = _FakeScraper(exc=RuntimeError("primary failed"))
        fallback = _FakeScraper(items=[_item("danggeun", "a11", "item", "https://e/a11")])

        engine.primary_scrapers["danggeun"] = primary
        engine.primary_scraper_kind["danggeun"] = "playwright"
        engine.fallback_scrapers["danggeun"] = fallback
        engine.fallback_scraper_kind["danggeun"] = "selenium"

        kw = SearchKeyword(keyword="item", platforms=["danggeun"])
        new_count = await engine.search_keyword(kw, blocked_set=set())

        self.assertEqual(new_count, 1)
        self.assertEqual(primary.calls, 1)
        self.assertEqual(fallback.calls, 1)
        if engine._executor is not None:
            engine._executor.shutdown(wait=True, cancel_futures=True)

    async def test_primary_empty_fallback_success(self):
        engine = await self._make_engine()
        primary = _FakeScraper(items=[])
        fallback = _FakeScraper(items=[_item("danggeun", "a20", "맥북", "https://e/a20")])

        engine.primary_scrapers["danggeun"] = primary
        engine.primary_scraper_kind["danggeun"] = "playwright"
        engine.fallback_scrapers["danggeun"] = fallback
        engine.fallback_scraper_kind["danggeun"] = "selenium"

        kw = SearchKeyword(keyword="맥북", platforms=["danggeun"])
        new_count = await engine.search_keyword(kw, blocked_set=set())

        self.assertEqual(new_count, 1)
        self.assertEqual(primary.calls, 1)
        self.assertEqual(fallback.calls, 1)
        if engine._executor is not None:
            engine._executor.shutdown(wait=True, cancel_futures=True)

    def test_dedupe_by_article_id_then_url(self):
        rows = [
            _item("danggeun", "a1", "t1", "https://e/u1"),
            _item("danggeun", "a1", "t1-dup", "https://e/u1x"),
            _item("danggeun", "a2", "t2-url-dup", "https://e/u1"),
            _item("danggeun", "a3", "t3", "https://e/u3"),
        ]
        merged = MonitorEngine._dedupe_items(rows)
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0].article_id, "a1")
        self.assertEqual(merged[1].article_id, "a3")


if __name__ == "__main__":
    unittest.main()
