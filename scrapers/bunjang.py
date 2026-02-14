# scrapers/bunjang.py
"""Bunjang (번개장터) scraper using Selenium"""

import time
from urllib.parse import quote
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .selenium_base import SeleniumScraper
from .base import Item


class BunjangScraper(SeleniumScraper):
    """Bunjang (번개장터) scraper with thumbnail and seller extraction"""
    
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

                    # 2. Extract Title (2nd div -> 1st div)
                    try:
                        title_el = link_el.find_element(By.CSS_SELECTOR, "div:nth-of-type(2) > div:nth-of-type(1)")
                        title = title_el.text.strip() if title_el else "제목 없음"
                    except Exception:
                        title = "제목 없음"

                    # 3. Extract Price (2nd div -> 2nd div -> 1st div)
                    try:
                        price_el = link_el.find_element(By.CSS_SELECTOR, "div:nth-of-type(2) > div:nth-of-type(2) > div:nth-of-type(1)")
                        if price_el:
                            price_text = price_el.text.replace(',', '').replace('원', '').strip()
                            price = int(price_text) if price_text.isdigit() else 0
                        else:
                            price = 0
                    except Exception:
                        price = 0

                    # 4. Extract Location (3rd div)
                    location_text = ""
                    try:
                        loc_el = link_el.find_element(By.CSS_SELECTOR, "div:nth-of-type(3)")
                        if loc_el:
                            location_text = loc_el.text.strip()
                    except Exception:
                        pass
                    
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
                        price="가격문의" if price == 0 else f"{price:,}원",
                        link=link,
                        keyword=keyword,
                        thumbnail=img_url,
                        seller=None,
                        location=location_text
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
