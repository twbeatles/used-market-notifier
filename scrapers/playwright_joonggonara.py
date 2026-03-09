# scrapers/playwright_joonggonara.py
"""Playwright-based Joonggonara scraper using Naver search results."""

from __future__ import annotations

import asyncio
from urllib.parse import quote

from models import Item

from .joonggonara import JoonggonaraScraper as SeleniumJoonggonaraScraper
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
    """Joonggonara scraper with title-link selector priority and cafe-link fallback."""

    INVALID_TITLE_PATTERNS = [
        "판매완료",
        "예약중",
        "거래완료",
        "No Title",
        "광고",
        "배송비포함",
    ]

    def __init__(self, headless: bool = True, disable_images: bool = True):
        super().__init__(
            headless=headless,
            disable_images=disable_images,
            use_stealth=True,
            debug_mode=False,
        )

    def is_healthy(self) -> bool:
        # This scraper uses one-shot sessions per search.
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

        selectors = [
            "a.title_link",
            "a.api_txt_lines.total_tit",
            "ul.lst_total > li a.link_tit",
            "div.total_area a.api_txt_lines",
        ]

        items: list[Item] = []
        seen_ids: set[str] = set()

        for selector in selectors:
            locator = page.locator(selector)
            count = await locator.count()
            if count <= 0:
                continue

            for i in range(min(count, 120)):
                el = locator.nth(i)
                try:
                    link = (await el.get_attribute("href") or "").strip()
                    if not link:
                        continue
                    if "joonggonara" not in link and "cafe.naver.com" not in link:
                        continue

                    raw_title = (await el.inner_text() or "").strip()
                    title = " ".join(raw_title.splitlines()[0].split()) if raw_title else ""
                    if not self._is_valid_title(title):
                        continue

                    article_id = SeleniumJoonggonaraScraper.extract_article_id(link)
                    if article_id in seen_ids:
                        continue

                    seen_ids.add(article_id)
                    items.append(
                        Item(
                            platform="joonggonara",
                            article_id=article_id,
                            title=title,
                            price="가격문의",
                            link=link,
                            keyword=keyword,
                            thumbnail=None,
                        )
                    )
                except Exception:
                    continue

            if items:
                return items

        # Fallback: any joonggonara cafe links.
        fallback_links = page.locator("a[href*='cafe.naver.com/joonggonara']")
        fallback_count = min(await fallback_links.count(), 120)
        for i in range(fallback_count):
            el = fallback_links.nth(i)
            try:
                link = (await el.get_attribute("href") or "").strip()
                title = " ".join((await el.inner_text() or "").split())
                if not link or not title:
                    continue
                if not self._is_valid_title(title):
                    continue

                article_id = SeleniumJoonggonaraScraper.extract_article_id(link)
                if article_id in seen_ids:
                    continue
                seen_ids.add(article_id)

                items.append(
                    Item(
                        platform="joonggonara",
                        article_id=article_id,
                        title=title,
                        price="가격문의",
                        link=link,
                        keyword=keyword,
                        thumbnail=None,
                    )
                )
            except Exception:
                continue

        return items
