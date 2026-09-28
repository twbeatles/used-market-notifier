# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false
"""Regression: lazy fallback scrapers and no primary re-creation during enrichment (ISSUE-005)."""

import concurrent.futures
import os
import tempfile
import unittest

from db import DatabaseManager
from models import AppSettings, Item
from monitor_engine import MonitorEngine
from scrapers import ScraperDependencyUnavailable


class _Settings:
    def __init__(self, mode: str):
        self.settings = AppSettings(notifications_enabled=False, scraper_mode=mode)


class _Scraper:
    def __init__(self, kind: str):
        self.kind = kind
        self.closed = False

    def safe_search(self, keyword, location=None):
        return []

    def enrich_item(self, item):
        return item  # detail page had no seller/location

    def is_healthy(self):
        return True

    def close(self):
        self.closed = True


def _items(n: int) -> list[Item]:
    return [
        Item(
            platform="joonggonara",
            article_id=str(i),
            title=f"t{i}",
            price="1",
            link=f"https://cafe.naver.com/joonggonara/{i}",
            keyword="k",
        )
        for i in range(n)
    ]


class FallbackLifecycleTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = DatabaseManager(os.path.join(self.tmp.name, "t.db"))
        self.created: list[_Scraper] = []

    async def asyncTearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def _engine(self, mode: str, unavailable: tuple[str, ...] = ()) -> MonitorEngine:
        engine = MonitorEngine(_Settings(mode), db=self.db)
        engine._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        def _create(platform, headless, kind):
            if kind in unavailable:
                raise ScraperDependencyUnavailable(f"{kind} unavailable")
            scraper = _Scraper(kind)
            self.created.append(scraper)
            return scraper

        engine._create_scraper = _create
        return engine

    async def test_enrichment_without_fallback_never_recreates_primary(self):
        engine = self._engine("selenium_only")
        await engine.initialize_scrapers(["joonggonara"])
        created_before = len(self.created)
        await engine._enrich_items_with_budget(
            "joonggonara", "k", _items(10), 10, phase="prefilter", predicate=lambda _: True, force=True
        )
        self.assertEqual(len(self.created), created_before)
        self.assertFalse(any(s.closed for s in self.created))
        engine._executor.shutdown(wait=True)

    async def test_fallback_is_created_lazily(self):
        engine = self._engine("playwright_primary")
        await engine.initialize_scrapers(["joonggonara"])
        self.assertEqual([s.kind for s in self.created], ["playwright"])
        self.assertNotIn("joonggonara", engine.fallback_scrapers)
        self.assertTrue(engine._has_fallback_option("joonggonara"))

        self.assertTrue(await engine._ensure_scraper("joonggonara", use_fallback=True))
        self.assertEqual([s.kind for s in self.created], ["playwright", "selenium"])
        self.assertTrue(await engine._ensure_scraper("joonggonara", use_fallback=True))
        self.assertEqual(len(self.created), 2, "an existing healthy fallback must be reused")
        engine._executor.shutdown(wait=True)

    async def test_failed_fallback_enters_cooldown_and_keeps_primary(self):
        engine = self._engine("playwright_primary", unavailable=("selenium",))
        await engine.initialize_scrapers(["joonggonara"])
        primary = engine.primary_scrapers["joonggonara"]

        self.assertFalse(await engine._ensure_scraper("joonggonara", use_fallback=True))
        self.assertFalse(engine._has_fallback_option("joonggonara"))
        self.assertFalse(await engine._ensure_scraper("joonggonara", use_fallback=True))
        self.assertIs(engine.primary_scrapers["joonggonara"], primary)
        self.assertFalse(primary.closed)
        engine._executor.shutdown(wait=True)

    async def test_unhealthy_fallback_is_replaced_alone(self):
        engine = self._engine("playwright_primary")
        await engine.initialize_scrapers(["joonggonara"])
        await engine._ensure_scraper("joonggonara", use_fallback=True)
        primary = engine.primary_scrapers["joonggonara"]
        old_fallback = engine.fallback_scrapers["joonggonara"]
        old_fallback.is_healthy = lambda: False

        self.assertTrue(await engine._ensure_scraper("joonggonara", use_fallback=True))
        self.assertTrue(old_fallback.closed)
        self.assertIsNot(engine.fallback_scrapers["joonggonara"], old_fallback)
        self.assertIs(engine.primary_scrapers["joonggonara"], primary)
        self.assertFalse(primary.closed)
        engine._executor.shutdown(wait=True)


if __name__ == "__main__":
    unittest.main()
