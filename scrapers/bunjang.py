# scrapers/bunjang.py
"""Bunjang (번개장터) scraper using Selenium"""

import re
import time
from urllib.parse import quote
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .selenium_base import SeleniumScraper
from .base import Item


class BunjangScraper(SeleniumScraper):
    """Bunjang (번개장터) scraper with thumbnail and seller extraction"""

    BADGE_LINES = {"배송비포함", "검수가능"}
    UNKNOWN_LOCATION_TEXTS = {"지역정보 없음", "지역 정보 없음"}

    # Invalid title patterns to filter out
    INVALID_TITLE_PATTERNS = [
        "배송비포함", "검수가능", "제목 없음", "No Title",
        "판매완료", "예약중", "광고"
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
            return "제목 없음", "N/A", None

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

    def search(self, keyword: str, location: str = None) -> list[Item]:
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
            # Wait for items to load (using data-pid selector which targets legitimate product items)
            try:
                WebDriverWait(self.driver, self.wait_time).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-pid]"))
                )
            except Exception:
                # If no items found, check if "No results" message exists or just return empty
                self.logger.info("No items found on Bunjang (Timeout waiting for a[data-pid])")
                return []

            product_links = self.driver.find_elements(By.CSS_SELECTOR, "a[data-pid]")

            for link_el in product_links:
                try:
                    # 1. Extract ID and Link
                    pid = link_el.get_attribute("data-pid")
                    if not pid:
                        continue
                    link = f"https://m.bunjang.co.kr/products/{pid}"

                    raw_card_text = (link_el.text or "").strip()
                    parsed_title, parsed_price, parsed_location = self._parse_card_text_fallback(raw_card_text)

                    # 2. Extract Title (2nd div -> 1st div)
                    try:
                        title_el = link_el.find_element(By.CSS_SELECTOR, "div:nth-of-type(2) > div:nth-of-type(1)")
                        title = title_el.text.strip() if title_el else parsed_title
                    except Exception:
                        title = parsed_title

                    # 3. Extract Price (2nd div -> 2nd div -> 1st div)
                    price = "N/A"
                    try:
                        price_el = link_el.find_element(
                            By.CSS_SELECTOR,
                            "div:nth-of-type(2) > div:nth-of-type(2) > div:nth-of-type(1)"
                        )
                        if price_el:
                            price = self._normalize_price_text(price_el.text)
                    except Exception:
                        price = "N/A"
                    if price == "N/A":
                        price = parsed_price

                    # 4. Extract Location (3rd div)
                    location_value: str | None = None
                    try:
                        loc_el = link_el.find_element(By.CSS_SELECTOR, "div:nth-of-type(3)")
                        if loc_el:
                            location_value = self._normalize_location(loc_el.text.strip())
                    except Exception:
                        pass
                    if location_value is None:
                        location_value = parsed_location

                    # 5. Extract Image (1st div -> img)
                    img_url = ""
                    try:
                        img_el = link_el.find_element(By.CSS_SELECTOR, "div:nth-of-type(1) img")
                        if img_el:
                            img_url = img_el.get_attribute("src")
                    except Exception:
                        pass

                    # Use the validation method
                    if not self._is_valid_title(title):
                        continue

                    item = Item(
                        platform="bunjang",
                        article_id=pid,
                        title=title,
                        price=price,
                        link=link,
                        keyword=keyword,
                        thumbnail=img_url,
                        seller=None,
                        location=location_value,
                    )
                    items.append(item)

                except Exception as e:
                    # Skip individual item errors
                    self.logger.debug(f"Error parsing item: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error parsing Bunjang items: {e}")

        self.logger.info(f"Found {len(items)} items on Bunjang for '{keyword}'")
        return items
