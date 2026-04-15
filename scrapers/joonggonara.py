# scrapers/joonggonara.py
"""Joonggonara (중고나라) scraper - Using Naver Search cafe results with Selenium."""

from __future__ import annotations

import hashlib
import re
import time
from urllib.parse import parse_qs, quote, urlsplit, urlunsplit

from .base import Item
from .marketplace_parsers import (
    extract_numeric_article_id,
    is_valid_joonggonara_title,
    parse_joonggonara_detail_text,
    parse_joonggonara_search_items,
)
from .selenium_base import By, EC, SeleniumScraper, WebDriverWait


class JoonggonaraScraper(SeleniumScraper):
    """
    Joonggonara scraper using Naver Search cafe tab.
    More reliable than direct cafe access which often requires login/captcha.
    """

    CAFE_ID = "10050146"

    INVALID_TITLE_PATTERNS = [
        "판매완료",
        "예약중",
        "거래완료",
        "No Title",
        "광고",
        "배송비포함",
    ]

    def __init__(self, headless: bool = True, disable_images: bool = True, driver=None):
        super().__init__(headless, disable_images, driver)

    def _is_valid_title(self, title: str) -> bool:
        return is_valid_joonggonara_title(title)

    @staticmethod
    def _normalize_link(link: str) -> str:
        """Normalize URL to improve deterministic ID generation."""
        if not link:
            return ""
        try:
            parts = urlsplit(link)
            return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))
        except Exception:
            return link

    @staticmethod
    def extract_article_id(link: str) -> str:
        """
        Extract a stable article id from a Naver cafe link.

        Priority:
        1) query param `articleid`
        2) numeric path segment (e.g. /12345?... or /12345)
        3) deterministic hash fallback (NOT Python's hash(), which is randomized per process)
        """
        if not link:
            return "hash_000000000000"

        normalized = JoonggonaraScraper._normalize_link(link)
        strict_id = extract_numeric_article_id(normalized)
        if strict_id:
            return strict_id

        try:
            parts = urlsplit(normalized)
            qs = parse_qs(parts.query or "")
            article_ids = qs.get("articleid") or qs.get("articleId") or qs.get("articleID")
            if article_ids and article_ids[0]:
                match = re.search(r"(\d+)", str(article_ids[0]))
                if match:
                    return match.group(1)
        except Exception:
            pass

        digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]
        return f"hash_{digest}"

    @staticmethod
    def _build_article_url(article_id: str, fallback_link: str) -> str:
        if str(article_id or "").isdigit():
            return f"https://cafe.naver.com/joonggonara/{article_id}"
        return fallback_link

    def _extract_detail_body_text(self) -> str:
        body_text = ""
        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass

        try:
            WebDriverWait(self.driver, self.wait_time).until(
                EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe#cafe_main"))
            )
            time.sleep(0.5)
            body_text = (self.driver.find_element(By.TAG_NAME, "body").text or "").strip()
        except Exception:
            body_text = ""
        finally:
            try:
                self.driver.switch_to.default_content()
            except Exception:
                pass

        if body_text:
            return body_text

        try:
            return (self.driver.find_element(By.TAG_NAME, "body").text or "").strip()
        except Exception:
            return ""

    def enrich_item(self, item: Item) -> Item:
        if not item.link:
            return item

        target_url = self._build_article_url(item.article_id, item.link)
        self.driver.get(target_url)
        time.sleep(1.0)

        body_text = self._extract_detail_body_text()
        parsed = parse_joonggonara_detail_text(body_text)

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

    def search(self, keyword: str, location: str | None = None) -> list[Item]:
        """Search Joonggonara via Naver Search cafe tab."""
        encoded = quote(keyword)
        url = (
            "https://search.naver.com/search.naver"
            f"?where=article&query={encoded}%20site%3Acafe.naver.com%2Fjoonggonara"
        )

        self.logger.info(f"Visiting {url}")
        self.driver.get(url)

        try:
            time.sleep(2)
            try:
                WebDriverWait(self.driver, self.wait_time).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='cafe.naver.com/joonggonara']"))
                )
            except Exception:
                self.logger.info(f"No Joonggonara article links found for '{keyword}'")
                return []

            items = parse_joonggonara_search_items(self.driver.page_source, keyword)
            self.logger.info(f"Found {len(items)} items on Joonggonara for '{keyword}'")
            return items
        except Exception as e:
            self.logger.error(f"Error scraping Joonggonara via Naver Search: {e}")
            return []
