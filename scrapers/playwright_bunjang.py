# scrapers/playwright_bunjang.py
"""Playwright-based Bunjang scraper."""

from __future__ import annotations

import re
from urllib.parse import quote

import aiohttp

from models import Item

from .marketplace_parsers import (
    merge_item_metadata,
    normalize_location_value,
    parse_bunjang_card_text,
    parse_bunjang_detail_payload,
    parse_bunjang_search_items,
    parse_html_snapshot,
    pick_seller_candidate,
    extract_bunjang_product_id,
)
from .playwright_base import PlaywrightScraper


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
        "ad",
    ]

    def __init__(self, headless: bool = True, disable_images: bool = True):
        super().__init__(
            headless=headless,
            disable_images=disable_images,
            use_stealth=True,
            debug_mode=False,
        )

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
        parsed = parse_bunjang_card_text(text)
        return parsed.title, parsed.price, parsed.location

    @staticmethod
    def _extract_pid_from_href(href: str) -> str | None:
        return extract_bunjang_product_id(href)

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
            title=payload.get("title"),
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
        return parse_bunjang_search_items(snapshot, keyword, max_results=self.MAX_RESULTS)

    async def _dump_anomaly_if_needed(self, page, keyword: str, metrics: dict[str, object], items: list[Item]) -> None:
        candidate_count = self._metric_int(metrics, "dom_card_count") + self._metric_int(metrics, "dom_product_link_count")
        if items or candidate_count <= 0:
            return
        self._last_failure_kind = "parser_zero"
        await self.dump_debug_artifacts(keyword, metrics, prefix="zero_results")

    async def enrich_item_async(self, item: Item) -> Item:
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

    async def search(self, keyword: str, location: str | None = None) -> list[Item]:
        page = await self.get_page()
        encoded_keyword = quote(keyword)
        url = f"https://m.bunjang.co.kr/search/products?q={encoded_keyword}&order=date"

        ok = await self.navigate_with_retry(url, wait_until="domcontentloaded", max_retries=2)
        if not ok:
            return []

        try:
            await page.wait_for_selector("a[href*='/products/'], a[data-pid]", timeout=6000)
        except Exception:
            pass
        await page.wait_for_timeout(800)

        snapshot = parse_html_snapshot(await page.content())
        items, metrics = self._parse_snapshot_items(snapshot, keyword)
        self._log_search_metrics(keyword, metrics)
        await self._dump_anomaly_if_needed(page, keyword, metrics, items)
        return items
