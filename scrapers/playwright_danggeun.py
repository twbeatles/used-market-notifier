# scrapers/playwright_danggeun.py
"""Playwright-based Danggeun scraper."""

from __future__ import annotations

import asyncio
import hashlib
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

    MAX_RESULTS = 120
    CARD_SELECTOR = "a[data-gtm='search_article'][href^='/kr/buy-sell/']"
    DETAIL_SELLER_SELECTORS = (
        "a[href*='/users/']",
        "[data-gtm='seller_profile']",
        "[class*='profile'] strong",
        "[class*='nickname']",
        "[class*='user-name']",
    )
    TIME_MARKERS = ("방금", "초 전", "분 전", "시간 전", "일 전", "주 전", "달 전", "끌올")

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
    def _extract_article_id(link: str) -> str | None:
        if not link:
            return None
        m = re.search(r"-(\d+)(?:/)?(?:\?|$)", link)
        if m:
            return m.group(1)
        m = re.search(r"/(\d+)(?:\?|$)", link)
        if m:
            return m.group(1)
        m = re.search(r"-([a-z0-9]{8,})(?:/)?(?:\?|$)", link, flags=re.IGNORECASE)
        if m:
            return m.group(1).lower()
        digest = hashlib.sha1(link.encode("utf-8")).hexdigest()[:12]
        return f"hash_{digest}"

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

    @staticmethod
    def _to_absolute_link(link: str) -> str:
        if not link:
            return ""
        if link.startswith("/"):
            return f"https://www.daangn.com{link}"
        return link

    @classmethod
    def _looks_like_time_line(cls, text: str) -> bool:
        s = str(text or "").strip()
        if not s:
            return False
        return any(marker in s for marker in cls.TIME_MARKERS)

    @classmethod
    def _parse_card_text(cls, text: str) -> tuple[str, str, str | None]:
        lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
        if not lines:
            return "", "가격문의", None

        title = lines[0]
        price = "가격문의"
        location: str | None = None

        for line in lines[1:]:
            compact = line.replace(" ", "")
            if compact == "·":
                continue

            if price == "가격문의":
                if "원" in line or compact.replace(",", "").isdigit():
                    digits = "".join(ch for ch in line if ch.isdigit())
                    if digits:
                        price = f"{int(digits):,}원"
                        continue
                if "만" in line and any(ch.isdigit() for ch in line):
                    price = line
                    continue

            if cls._looks_like_time_line(line):
                continue

            if location is None and len(line) >= 2:
                location = line

        return title, price, location

    @staticmethod
    def _extract_label_value(text: str, labels: tuple[str, ...]) -> str | None:
        for label in labels:
            pattern = rf"{re.escape(label)}\s*[:\n]\s*([^\n]{{2,40}})"
            match = re.search(pattern, text)
            if match:
                value = match.group(1).strip()
                if value:
                    return value
        return None

    async def _extract_first_matching_text(self, page, selectors: tuple[str, ...]) -> str | None:
        for selector in selectors:
            try:
                value = (await page.locator(selector).first.inner_text(timeout=800) or "").strip()
            except Exception:
                value = ""
            if value:
                return value
        return None

    async def _enrich_item_async(self, item: Item) -> Item:
        if not item.link:
            return item

        page = await self.get_page()
        ok = await self.navigate_with_retry(item.link, wait_until="domcontentloaded", max_retries=2)
        if not ok:
            return item
        await page.wait_for_timeout(800)

        page_text = ""
        try:
            page_text = (await page.locator("body").inner_text() or "").strip()
        except Exception:
            page_text = ""

        seller = item.seller or await self._extract_first_matching_text(page, self.DETAIL_SELLER_SELECTORS)
        if not seller and page_text:
            seller = self._extract_label_value(page_text, ("판매자", "작성자", "당근이웃"))

        location_value = item.location or self._extract_location(page_text)

        return Item(
            platform=item.platform,
            article_id=item.article_id,
            title=item.title,
            price=item.price,
            link=item.link,
            keyword=item.keyword,
            thumbnail=item.thumbnail,
            seller=seller or item.seller,
            location=location_value or item.location,
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

    async def _build_dom_card_map(self, page) -> dict[str, dict[str, str | None]]:
        card_map: dict[str, dict[str, str | None]] = {}
        cards = page.locator(self.CARD_SELECTOR)
        count = min(await cards.count(), self.MAX_RESULTS)

        for i in range(count):
            card = cards.nth(i)
            try:
                link = self._to_absolute_link((await card.get_attribute("href") or "").strip())
                if not link:
                    continue

                article_id = self._extract_article_id(link)
                if not article_id or article_id in card_map:
                    continue

                text = (await card.inner_text() or "").strip()
                title, price, location = self._parse_card_text(text)

                thumbnail = None
                try:
                    thumbnail = await card.locator("img").first.get_attribute("src", timeout=800)
                except Exception:
                    thumbnail = None

                card_map[article_id] = {
                    "title": title or None,
                    "price": price if price != "가격문의" else None,
                    "location": location,
                    "thumbnail": thumbnail,
                    "link": link,
                }
            except Exception:
                continue

        return card_map

    async def search(self, keyword: str, location: str | None = None) -> list[Item]:
        page = await self.get_page()
        encoded_keyword = quote(keyword)
        url = f"https://www.daangn.com/kr/buy-sell/?search={encoded_keyword}&sort=recent"

        ok = await self.navigate_with_retry(url, wait_until="domcontentloaded", max_retries=2)
        if not ok:
            return []
        await page.wait_for_timeout(1200)

        dom_card_map = await self._build_dom_card_map(page)
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
                    for entry in node.get("itemListElement", [])[: self.MAX_RESULTS]:
                        product = entry.get("item", {}) if isinstance(entry, dict) else {}
                        if not product and isinstance(entry, dict):
                            product = entry
                        if not isinstance(product, dict):
                            continue
                        if product.get("@type") not in (None, "Product"):
                            continue

                        link = self._to_absolute_link(str(product.get("url", "")).strip())
                        article_id = self._extract_article_id(link)
                        if not article_id or article_id in seen_ids:
                            continue

                        card_data = dom_card_map.get(article_id, {})
                        title = str(product.get("name", "")).strip() or str(card_data.get("title") or "")
                        if not self._is_valid_title(title):
                            continue

                        price = self._normalize_price(product)
                        if price == "가격문의" and card_data.get("price"):
                            price = str(card_data["price"])

                        location_text = self._extract_location(str(product.get("description", "")))
                        if not location_text:
                            location_text = str(card_data.get("location") or "") or None

                        thumbnail = product.get("image") or card_data.get("thumbnail")

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
                                location=location_text,
                            )
                        )
                        if len(items) >= self.MAX_RESULTS:
                            return items
                if items:
                    return items
        except Exception:
            pass

        # 2) DOM card parsing fallback
        cards = page.locator(self.CARD_SELECTOR)
        count = min(await cards.count(), self.MAX_RESULTS)
        for i in range(count):
            card = cards.nth(i)
            try:
                link = self._to_absolute_link((await card.get_attribute("href") or "").strip())
                if not link:
                    continue

                article_id = self._extract_article_id(link)
                if not article_id or article_id in seen_ids:
                    continue

                text = (await card.inner_text() or "").strip()
                if not text:
                    continue
                title, price, location_text = self._parse_card_text(text)
                if not self._is_valid_title(title):
                    continue

                thumbnail = None
                try:
                    thumbnail = await card.locator("img").first.get_attribute("src", timeout=800)
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
                        location=location_text,
                    )
                )
                if len(items) >= self.MAX_RESULTS:
                    break
            except Exception:
                continue

        return items
