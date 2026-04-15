# scrapers/playwright_joonggonara.py
"""Playwright-based Joonggonara scraper using Naver search results."""

from __future__ import annotations

import asyncio
from urllib.parse import quote

from models import Item

from .marketplace_parsers import parse_joonggonara_detail_text, parse_joonggonara_search_items
from .playwright_base import PlaywrightScraper


def _run_async(coro_factory):
    """Run an async coroutine from synchronous scraper entrypoints."""
    try:
        return asyncio.run(coro_factory())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro_factory())
        finally:
            loop.close()


class PlaywrightJoonggonaraScraper(PlaywrightScraper):
    """Joonggonara scraper using link classification and iframe detail enrichment."""

    def __init__(self, headless: bool = True, disable_images: bool = True):
        super().__init__(
            headless=headless,
            disable_images=disable_images,
            use_stealth=True,
            debug_mode=False,
        )

    def is_healthy(self) -> bool:
        return True

    def safe_search(self, keyword: str, location: str | None = None) -> list[Item]:
        return _run_async(lambda: self._safe_search_session(keyword, location))

    async def _safe_search_session(self, keyword: str, location: str | None = None) -> list[Item]:
        from playwright.async_api import async_playwright

        async with async_playwright() as pw:
            browser = await self._launch_browser(pw)
            try:
                self._context = await self._create_context(browser)
                self._owned_context = True
                self._page = None
                return await super()._safe_search_async(keyword, location)
            finally:
                try:
                    await self.close()
                finally:
                    try:
                        await browser.close()
                    except Exception:
                        pass

    @staticmethod
    def _build_article_url(article_id: str, fallback_link: str) -> str:
        if str(article_id or "").isdigit():
            return f"https://cafe.naver.com/joonggonara/{article_id}"
        return fallback_link

    async def _extract_detail_body_text(self, page) -> str:
        try:
            await page.wait_for_selector("iframe#cafe_main", timeout=4000)
        except Exception:
            pass

        for _ in range(10):
            try:
                frame = page.frame(name="cafe_main")
                if frame is None:
                    frame = next(
                        (
                            current
                            for current in page.frames
                            if "/cafes/10050146/articles/" in str(current.url or "")
                        ),
                        None,
                    )
                if frame is not None:
                    body_text = (await frame.locator("body").inner_text(timeout=1500) or "").strip()
                    if body_text:
                        return body_text
            except Exception:
                pass
            await page.wait_for_timeout(250)

        try:
            return (await page.locator("body").inner_text() or "").strip()
        except Exception:
            return ""

    async def _enrich_item_async(self, item: Item) -> Item:
        if not item.link:
            return item

        page = await self.get_page()
        target_url = self._build_article_url(item.article_id, item.link)
        ok = await self.navigate_with_retry(target_url, wait_until="domcontentloaded", max_retries=2)
        if not ok:
            return item
        await page.wait_for_timeout(900)

        parsed = parse_joonggonara_detail_text(await self._extract_detail_body_text(page))
        return Item(
            platform=item.platform,
            article_id=item.article_id,
            title=item.title,
            price=parsed.get("price") or item.price,
            link=item.link,
            keyword=item.keyword,
            thumbnail=item.thumbnail,
            seller=parsed.get("seller") or item.seller,
            location=parsed.get("location") or item.location,
            sale_status=item.sale_status,
            price_numeric=item.price_numeric,
        )

    async def _enrich_item_session(self, item: Item) -> Item:
        from playwright.async_api import async_playwright

        async with async_playwright() as pw:
            browser = await self._launch_browser(pw)
            try:
                self._context = await self._create_context(browser)
                self._owned_context = True
                self._page = None
                return await self._enrich_item_async(item)
            finally:
                try:
                    await self.close()
                finally:
                    try:
                        await browser.close()
                    except Exception:
                        pass

    def enrich_item(self, item: Item) -> Item:
        return _run_async(lambda: self._enrich_item_session(item))

    async def search(self, keyword: str, location: str | None = None) -> list[Item]:
        page = await self.get_page()
        encoded = quote(keyword)
        url = (
            "https://search.naver.com/search.naver"
            f"?where=article&query={encoded}%20site%3Acafe.naver.com%2Fjoonggonara"
        )

        ok = await self.navigate_with_retry(url, wait_until="domcontentloaded", max_retries=2)
        if not ok:
            return []
        await page.wait_for_timeout(1200)

        try:
            await page.wait_for_selector("a[href*='cafe.naver.com/joonggonara']", timeout=5000)
        except Exception:
            pass

        items = parse_joonggonara_search_items(await page.content(), keyword)
        self.logger.info(f"Joonggonara search classified {len(items)} items for '{keyword}'")
        return items
