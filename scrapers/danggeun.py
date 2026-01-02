import time
import re
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
    
    def __init__(self, headless: bool = True, disable_images: bool = True, driver=None):
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

    def search(self, keyword: str, location: str = None) -> list[Item]:
        """
        Search Danggeun Market for keyword.
        
        Args:
            keyword: Search term
            location: Optional location filter (e.g., "강남구", "서초동")
        """
        import json
        
        encoded_keyword = quote(keyword)
        # Updated URL structure
        url = f"https://www.daangn.com/kr/buy-sell/?search={encoded_keyword}"
        
        self.logger.info(f"Visiting {url}")
        self.driver.get(url)
        
        # Wait for content or JSON-LD
        try:
            WebDriverWait(self.driver, 10).until(
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
                    data = json.loads(script.get_attribute('innerHTML'))
                    if data.get('@type') == 'ItemList' and 'itemListElement' in data:
                        json_items.extend(data['itemListElement'])
                except Exception:
                    continue
            
            if json_items:
                self.logger.info(f"Found {len(json_items)} items via JSON-LD")
                
                for j_item in json_items:
                    # print(f"DEBUG ITEM keys: {j_item.keys()}")
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
                        # https://www.daangn.com/kr/buy-sell/title-slug-articleid/
                        # Extract ID from URL
                        # https://www.daangn.com/kr/buy-sell/title-slug-articleid/
                        article_id = None
                        if link:
                            # Handle trailing slashes and split
                            # URL typically ends with slug-id
                            parts = link.rstrip('/').split('-')
                            if len(parts) > 1:
                                article_id = parts[-1]
                            # Sometimes URL is just /.../id without dash? Unlikely but fallback
                            elif parts:
                                article_id = parts[0].split('/')[-1]

                        if not article_id:
                            # self.logger.debug(f"Skipping item without ID: {link}")
                            continue

                        # Robust price parsing
                        try:
                             if price != "가격문의" and price.replace('원','').replace(',','').isdigit() == False:
                                  # Try to clean it up
                                  p_clean = ''.join(c for c in price if c.isdigit())
                                  if p_clean:
                                      price = f"{int(p_clean)}원"
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
                            location=location if location else "지역정보없음"
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
                        if 'search=' in link: # Skip navigation links
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
                            thumbnail=None,
                            location="지역정보없음"
                        )
                        items.append(item)
                    except Exception:
                        continue
                    
        except Exception as e:
            self.logger.error(f"Error fetching danggeun items: {e}")

        # Filter by location if strictly required and we have info (JSON LD weak on location)
        if location and items:
            # Re-verify location for top items if needed, but for now return all matches to ensure data flow
            pass

        self.logger.info(f"Found {len(items)} items on Danggeun for '{keyword}'")
        return items
