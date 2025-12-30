# scrapers/joonggonara.py
"""Joonggonara (중고나라) scraper - Naver Cafe based"""

import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from .base import BaseScraper, Item


class JoonggonaraScraper(BaseScraper):
    """
    Joonggonara scraper using the public search interface.
    Note: Some features may be limited without Naver login.
    """
    
    def __init__(self, headless: bool = True):
        super().__init__()
        self.options = Options()
        if headless:
            self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--window-size=1920,1080')
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=self.options
        )
    
    def search(self, keyword: str, location: str = None) -> list[Item]:
        """
        Search Joonggonara via Naver Cafe search.
        Using mobile cafe search for lighter loading.
        """
        # URL encode the keyword
        from urllib.parse import quote
        encoded_keyword = quote(keyword)
        
        # Joonggonara cafe ID: 10050146
        # Using cafe article search
        url = f"https://m.cafe.naver.com/ca-fe/web/cafes/10050146/articles?query={encoded_keyword}&searchBy=0"
        
        self.logger.info(f"Visiting {url}")
        self.driver.get(url)
        
        # Wait for content to load
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.item"))
            )
        except Exception as e:
            self.logger.warning(f"Timeout waiting for Joonggonara results: {e}")
            # Try alternative selector
            time.sleep(3)
        
        items = []
        try:
            # Find all article links
            elements = self.driver.find_elements(By.CSS_SELECTOR, "a.item, a.article_item, li.article-item a")
            
            for el in elements:
                try:
                    link = el.get_attribute('href')
                    if not link:
                        continue
                    
                    # Extract article ID from URL
                    article_id = None
                    if '/articles/' in link:
                        match = re.search(r'/articles/(\d+)', link)
                        if match:
                            article_id = match.group(1)
                    elif 'articleid=' in link.lower():
                        match = re.search(r'articleid=(\d+)', link, re.IGNORECASE)
                        if match:
                            article_id = match.group(1)
                    
                    if not article_id:
                        continue
                    
                    # Get text content
                    text = el.text.strip()
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    
                    title = "No Title"
                    price = "가격문의"
                    seller = None
                    
                    if lines:
                        title = lines[0]
                    
                    # Look for price pattern in text
                    for line in lines:
                        # Korean won patterns
                        price_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*원', line)
                        if price_match:
                            price = price_match.group(0)
                            break
                        # Just numbers that look like prices
                        if re.match(r'^\d{1,3}(,\d{3})*$', line) and len(line) >= 4:
                            price = line + "원"
                            break
                    
                    # Try to get thumbnail
                    thumbnail = None
                    try:
                        img = el.find_element(By.TAG_NAME, "img")
                        thumbnail = img.get_attribute("src")
                        if thumbnail and 'blur' in thumbnail:
                            thumbnail = None  # Skip blurred images
                    except:
                        pass
                    
                    # Construct full link if needed
                    if not link.startswith('http'):
                        link = f"https://m.cafe.naver.com{link}"
                    
                    item = Item(
                        platform='joonggonara',
                        article_id=article_id,
                        title=title[:100],  # Limit title length
                        price=price,
                        link=link,
                        keyword=keyword,
                        thumbnail=thumbnail,
                        seller=seller,
                        location=location
                    )
                    items.append(item)
                    
                except Exception as e:
                    self.logger.debug(f"Error parsing item: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error scraping Joonggonara: {e}")
        
        self.logger.info(f"Found {len(items)} items on Joonggonara for '{keyword}'")
        return items
    
    def close(self):
        """Close the browser"""
        try:
            self.driver.quit()
        except:
            pass
