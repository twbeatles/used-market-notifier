# scrapers/joonggonara.py
"""
Joonggonara (중고나라) scraper - Enhanced with advanced stealth for Naver bot detection bypass.

This scraper uses comprehensive stealth techniques to bypass Naver's aggressive bot detection:
- 15 browser fingerprint masking techniques
- Human-like behavior simulation
- Random delays and scroll patterns
- Enhanced HTTP headers
"""

import re
from urllib.parse import quote
from .playwright_base import PlaywrightScraper
from .stealth import random_delay, scroll_like_human
from models import Item


class JoonggonaraScraper(PlaywrightScraper):
    """
    Joonggonara scraper using Naver Search cafe tab.
    Uses advanced stealth mode to bypass Naver's aggressive bot detection.
    More reliable than direct café access which requires login/captcha.
    """
    
    # Joonggonara cafe ID
    CAFE_ID = "10050146"
    
    # Invalid title patterns to filter out
    INVALID_TITLE_PATTERNS = [
        "판매완료", "예약중", "거래완료", "No Title", "광고", "배송비포함"
    ]
    
    # Naver-specific headers to appear more legitimate
    NAVER_HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.naver.com/",
        "Sec-Ch-Ua": '"Chromium";v="126", "Google Chrome";v="126", "Not-A.Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }
    
    def __init__(
        self, 
        headless: bool = True, 
        disable_images: bool = True,
        context=None,
        debug_mode: bool = False
    ):
        # Always enable stealth mode and random fingerprint for Naver
        super().__init__(
            headless=headless, 
            disable_images=disable_images, 
            context=context, 
            use_stealth=True,
            debug_mode=debug_mode,
            random_fingerprint=True
        )
    
    async def search(self, keyword: str, location: str = None) -> list[Item]:
        """
        Search Joonggonara via Naver Search cafe tab.
        This works better than direct cafe access which often requires captcha.
        
        Uses advanced stealth techniques to bypass Naver bot detection.
        """
        encoded = quote(keyword)
        
        # Naver Search cafe-specific query for joonggonara
        # site:cafe.naver.com/joonggonara forces results from this cafe
        url = f"https://search.naver.com/search.naver?where=article&query={encoded}%20site%3Acafe.naver.com%2Fjoonggonara"
        
        self.logger.info(f"🔍 Searching Joonggonara for '{keyword}'")
        
        page = await self.get_page()
        
        # Set Naver-specific headers
        await page.set_extra_http_headers(self.NAVER_HEADERS)
        
        # Add random delay before navigation (human-like)
        await random_delay(500, 1500)
        
        # Navigate with retry
        success = await self.navigate_with_retry(url, wait_until="domcontentloaded")
        if not success:
            self.logger.error("❌ Failed to navigate to Naver Search")
            return []
        
        items = []
        
        try:
            # Verify stealth is working
            if self.debug_mode:
                await self.verify_stealth()
            
            # Add human-like behavior: scroll a bit
            await random_delay(300, 800)
            await scroll_like_human(page, scroll_count=2)
            
            # Wait for search results with multiple possible selectors
            selectors = [
                "a.title_link",
                "a.api_txt_lines.total_tit",
                ".bx",
                "ul.lst_total"
            ]
            
            # Wait for any of the selectors with debugging
            found = await self.wait_and_check(
                ", ".join(selectors), 
                timeout=10000,
                on_timeout="both"  # Screenshot and HTML on timeout
            )
            
            if not found:
                self.logger.info(f"No results found on Naver Search for '{keyword}' in Joonggonara")
                
                # Check for CAPTCHA or block page
                page_content = await page.content()
                if "자동입력" in page_content or "captcha" in page_content.lower():
                    self.logger.warning("⚠️ CAPTCHA detected - Bot detection triggered")
                    if self.debugger:
                        self.debugger.log_warning("CAPTCHA detected")
                        await self.debugger.take_screenshot(page, "captcha_detected")
                
                return []
            
            # Try multiple selector patterns for Naver Search results
            article_elements = []
            selector_used = None
            
            for selector in [
                "a.title_link",  # Main title links
                "a.api_txt_lines.total_tit",  # Alternative title format
                "ul.lst_total > li a.link_tit",  # List format
                "div.total_area a.api_txt_lines",  # Total search area
            ]:
                elements = await page.query_selector_all(selector)
                if elements:
                    self.logger.debug(f"Found {len(elements)} elements with selector: {selector}")
                    article_elements = elements
                    selector_used = selector
                    break
            
            if not article_elements:
                # Fallback: find any cafe links
                all_links = await page.query_selector_all("a[href*='cafe.naver.com/joonggonara']")
                article_elements = []
                for l in all_links:
                    text = await l.inner_text()
                    if text.strip():
                        article_elements.append(l)
                self.logger.debug(f"Fallback: found {len(article_elements)} cafe links")
            
            self.logger.info(f"📦 Processing {len(article_elements)} potential items")
            
            for el in article_elements:
                try:
                    link = await el.get_attribute("href") or ""
                    title = await el.inner_text()
                    title = title.strip()
                    
                    # Must be joonggonara link
                    if "joonggonara" not in link and "cafe.naver.com" not in link:
                        continue
                    
                    # Extract article ID from URL
                    match = re.search(r'articleid=(\d+)', link, re.IGNORECASE)
                    if not match:
                        match = re.search(r'/(\d+)\?', link)
                    if not match:
                        match = re.search(r'/(\d+)$', link)
                    if not match:
                        # Generate ID from URL hash
                        article_id = str(hash(link) % 1000000000)
                    else:
                        article_id = match.group(1)
                    
                    # Clean title (remove newlines and extra spaces)
                    if '\n' in title:
                        title = title.split('\n')[0].strip()
                    title = ' '.join(title.split())
                    
                    if not self._is_valid_title(title):
                        continue
                    
                    item = Item(
                        platform='joonggonara',
                        article_id=article_id,
                        title=title,
                        price="가격문의",  # Search results don't show price
                        link=link,
                        keyword=keyword,
                        thumbnail=None
                    )
                    items.append(item)
                    
                except Exception as e:
                    self.logger.debug(f"Error parsing article: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"❌ Error scraping Joonggonara via Naver Search: {e}")
            
            # Capture error diagnostics
            if self.debug_mode and self.debugger:
                from .debug import capture_on_error
                await capture_on_error(page, self.debugger, e, "search")
        
        self.logger.info(f"✅ Found {len(items)} items on Joonggonara for '{keyword}'")
        return items
