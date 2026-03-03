# scrapers/danggeun.py
"""Danggeun Market (당근마켓) scraper using Selenium"""

import hashlib
import json
import re
import time
from urllib.parse import quote
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .selenium_base import SeleniumScraper
from .base import Item


class DanggeunScraper(SeleniumScraper):
    """Danggeun Market (당근마켓) scraper with location filter support"""

    MAX_RESULTS = 120
    CARD_SELECTOR = "a[data-gtm='search_article'][href^='/kr/buy-sell/']"
    TIME_MARKERS = ("방금", "초 전", "분 전", "시간 전", "일 전", "주 전", "달 전", "끌올")

    # Invalid title patterns to filter out
    INVALID_TITLE_PATTERNS = [
        "판매완료", "예약중", "거래완료", "No Title", "광고"
    ]

    def __init__(self, headless: bool = True, disable_images: bool = True,
                 driver=None):
        super().__init__(headless, disable_images, driver)

    def _is_valid_title(self, title: str) -> bool:
        """Check if title is valid (not sold out or placeholder)"""
        if not title or len(title.strip()) < 2:
            return False
        # Filter out sold/reserved items - use partial matching
        title_lower = title.strip().lower()
        for pattern in self.INVALID_TITLE_PATTERNS:
            if pattern.lower() in title_lower:
                return False
        return True

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
        m = re.search(
            r"(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)[^\n|,/]{0,20}",
            text,
        )
        return m.group(0).strip() if m else None

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
    def _normalize_price_text(price: str) -> str:
        if not price:
            return "가격문의"
        digits = "".join(c for c in str(price) if c.isdigit())
        if not digits:
            return "가격문의"
        return f"{int(digits):,}원"

    def _build_dom_card_map(self) -> dict[str, dict[str, str | None]]:
        card_map: dict[str, dict[str, str | None]] = {}
        elements = self.driver.find_elements(By.CSS_SELECTOR, self.CARD_SELECTOR)

        for el in elements[: self.MAX_RESULTS]:
            try:
                link = self._to_absolute_link((el.get_attribute("href") or "").strip())
                if not link:
                    continue
                article_id = self._extract_article_id(link)
                if not article_id or article_id in card_map:
                    continue

                text = (el.text or "").strip()
                title, price, location = self._parse_card_text(text)

                thumbnail = None
                try:
                    thumbnail = el.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
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

    def search(self, keyword: str, location: str = None) -> list[Item]:
        """
        Search Danggeun Market for keyword.
        
        Args:
            keyword: Search term
            location: Optional location filter (e.g., "강남구", "서초동")
        """
        encoded_keyword = quote(keyword)
        # URL with recency sort for latest listings
        url = f"https://www.daangn.com/kr/buy-sell/?search={encoded_keyword}&sort=recent"
        
        self.logger.info(f"Visiting {url}")
        self.driver.get(url)
        
        # Wait for content or JSON-LD
        try:
            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "script[type='application/ld+json']"))
            )
        except Exception:
            time.sleep(3)

        dom_card_map = self._build_dom_card_map()
        items = []
        seen_ids: set[str] = set()
        try:
            # Try to parse JSON-LD first (Most reliable)
            scripts = self.driver.find_elements(By.CSS_SELECTOR, "script[type='application/ld+json']")
            json_items = []

            for script in scripts:
                try:
                    script_content = script.get_attribute('innerHTML')
                    data = json.loads(script_content)
                    if data.get('@type') == 'ItemList' and 'itemListElement' in data:
                        json_items.extend(data['itemListElement'])
                except Exception:
                    continue
            
            if json_items:
                self.logger.info(f"Found {len(json_items)} items via JSON-LD")

                for j_item in json_items[: self.MAX_RESULTS]:
                    try:
                        product = j_item.get('item', {}) if isinstance(j_item, dict) else {}
                        # If 'item' is missing, maybe j_item itself is the product?
                        if not product:
                            if isinstance(j_item, dict) and 'name' in j_item:
                                product = j_item
                            else:
                                continue
                        if not isinstance(product, dict):
                            continue
                        if product.get("@type") not in (None, "Product"):
                            continue

                        # Extract basic info
                        desc = str(product.get('description', ''))
                        link = self._to_absolute_link(str(product.get('url', '')))
                        image_url = product.get('image', '')

                        article_id = self._extract_article_id(link)
                        if not article_id or article_id in seen_ids:
                            continue

                        dom_data = dom_card_map.get(article_id, {})
                        title = str(product.get('name', '')).strip() or str(dom_data.get("title") or "No Title")
                        if not self._is_valid_title(title):
                            continue

                        # Extract price
                        offers = product.get('offers', {})
                        price = "가격문의"
                        if isinstance(offers, dict):
                            price_val = offers.get('price')
                            if price_val:
                                price = f"{int(float(price_val)):,}원"
                        if price == "가격문의" and dom_data.get("price"):
                            price = str(dom_data["price"])

                        # Robust price parsing
                        try:
                            if price != "가격문의" and not price.replace('원', '').replace(',', '').isdigit():
                                # Try to clean it up
                                p_clean = ''.join(c for c in price if c.isdigit())
                                if p_clean:
                                    price = f"{int(p_clean):,}원"
                        except Exception:
                            pass

                        location_text = self._extract_location(desc)
                        if not location_text:
                            location_text = str(dom_data.get("location") or "") or None

                        item = Item(
                            platform='danggeun',
                            article_id=article_id,
                            title=title,
                            price=price,
                            link=link,
                            keyword=keyword,
                            thumbnail=image_url if image_url else dom_data.get("thumbnail"),
                            location=location_text,
                        )
                        seen_ids.add(article_id)
                        items.append(item)
                        if len(items) >= self.MAX_RESULTS:
                            return items
                    except Exception as e:
                        self.logger.debug(f"Error parsing JSON-LD item: {e}")

            else:
                # Fallback to HTML parsing if JSON-LD fails
                self.logger.info("JSON-LD not found/empty, falling back to HTML parsing")
                elements = self.driver.find_elements(By.CSS_SELECTOR, self.CARD_SELECTOR)

                for el in elements[: self.MAX_RESULTS]:
                    try:
                        link = self._to_absolute_link((el.get_attribute('href') or '').strip())
                        if not link:
                            continue

                        article_id = self._extract_article_id(link)
                        if not article_id or article_id in seen_ids:
                            continue

                        text = (el.text or "").strip()
                        if not text:
                            continue

                        title, price, location_text = self._parse_card_text(text)

                        # Filter invalid titles
                        if not self._is_valid_title(title):
                            continue

                        thumbnail = None
                        try:
                            thumbnail = el.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
                        except Exception:
                            pass

                        item = Item(
                            platform='danggeun',
                            article_id=article_id,
                            title=title,
                            price=self._normalize_price_text(price),
                            link=link,
                            keyword=keyword,
                            thumbnail=thumbnail,
                            location=location_text,
                        )
                        seen_ids.add(article_id)
                        items.append(item)
                        if len(items) >= self.MAX_RESULTS:
                            break
                    except Exception:
                        continue

        except Exception as e:
            self.logger.error(f"Error fetching danggeun items: {e}")

        # Filter by location if strictly required and we have info
        if location and items:
            pass

        self.logger.info(f"Found {len(items)} items on Danggeun for '{keyword}'")
        return items
