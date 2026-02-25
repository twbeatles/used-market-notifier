# scrapers/playwright_danggeun.py
"""Playwright-based Danggeun scraper."""

from __future__ import annotations

import asyncio
import json
import re
from urllib.parse import quote

from models import Item

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


class PlaywrightDanggeunScraper(PlaywrightScraper):
    """Danggeun scraper with JSON-LD first and DOM fallback parsing."""

    INVALID_TITLE_PATTERNS = [
        "판매완료",
        "예약중",
        "거래완료",
        "No Title",
        "광고",
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

    def safe_search(self, keyword: str, location: str = None) -> list[Item]:
        return _run_async(lambda: self._safe_search_session(keyword, location))

    async def _safe_search_session(self, keyword: str, location: str = None) -> list[Item]:
        from playwright.async_api import async_playwright

        async with async_playwright() as pw:
            browser = await self._launch_browser(pw)
            try:
                self._context = await self._create_context(browser)
                self._owned_context = True
                self._page = None
                return await super().safe_search(keyword, location)
            finally:
                try:
                    await self.close()
                finally:
                    try:
                        await browser.close()
                    except Exception:
                        pass

    @staticmethod
    def _extract_article_id(link: str) -> str | None:
        if not link:
            return None
        m = re.search(r"-(\d+)(?:/)?$", link)
        if m:
            return m.group(1)
        m = re.search(r"/(\d+)(?:\?|$)", link)
        if m:
            return m.group(1)
        return None

    @staticmethod
    def _extract_location(text: str) -> str | None:
        if not text:
            return None
        # Best-effort extraction for Korean region prefixes.
        m = re.search(
            r"(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)[^\n|,/]{0,20}",
            text,
        )
        return m.group(0).strip() if m else None

    @staticmethod
    def _normalize_price(product: dict) -> str:
        offers = product.get("offers", {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        if isinstance(offers, dict):
            raw = offers.get("price")
            if raw is not None:
                try:
                    return f"{int(float(str(raw))):,}원"
                except Exception:
                    pass
        return "가격문의"

    async def search(self, keyword: str, location: str = None) -> list[Item]:
        page = await self.get_page()
        encoded_keyword = quote(keyword)
        url = f"https://www.daangn.com/kr/buy-sell/?search={encoded_keyword}&sort=recent"

        ok = await self.navigate_with_retry(url, wait_until="domcontentloaded", max_retries=2)
        if not ok:
            return []
        await page.wait_for_timeout(1200)

        items: list[Item] = []
        seen_ids: set[str] = set()

        # 1) JSON-LD parsing (preferred)
        try:
            scripts = await page.locator("script[type='application/ld+json']").all_text_contents()
            for script_text in scripts:
                try:
                    data = json.loads(script_text)
                except Exception:
                    continue

                nodes = data if isinstance(data, list) else [data]
                for node in nodes:
                    if not isinstance(node, dict):
                        continue
                    if node.get("@type") != "ItemList":
                        continue
                    for entry in node.get("itemListElement", []):
                        product = entry.get("item", {}) if isinstance(entry, dict) else {}
                        if not product and isinstance(entry, dict):
                            product = entry
                        if not isinstance(product, dict):
                            continue

                        title = str(product.get("name", "")).strip()
                        if not self._is_valid_title(title):
                            continue

                        link = str(product.get("url", "")).strip()
                        if link.startswith("/"):
                            link = f"https://www.daangn.com{link}"
                        article_id = self._extract_article_id(link)
                        if not article_id or article_id in seen_ids:
                            continue

                        seen_ids.add(article_id)
                        items.append(
                            Item(
                                platform="danggeun",
                                article_id=article_id,
                                title=title,
                                price=self._normalize_price(product),
                                link=link,
                                keyword=keyword,
                                thumbnail=product.get("image"),
                                location=self._extract_location(str(product.get("description", ""))),
                            )
                        )
                if items:
                    return items
        except Exception:
            pass

        # 2) DOM card parsing fallback
        cards = page.locator("a[href*='/kr/buy-sell/']")
        count = min(await cards.count(), 80)
        for i in range(count):
            card = cards.nth(i)
            try:
                link = await card.get_attribute("href")
                if not link or "search=" in link:
                    continue
                if link.startswith("/"):
                    link = f"https://www.daangn.com{link}"

                article_id = self._extract_article_id(link)
                if not article_id or article_id in seen_ids:
                    continue

                text = (await card.inner_text() or "").strip()
                if not text:
                    continue
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                title = lines[0] if lines else ""
                if not self._is_valid_title(title):
                    continue

                price = "가격문의"
                for line in lines[1:]:
                    if "원" in line or ("만" in line and any(ch.isdigit() for ch in line)):
                        price = line
                        break

                thumbnail = None
                try:
                    thumbnail = await card.locator("img").first.get_attribute("src")
                except Exception:
                    thumbnail = None

                seen_ids.add(article_id)
                items.append(
                    Item(
                        platform="danggeun",
                        article_id=article_id,
                        title=title,
                        price=price,
                        link=link,
                        keyword=keyword,
                        thumbnail=thumbnail,
                        location=self._extract_location(text),
                    )
                )
            except Exception:
                continue

        return items
