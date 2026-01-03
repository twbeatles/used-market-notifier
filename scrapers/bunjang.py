# scrapers/bunjang.py
"""Bunjang (번개장터) scraper - Playwright version with async support"""

from urllib.parse import quote
from .playwright_base import PlaywrightScraper
from models import Item


class BunjangScraper(PlaywrightScraper):
    """Bunjang (번개장터) scraper with thumbnail and seller extraction"""
    
    # Additional invalid title patterns specific to Bunjang
    INVALID_TITLE_PATTERNS = [
        "배송비포함", "검수가능", "제목 없음", "No Title", 
        "판매완료", "예약중", "광고"
    ]
    
    def __init__(
        self, 
        headless: bool = True, 
        disable_images: bool = True,
        context=None,
        debug_mode: bool = False
    ):
        super().__init__(
            headless=headless, 
            disable_images=disable_images, 
            context=context,
            debug_mode=debug_mode
        )
    
    async def search(self, keyword: str, location: str = None) -> list[Item]:
        """
        Search Bunjang for keyword.
        
        Args:
            keyword: Search term
            location: Not used for Bunjang (nationwide platform)
        """
        encoded_keyword = quote(keyword)
        url = f"https://m.bunjang.co.kr/search/products?q={encoded_keyword}"
        
        self.logger.info(f"Visiting {url}")
        
        page = await self.get_page()
        await page.goto(url, wait_until="domcontentloaded")
        
        items = []
        try:
            # Wait for items to load (using data-pid selector which targets legitimate product items)
            try:
                await page.wait_for_selector("a[data-pid]", timeout=10000)
            except Exception:
                # If no items found, check if "No results" message exists or just return empty
                self.logger.info("No items found on Bunjang (Timeout waiting for a[data-pid])")
                return []
            
            # Get all product links
            product_links = await page.query_selector_all("a[data-pid]")
            
            for link_el in product_links:
                try:
                    # 1. Extract ID and Link
                    pid = await link_el.get_attribute("data-pid")
                    if not pid:
                        continue
                    link = f"https://m.bunjang.co.kr/products/{pid}"
                    
                    # 2. Extract Title (2nd div -> 1st div)
                    # Structure: Image(1) - Info(2) - Location(3)
                    # Info: Title(1) - Price/Time(2)
                    try:
                        title_el = await link_el.query_selector("div:nth-of-type(2) > div:nth-of-type(1)")
                        title = await title_el.inner_text() if title_el else "제목 없음"
                        title = title.strip()
                    except Exception:
                        title = "제목 없음"
                    
                    # 3. Extract Price (2nd div -> 2nd div -> 1st div)
                    try:
                        price_el = await link_el.query_selector("div:nth-of-type(2) > div:nth-of-type(2) > div:nth-of-type(1)")
                        if price_el:
                            price_text = await price_el.inner_text()
                            price_text = price_text.replace(',', '').replace('원', '').strip()
                            price = int(price_text) if price_text.isdigit() else 0
                        else:
                            price = 0
                    except Exception:
                        price = 0
                    
                    # 4. Extract Location (3rd div)
                    location_text = ""
                    try:
                        loc_el = await link_el.query_selector("div:nth-of-type(3)")
                        if loc_el:
                            location_text = await loc_el.inner_text()
                            location_text = location_text.strip()
                    except Exception:
                        pass
                    
                    # 5. Extract Image (1st div -> img)
                    img_url = ""
                    try:
                        img_el = await link_el.query_selector("div:nth-of-type(1) img")
                        if img_el:
                            img_url = await img_el.get_attribute("src")
                    except Exception:
                        pass
                    
                    # Use the validation method
                    if not self._is_valid_title(title):
                        continue
                    
                    item = Item(
                        platform="bunjang",
                        article_id=pid,
                        title=title,
                        price=str(price),
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
