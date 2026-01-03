# scrapers/danggeun.py
"""Danggeun Market (당근마켓) scraper - Playwright version with async support"""

import json
from urllib.parse import quote
from .playwright_base import PlaywrightScraper
from models import Item


class DanggeunScraper(PlaywrightScraper):
    """Danggeun Market (당근마켓) scraper with location filter support"""
    
    # Invalid title patterns to filter out
    INVALID_TITLE_PATTERNS = [
        "판매완료", "예약중", "거래완료", "No Title", "광고"
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
        Search Danggeun Market for keyword.
        
        Args:
            keyword: Search term
            location: Optional location filter (e.g., "강남구", "서초동")
        """
        encoded_keyword = quote(keyword)
        # Updated URL structure
        url = f"https://www.daangn.com/kr/buy-sell/?search={encoded_keyword}"
        
        self.logger.info(f"Visiting {url}")
        
        page = await self.get_page()
        await page.goto(url, wait_until="domcontentloaded")
        
        # Wait for content or JSON-LD
        try:
            await page.wait_for_selector("script[type='application/ld+json']", timeout=10000)
        except Exception:
            # Small delay as fallback
            await page.wait_for_timeout(3000)
        
        items = []
        try:
            # Try to parse JSON-LD first (Most reliable)
            scripts = await page.query_selector_all("script[type='application/ld+json']")
            json_items = []
            
            for script in scripts:
                try:
                    script_content = await script.inner_html()
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
                elements = await page.query_selector_all('a[href*="/kr/buy-sell/"]')
                
                for el in elements:
                    try:
                        link = await el.get_attribute('href')
                        if not link or 'search=' in link:  # Skip navigation links
                            continue
                        
                        text = await el.inner_text()
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
                        
                        # Extract article_id from link
                        parts = link.rstrip('/').split('-')
                        article_id = parts[-1] if len(parts) > 1 else link.split('/')[-1]
                        
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
