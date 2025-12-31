# scrapers/joonggonara.py
"""Joonggonara (중고나라) scraper - Naver Cafe based"""

import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .selenium_base import SeleniumScraper
from .base import Item


class JoonggonaraScraper(SeleniumScraper):
    """
    Joonggonara scraper using the public search interface.
    Note: Some features may be limited without Naver login.
    """
    
    def __init__(self, headless: bool = True, disable_images: bool = True):
        super().__init__(headless, disable_images)
    
    def search(self, keyword: str, location: str = None) -> list[Item]:
        """
        Search Joonggonara via Naver Cafe search.
        Target URL: https://m.cafe.naver.com/joonggonara/search?search.query={keyword}
        """
        # Encode keyword manually or use urllib. We need urllib quote for robust encoding
        from urllib.parse import quote
        encoded = quote(keyword)
        url = f"https://m.cafe.naver.com/joonggonara/search?search.query={encoded}"
        
        self.logger.info(f"Visiting {url}")
        self.driver.get(url)
        
        # Wait for list items
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.list_item"))
            )
        except Exception as e:
            self.logger.warning(f"Timeout waiting for Joonggonara results: {e}")
            return []
            
        items = []
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, "li.list_item")
            
            for el in elements:
                try:
                    # Extracts are tricky on mobile Naver Cafe. 
                    # Structure usually: a.item_link -> div.info -> strong.tit
                    
                    link_el = el.find_element(By.CSS_SELECTOR, "a")
                    link = link_el.get_attribute("href")
                    
                    if not link or "ArticleRead.nhn" not in link:
                        continue
                        
                    # Extract article ID
                    # ../ArticleRead.nhn?clubid=10050146&articleid=101234567...
                    match = re.search(r'articleid=(\d+)', link)
                    if not match:
                        continue
                    article_id = match.group(1)
                    
                    title_el = el.find_element(By.CSS_SELECTOR, "strong.tit")
                    title = title_el.text.strip()
                    
                    # Price might be missing or in different spot
                    price = "가격문의"
                    try:
                        price_el = el.find_element(By.CSS_SELECTOR, "span.price")
                        price = price_el.text.strip()
                    except:
                        pass
                        
                    # Get thumbnail
                    thumbnail = None
                    try:
                        img = el.find_element(By.TAG_NAME, "img")
                        thumbnail = img.get_attribute("src")
                    except:
                        pass

                    if not link.startswith('http'):
                        link = f"https://m.cafe.naver.com{link}"
                    
                    item = Item(
                        platform='joonggonara',
                        article_id=article_id,
                        title=title,
                        price=price,
                        link=link,
                        keyword=keyword,
                        thumbnail=thumbnail
                    )
                    items.append(item)
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error scraping Joonggonara: {e}")
            
        self.logger.info(f"Found {len(items)} items on Joonggonara")
        return items
