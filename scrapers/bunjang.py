# scrapers/bunjang.py
"""Bunjang (번개장터) scraper using Selenium"""

import json
import re
import time
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import urlopen

from .base import Item
from .marketplace_parsers import (
    merge_item_metadata,
    normalize_location_value,
    parse_bunjang_card_text,
    parse_bunjang_detail_payload,
    parse_bunjang_search_items,
    parse_html_snapshot,
    pick_seller_candidate,
)
from .selenium_base import By, EC, SeleniumScraper, WebDriverWait


class BunjangScraper(SeleniumScraper):
    """Bunjang (번개장터) scraper with thumbnail and seller extraction"""

    BADGE_LINES = {"배송비포함", "검수가능"}
    UNKNOWN_LOCATION_TEXTS = {"지역정보 없음", "지역 정보 없음"}

    DETAIL_SELLER_SELECTORS = (
        "[class*='ProductSeller'] [class*='Name']",
        "[class*='Seller'] [class*='Name']",
        "a[href*='/shop/'][href$='/products']",
        "a[href*='/shop/']",
        "[class*='Seller']",
    )

    # Invalid title patterns to filter out
    INVALID_TITLE_PATTERNS = [
        "배송비포함", "검수가능", "제목 없음", "No Title",
        "판매완료", "예약중", "광고", "AD"
    ]

    def __init__(self, headless: bool = True, disable_images: bool = True,
                 driver=None):
        super().__init__(headless, disable_images, driver)

    def _is_valid_title(self, title: str) -> bool:
        """Check if title is valid (not sold out or placeholder)"""
        if not title or len(title.strip()) < 2:
            return False
        # Filter out invalid title patterns - use partial matching
        title_lower = title.strip().lower()
        for pattern in self.INVALID_TITLE_PATTERNS:
            if pattern.lower() in title_lower:
                return False
        return True

    @staticmethod
    def _normalize_price_text(text: str) -> str:
        digits = re.sub(r"[^\d]", "", str(text or ""))
        if not digits:
            return "N/A"
        return f"{int(digits):,}원"

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
        return parsed.title or "제목 없음", parsed.price, parsed.location

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

    def _extract_first_matching_text(self, selectors: tuple[str, ...]) -> str | None:
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            except Exception:
                elements = []
            candidates: list[dict[str, str | None]] = []
            for element in elements[:5]:
                try:
                    text = (element.text or "").strip()
                except Exception:
                    text = ""
                try:
                    href = element.get_attribute("href")
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

    def _fetch_detail_payload(self, article_id: str) -> dict | None:
        if not article_id:
            return None
        try:
            with urlopen(self._detail_api_url(article_id), timeout=5) as response:
                if getattr(response, "status", 200) >= 400:
                    return None
                return json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, json.JSONDecodeError):
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

    def enrich_item(self, item: Item) -> Item:
        if not item.link:
            return item

        payload = parse_bunjang_detail_payload(self._fetch_detail_payload(item.article_id))
        enriched = self._apply_detail_payload(item, payload)
        if enriched.seller and enriched.location:
            return enriched

        self.driver.get(enriched.link)
        time.sleep(1.0)

        try:
            page_text = (self.driver.find_element(By.TAG_NAME, "body").text or "").strip()
        except Exception:
            page_text = ""

        seller = enriched.seller or self._extract_first_matching_text(self.DETAIL_SELLER_SELECTORS)
        if not seller and page_text:
            seller = self._extract_label_value(page_text, ("상점명", "판매자", "작성자"))

        location_value = enriched.location or self._extract_location_from_text(page_text)

        return merge_item_metadata(
            enriched,
            seller=seller,
            location=location_value,
        )

    def search(self, keyword: str, location: str | None = None) -> list[Item]:
        """
        Search Bunjang for keyword.

        Args:
            keyword: Search term
            location: Not used for Bunjang (nationwide platform)
        """
        encoded_keyword = quote(keyword)
        # URL with recency sort
        url = f"https://m.bunjang.co.kr/search/products?q={encoded_keyword}&order=date"

        self.logger.info(f"Visiting {url}")
        self.driver.get(url)

        items = []
        try:
            # Wait for current product links or legacy data-pid cards.
            try:
                WebDriverWait(self.driver, self.wait_time).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/products/'], a[data-pid]"))
                )
            except Exception:
                self.logger.info("No items found on Bunjang (Timeout waiting for product links)")
                return []

            snapshot = parse_html_snapshot(self.driver.page_source)
            items, metrics = parse_bunjang_search_items(snapshot, keyword)
            self.logger.info(
                f"Bunjang Selenium parse metrics keyword='{keyword}' "
                f"dom_product_link_count={metrics.get('dom_product_link_count', 0)} "
                f"dom_card_count={metrics.get('dom_card_count', 0)} "
                f"items={len(items)} drop_reason_count={metrics.get('drop_reason_count', {})}"
            )

        except Exception as e:
            self.logger.error(f"Error parsing Bunjang items: {e}")

        self.logger.info(f"Found {len(items)} items on Bunjang for '{keyword}'")
        return items
