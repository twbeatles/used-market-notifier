# scrapers/playwright_bunjang.py
"""Playwright-based Bunjang scraper."""

from __future__ import annotations

import asyncio
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


class PlaywrightBunjangScraper(PlaywrightScraper):
    """Bunjang scraper with data-pid priority and link fallback."""

    BADGE_LINES = {"배송비포함", "검수가능"}
    UNKNOWN_LOCATION_TEXTS = {"지역정보 없음", "지역 정보 없음"}
    MAX_RESULTS = 120

    INVALID_TITLE_PATTERNS = [
        "\ud310\ub9e4\uc644\ub8cc",  # 판매완료
        "\uc608\uc57d\uc911",  # 예약중
        "\uac70\ub798\uc644\ub8cc",  # 거래완료
        "\ubc30\uc1a1\ube44\ud3ec\ud568",  # 배송비포함
        "\uad11\uace0",  # 광고
        "no title",
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
    def _parse_price(text: str) -> str:
        if not text:
            return "N/A"
        digits = re.sub(r"[^\d]", "", text)
        if not digits:
            return "N/A"
        return f"{int(digits):,}\uc6d0"

    @classmethod
    def _normalize_location(cls, text: str) -> str | None:
        value = str(text or "").strip()
        if not value:
            return None
        compact = value.replace(" ", "")
        if compact in {"지역정보없음"} or value in cls.UNKNOWN_LOCATION_TEXTS:
            return None
        return value

    @staticmethod
    def _looks_like_time_line(text: str) -> bool:
        s = str(text or "").strip()
        if not s:
            return False
        return any(token in s for token in ("방금", "초 전", "분 전", "시간 전", "일 전", "주 전", "달 전", "끌올"))

    @classmethod
    def _parse_card_text_fallback(cls, text: str) -> tuple[str, str, str | None]:
        lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
        cleaned = [line for line in lines if line not in cls.BADGE_LINES and line != "·"]

        if not cleaned:
            return "", "N/A", None

        title = cleaned[0]
        price = "N/A"
        price_idx = -1
        for idx, line in enumerate(cleaned):
            compact = line.replace(",", "").replace(" ", "")
            if compact.isdigit():
                price = f"{int(compact):,}원"
                price_idx = idx
                break
            if compact.endswith("원") and compact[:-1].replace(",", "").isdigit():
                digits = "".join(ch for ch in compact if ch.isdigit())
                if digits:
                    price = f"{int(digits):,}원"
                    price_idx = idx
                    break

        if price_idx > 0:
            title = cleaned[price_idx - 1]

        location_text: str | None = None
        for line in reversed(cleaned):
            if line == title or cls._looks_like_time_line(line):
                continue
            compact = line.replace(",", "").replace(" ", "")
            if compact.isdigit() or compact.endswith("원"):
                continue
            location_text = cls._normalize_location(line)
            break

        return title, price, location_text

    @staticmethod
    def _extract_pid_from_href(href: str) -> str | None:
        if not href:
            return None
        m = re.search(r"/products/(\d+)", href)
        if m:
            return m.group(1)
        return None

    @staticmethod
    async def _extract_first_text(card, selector: str) -> str:
        try:
            return (await card.locator(selector).first.inner_text() or "").strip()
        except Exception:
            return ""

    async def search(self, keyword: str, location: str = None) -> list[Item]:
        page = await self.get_page()
        encoded_keyword = quote(keyword)
        url = f"https://m.bunjang.co.kr/search/products?q={encoded_keyword}&order=date"

        ok = await self.navigate_with_retry(url, wait_until="domcontentloaded", max_retries=2)
        if not ok:
            return []

        try:
            await page.wait_for_selector("a[data-pid]", timeout=6000)
        except Exception:
            # Keep going: fallback link selectors may still be available.
            pass

        items: list[Item] = []
        seen_pids: set[str] = set()

        # 1) data-pid cards (preferred)
        cards = page.locator("a[data-pid]")
        count = min(await cards.count(), self.MAX_RESULTS)
        for i in range(count):
            card = cards.nth(i)
            try:
                pid = (await card.get_attribute("data-pid") or "").strip()
                if not pid or pid in seen_pids:
                    continue

                raw_card_text = (await card.inner_text() or "").strip()
                parsed_title, parsed_price, parsed_location = self._parse_card_text_fallback(raw_card_text)

                title = await self._extract_first_text(card, "div:nth-of-type(2) > div:nth-of-type(1)")
                if not title:
                    title = parsed_title
                if not self._is_valid_title(title):
                    continue

                price_text = await self._extract_first_text(
                    card,
                    "div:nth-of-type(2) > div:nth-of-type(2) > div:nth-of-type(1)",
                )
                price = self._parse_price(price_text)
                if price == "N/A":
                    price = parsed_price

                location_text = await self._extract_first_text(card, "div:nth-of-type(3)")
                location_value = self._normalize_location(location_text) or parsed_location

                thumbnail = None
                try:
                    thumbnail = await card.locator("img").first.get_attribute("src")
                except Exception:
                    thumbnail = None

                items.append(
                    Item(
                        platform="bunjang",
                        article_id=pid,
                        title=title,
                        price=price,
                        link=f"https://m.bunjang.co.kr/products/{pid}",
                        keyword=keyword,
                        thumbnail=thumbnail,
                        seller=None,
                        location=location_value,
                    )
                )
                seen_pids.add(pid)
            except Exception:
                continue

        if items:
            return items

        # 2) Product link DOM fallback
        links = page.locator("a[href*='/products/']")
        fallback_count = min(await links.count(), self.MAX_RESULTS)
        for i in range(fallback_count):
            el = links.nth(i)
            try:
                href = (await el.get_attribute("href") or "").strip()
                if not href:
                    continue
                if href.startswith("/"):
                    href = f"https://m.bunjang.co.kr{href}"

                pid = self._extract_pid_from_href(href)
                if not pid or pid in seen_pids:
                    continue

                raw_text = (await el.inner_text() or "").strip()
                title, price, location_text = self._parse_card_text_fallback(raw_text)
                if not self._is_valid_title(title):
                    continue

                items.append(
                    Item(
                        platform="bunjang",
                        article_id=pid,
                        title=title,
                        price=price,
                        link=href,
                        keyword=keyword,
                        thumbnail=None,
                        seller=None,
                        location=location_text,
                    )
                )
                seen_pids.add(pid)
            except Exception:
                continue

        return items
