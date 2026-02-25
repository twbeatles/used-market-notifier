# scrapers/danggeun.py
"""Danggeun Market (당근마켓) scraper using Selenium"""

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
        m = re.search(
            r"(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)[^\n|,/]{0,20}",
            text,
        )
        return m.group(0).strip() if m else None

    @staticmethod
    def _normalize_price_text(price: str) -> str:
        if not price:
            return "가격문의"
        digits = "".join(c for c in str(price) if c.isdigit())
        if not digits:
            return "가격문의"
        return f"{int(digits):,}원"

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

        items = []
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
                
                for j_item in json_items:
                    try:
                        product = j_item.get('item', {})
                        # If 'item' is missing, maybe j_item itself is the product?
                        if not product:
                            if 'name' in j_item:
                                product = j_item
                            else:
                                continue
                        
                        # Extract basic info
                        title = product.get('name', 'No Title')
                        desc = product.get('description', '')
                        link = product.get('url', '')
                        image_url = product.get('image', '')
                        
                        # Extract price
                        offers = product.get('offers', {})
                        price = "가격문의"
                        if isinstance(offers, dict):
                            price_val = offers.get('price')
                            currency = offers.get('priceCurrency', 'KRW')
                            if price_val:
                                price = f"{int(float(price_val))}원"
                        
                        # Extract ID from URL
                        article_id = self._extract_article_id(link)

                        if not article_id:
                            continue

                        # Robust price parsing
                        try:
                            if price != "가격문의" and not price.replace('원', '').replace(',', '').isdigit():
                                # Try to clean it up
                                p_clean = ''.join(c for c in price if c.isdigit())
                                if p_clean:
                                    price = f"{int(p_clean):,}원"
                        except Exception:
                            pass

                        # Filter invalid titles
                        if not self._is_valid_title(title):
                            continue

                        item = Item(
                            platform='danggeun',
                            article_id=article_id,
                            title=title,
                            price=price,
                            link=link,
                            keyword=keyword,
                            thumbnail=image_url if image_url else None,
                            location=self._extract_location(desc),
                        )
                        items.append(item)
                    except Exception as e:
                        self.logger.debug(f"Error parsing JSON-LD item: {e}")
                        
            else:
                # Fallback to HTML parsing if JSON-LD fails
                self.logger.info("JSON-LD not found/empty, falling back to HTML parsing")
                elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/kr/buy-sell/"]')
                
                for el in elements:
                    try:
                        link = el.get_attribute('href')
                        if not link or 'search=' in link:  # Skip navigation links
                            continue
                            
                        text = el.text
                        if not text:
                            continue
                            
                        # Simple cleanup parsing
                        lines = [l for l in text.split('\n') if l.strip()]
                        title = lines[0] if lines else "No Title"
                        
                        price = "가격문의"
                        for l in lines:
                            if '원' in l:
                                price = l
                                break
                        
                        # Extract article ID
                        article_id = self._extract_article_id(link)

                        if not article_id:
                            continue
                                
                        # Filter invalid titles
                        if not self._is_valid_title(title):
                            continue
                        
                        # Extract thumbnail from parent element
                        thumbnail = None
                        try:
                            parent = el.find_element(By.XPATH, "./..")
                            img_el = parent.find_element(By.CSS_SELECTOR, "img")
                            thumbnail = img_el.get_attribute("src")
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
                            location=self._extract_location(text),
                        )
                        items.append(item)
                    except Exception:
                        continue
                    
        except Exception as e:
            self.logger.error(f"Error fetching danggeun items: {e}")

        # Filter by location if strictly required and we have info
        if location and items:
            pass

        self.logger.info(f"Found {len(items)} items on Danggeun for '{keyword}'")
        return items
