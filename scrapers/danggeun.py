import time
import re
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from .base import BaseScraper, Item


class DanggeunScraper(BaseScraper):
    """Danggeun Market (당근마켓) scraper with location filter support"""
    
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
        Search Danggeun Market for keyword.
        
        Args:
            keyword: Search term
            location: Optional location filter (e.g., "강남구", "서초동")
        """
        encoded_keyword = quote(keyword)
        url = f"https://www.daangn.com/search/{encoded_keyword}"
        
        self.logger.info(f"Visiting {url}")
        self.driver.get(url)
        
        # Wait for content
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/kr/buy-sell/"]'))
            )
        except:
            time.sleep(3)

        items = []
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/kr/buy-sell/"]')
            
            for el in elements:
                try:
                    link = el.get_attribute('href')
                    if not link:
                        continue
                    
                    # Filter out search/filter links
                    if '?' in link or 'search=' in link:
                        continue

                    # Extract article ID
                    article_id = link.split('-')[-1].replace('/', '')
                    if len(article_id) < 3 or article_id == 'sell':
                        continue
                    
                    text = el.text
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    
                    title = "No Title"
                    price = "가격문의"
                    item_location = None
                    
                    for line in lines:
                        # Price detection
                        if '원' in line and (line[0].isdigit() or len(line) < 20):
                            price = line
                        # Location detection (usually contains 동, 구, 시)
                        elif re.search(r'[시구동면읍리]', line) and len(line) < 30:
                            item_location = line
                        # Title (first substantial line)
                        elif title == "No Title" and len(line) > 2:
                            title = line
                    
                    if title == "No Title" and lines:
                        title = lines[0]
                    
                    # Location filter
                    if location and item_location:
                        if location.lower() not in item_location.lower():
                            continue
                    
                    # Try to get thumbnail
                    thumbnail = None
                    try:
                        img = el.find_element(By.TAG_NAME, "img")
                        thumbnail = img.get_attribute("src")
                        # Filter out placeholder/icon images
                        if thumbnail and ('placeholder' in thumbnail or 'icon' in thumbnail or len(thumbnail) < 50):
                            thumbnail = None
                    except:
                        pass

                    item = Item(
                        platform='danggeun',
                        article_id=article_id,
                        title=title,
                        price=price,
                        link=link,
                        keyword=keyword,
                        thumbnail=thumbnail,
                        location=item_location
                    )
                    items.append(item)
                    
                except Exception as e:
                    self.logger.debug(f"Error parsing item: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error fetching danggeun items: {e}")

        self.logger.info(f"Found {len(items)} items on Danggeun for '{keyword}'")
        return items

    def close(self):
        """Close the browser"""
        try:
            self.driver.quit()
        except:
            pass
