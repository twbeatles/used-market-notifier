import re
from urllib.parse import quote
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .selenium_base import SeleniumScraper
from .base import Item


class BunjangScraper(SeleniumScraper):
    """Bunjang (번개장터) scraper with thumbnail and seller extraction"""
    
    def __init__(self, headless: bool = True, disable_images: bool = True):
        super().__init__(headless, disable_images)

    def search(self, keyword: str, location: str = None) -> list[Item]:
        """
        Search Bunjang for keyword.
        
        Args:
            keyword: Search term
            location: Not used for Bunjang (nationwide platform)
        """
        encoded_keyword = quote(keyword)
        url = f"https://m.bunjang.co.kr/search/products?q={encoded_keyword}"
        
        self.logger.info(f"Visiting {url}")
        self.driver.get(url)
        
        # Bunjang is SPA, wait for content
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/products/']"))
            )
        except Exception as e:
            self.logger.warning(f"Timeout waiting for Bunjang results: {e}")
            return []

        items = []
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/products/']")
            
            for el in elements:
                try:
                    link = el.get_attribute('href')
                    if not link or '/products/' not in link or '/products/new' in link:
                        continue
                    
                    # Extract article ID
                    article_id = link.split('/products/')[1].split('?')[0]
                    if not article_id or not article_id.isdigit():
                        continue
                    
                    text_content = [l.strip() for l in el.text.split('\n') if l.strip()]
                    
                    title = "No Title"
                    price = "가격문의"
                    seller = None
                    thumbnail = None
                    
                    # Get thumbnail from image
                    try:
                        img = el.find_element(By.TAG_NAME, "img")
                        alt = img.get_attribute("alt")
                        thumbnail = img.get_attribute("src")
                        
                        if alt and alt != "상품 이미지" and alt != "product":
                            title = alt
                        
                        # Filter placeholder thumbnails
                        if thumbnail and ('placeholder' in thumbnail or 'default' in thumbnail):
                            thumbnail = None
                    except:
                        pass
                    
                    # Parse text content
                    for line in text_content:
                        # Price detection
                        if ('원' in line or line.replace(',', '').isdigit()) and len(line) < 15:
                            price = line
                        # Title (if not from alt)
                        elif title == "No Title" and len(line) > 2:
                            title = line
                    
                    # Ensure full link
                    if not link.startswith('http'):
                        link = f"https://m.bunjang.co.kr{link}"

                    item = Item(
                        platform='bunjang',
                        article_id=article_id,
                        title=title,
                        price=price,
                        link=link,
                        keyword=keyword,
                        thumbnail=thumbnail,
                        seller=seller
                    )
                    items.append(item)
                    
                except Exception as e:
                    self.logger.debug(f"Error parsing item: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error scraping Bunjang: {e}")

        self.logger.info(f"Found {len(items)} items on Bunjang for '{keyword}'")
        return items
