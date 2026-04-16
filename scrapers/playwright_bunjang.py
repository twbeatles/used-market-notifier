# scrapers/playwright_bunjang.py
"""Playwright-based Bunjang scraper."""

from __future__ import annotations

import asyncio
from collections import Counter
import re
from urllib.parse import quote

import aiohttp

from models import Item

from .marketplace_parsers import (
    merge_item_metadata,
    normalize_location_value,
    parse_bunjang_detail_payload,
    parse_html_snapshot,
    pick_seller_candidate,
)
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
    """Bunjang scraper with data-pid priority, API enrichment, and anomaly diagnostics."""

    BADGE_LINES = {"배송비포함", "검수가능"}
    UNKNOWN_LOCATION_TEXTS = {"지역정보 없음", "지역 정보 없음"}
    MAX_RESULTS = 120
    DETAIL_SELLER_SELECTORS = (
        "[class*='ProductSeller'] [class*='Name']",
        "[class*='Seller'] [class*='Name']",
        "a[href*='/shop/'][href$='/products']",
        "a[href*='/shop/']",
        "[class*='Seller']",
    )

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
    def _parse_price(text: str) -> str:
        if not text:
            return "N/A"
        digits = re.sub(r"[^\d]", "", text)
        if not digits:
            return "N/A"
        return f"{int(digits):,}\uc6d0"

    @classmethod
    def _normalize_location(cls, text: str) -> str | None:
        return normalize_location_value(text)

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
    def _extract_label_value(text: str, labels: tuple[str, ...]) -> str | None:
        for label in labels:
            pattern = rf"{re.escape(label)}\s*[:\n]\s*([^\n]{{2,40}})"
            match = re.search(pattern, text)
            if match:
                value = match.group(1).strip()
                if value:
                    return value
        return None

    @classmethod
    def _extract_location_from_text(cls, text: str) -> str | None:
        labeled = cls._extract_label_value(
            text,
            ("직거래지역", "직거래 지역", "거래지역", "거래 지역", "지역", "지역 정보", "지역정보"),
        )
        if labeled:
            return cls._normalize_location(labeled)
        match = re.search(
            r"(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)[^\n|,/]{0,20}",
            text,
        )
        return cls._normalize_location(match.group(0)) if match else None

    async def _extract_first_matching_text(self, page, selectors: tuple[str, ...]) -> str | None:
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
            except Exception:
                elements = []
            candidates: list[dict[str, str | None]] = []
            for element in elements[:5]:
                try:
                    text = (await element.inner_text() or "").strip()
                except Exception:
                    text = ""
                try:
                    href = await element.get_attribute("href")
                except Exception:
                    href = None
                candidates.append({"text": text, "href": href, "aria_label": None})
            value = pick_seller_candidate(candidates, platform="bunjang")
            if value:
                return value
        return None

    @staticmethod
    def _detail_api_url(article_id: str) -> str:
        return f"https://api.bunjang.co.kr/api/pms/v3/products-detail/{article_id}?viewerUid=-1"

    async def _fetch_detail_payload(self, article_id: str) -> dict | None:
        if not article_id:
            return None
        timeout = aiohttp.ClientTimeout(total=5)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self._detail_api_url(article_id)) as response:
                    if response.status >= 400:
                        return None
                    return await response.json(content_type=None)
        except Exception:
            return None

    @staticmethod
    def _apply_detail_payload(item: Item, payload: dict[str, object]) -> Item:
        return merge_item_metadata(
            item,
            seller=payload.get("seller"),
            location=payload.get("location"),
            price=payload.get("price"),
            sale_status=payload.get("sale_status"),
            price_numeric=payload.get("price_numeric"),
        )

    def _log_search_metrics(self, keyword: str, metrics: dict[str, object]) -> None:
        self.logger.info(
            f"Bunjang search metrics keyword='{keyword}' "
            f"dom_card_count={metrics.get('dom_card_count', 0)} "
            f"dom_product_link_count={metrics.get('dom_product_link_count', 0)} "
            f"items_after_data_pid={metrics.get('items_after_data_pid', 0)} "
            f"items_after_dom_fallback={metrics.get('items_after_dom_fallback', 0)} "
            f"drop_reason_count={metrics.get('drop_reason_count', {})}"
        )

    def _parse_snapshot_items(self, snapshot, keyword: str) -> tuple[list[Item], dict[str, object]]:
        metrics: dict[str, object] = {
            "dom_card_count": 0,
            "dom_product_link_count": 0,
            "items_after_data_pid": 0,
            "items_after_dom_fallback": 0,
            "drop_reason_count": {},
        }
        drop_reasons: Counter[str] = Counter()
        items: list[Item] = []
        seen_pids: set[str] = set()

        cards = [anchor for anchor in snapshot.anchors if anchor.attrs.get("data-pid")]
        metrics["dom_card_count"] = len(cards)
        for anchor in cards[: self.MAX_RESULTS]:
            try:
                pid = str(anchor.attrs.get("data-pid") or "").strip()
                if not pid:
                    drop_reasons["missing_id"] += 1
                    continue
                if pid in seen_pids:
                    drop_reasons["duplicate_id"] += 1
                    continue

                raw_card_text = anchor.text
                title, price, location_value = self._parse_card_text_fallback(raw_card_text)
                if not self._is_valid_title(title):
                    drop_reasons["invalid_title"] += 1
                    continue

                items.append(
                    Item(
                        platform="bunjang",
                        article_id=pid,
                        title=title,
                        price=price,
                        link=f"https://m.bunjang.co.kr/products/{pid}",
                        keyword=keyword,
                        thumbnail=anchor.image,
                        seller=None,
                        location=location_value,
                    )
                )
                seen_pids.add(pid)
            except Exception:
                drop_reasons["parse_error"] += 1

        metrics["items_after_data_pid"] = len(items)
        if items:
            metrics["drop_reason_count"] = dict(drop_reasons)
            return items, metrics

        product_links = [
            anchor
            for anchor in snapshot.anchors
            if "/products/" in str(anchor.attrs.get("href") or "")
        ]
        metrics["dom_product_link_count"] = len(product_links)
        for anchor in product_links[: self.MAX_RESULTS]:
            try:
                href = str(anchor.attrs.get("href") or "").strip()
                if not href:
                    drop_reasons["missing_href"] += 1
                    continue
                if href.startswith("/"):
                    href = f"https://m.bunjang.co.kr{href}"

                pid = self._extract_pid_from_href(href)
                if not pid:
                    drop_reasons["missing_id"] += 1
                    continue
                if pid in seen_pids:
                    drop_reasons["duplicate_id"] += 1
                    continue

                title, price, location_value = self._parse_card_text_fallback(anchor.text)
                if not self._is_valid_title(title):
                    drop_reasons["invalid_title"] += 1
                    continue

                items.append(
                    Item(
                        platform="bunjang",
                        article_id=pid,
                        title=title,
                        price=price,
                        link=href,
                        keyword=keyword,
                        thumbnail=anchor.image,
                        seller=None,
                        location=location_value,
                    )
                )
                seen_pids.add(pid)
            except Exception:
                drop_reasons["parse_error"] += 1

        metrics["items_after_dom_fallback"] = len(items)
        metrics["drop_reason_count"] = dict(drop_reasons)
        return items, metrics

    async def _dump_anomaly_if_needed(self, page, keyword: str, metrics: dict[str, object], items: list[Item]) -> None:
        candidate_count = int(metrics.get("dom_card_count", 0)) + int(metrics.get("dom_product_link_count", 0))
        if items or candidate_count <= 0:
            return
        await self.dump_debug_artifacts(keyword, metrics, prefix="zero_results")

    async def _enrich_item_async(self, item: Item) -> Item:
        if not item.link:
            return item

        payload = parse_bunjang_detail_payload(await self._fetch_detail_payload(item.article_id))
        enriched = self._apply_detail_payload(item, payload)
        if enriched.seller and enriched.location:
            return enriched

        page = await self.get_page()
        ok = await self.navigate_with_retry(enriched.link, wait_until="domcontentloaded", max_retries=2)
        if not ok:
            return enriched
        await page.wait_for_timeout(800)

        page_text = ""
        try:
            page_text = (await page.locator("body").inner_text() or "").strip()
        except Exception:
            page_text = ""

        seller = enriched.seller or await self._extract_first_matching_text(page, self.DETAIL_SELLER_SELECTORS)
        if not seller and page_text:
            seller = self._extract_label_value(page_text, ("상점명", "판매자", "작성자"))

        location_value = enriched.location or self._extract_location_from_text(page_text)

        return merge_item_metadata(
            enriched,
            seller=seller,
            location=location_value,
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
        encoded_keyword = quote(keyword)
        url = f"https://m.bunjang.co.kr/search/products?q={encoded_keyword}&order=date"

        ok = await self.navigate_with_retry(url, wait_until="domcontentloaded", max_retries=2)
        if not ok:
            return []

        try:
            await page.wait_for_selector("a[data-pid]", timeout=6000)
        except Exception:
            pass
        await page.wait_for_timeout(800)

        snapshot = parse_html_snapshot(await page.content())
        items, metrics = self._parse_snapshot_items(snapshot, keyword)
        self._log_search_metrics(keyword, metrics)
        await self._dump_anomaly_if_needed(page, keyword, metrics, items)
        return items
