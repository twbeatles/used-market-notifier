# scrapers/joonggonara.py
"""Joonggonara (중고나라) scraper - Using Naver Search cafe results with Selenium"""

import re
import time
import hashlib
from urllib.parse import quote
from urllib.parse import urlsplit, urlunsplit, parse_qs
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .selenium_base import SeleniumScraper
from .base import Item


class JoonggonaraScraper(SeleniumScraper):
    """
    Joonggonara scraper using Naver Search cafe tab.
    More reliable than direct café access which requires login/captcha.
    """
    
    # Joonggonara cafe ID
    CAFE_ID = "10050146"
    
    # Invalid title patterns to filter out
    INVALID_TITLE_PATTERNS = [
        "판매완료", "예약중", "거래완료", "No Title", "광고", "배송비포함"
    ]
    
    def __init__(self, headless: bool = True, disable_images: bool = True, 
                 driver=None):
        super().__init__(headless, disable_images, driver)
    
    def _is_valid_title(self, title: str) -> bool:
        """Check if title is valid (not sold out or placeholder)"""
        if not title or len(title.strip()) < 2:
            return False
        if title.strip() in self.INVALID_TITLE_PATTERNS:
            return False
        return True

    @staticmethod
    def _normalize_link(link: str) -> str:
        """
        Normalize URL to improve deterministic ID generation.
        Currently removes fragment only (same article, different #...).
        """
        if not link:
            return ""
        try:
            parts = urlsplit(link)
            # Drop fragment, keep query/path as-is.
            return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))
        except Exception:
            return link

    @staticmethod
    def extract_article_id(link: str) -> str:
        """
        Extract a stable article id from a Naver cafe link.

        Priority:
        1) query param `articleid`
        2) numeric path segment (e.g. /12345?... or /12345)
        3) deterministic hash fallback (NOT Python's hash(), which is randomized per process)
        """
        if not link:
            return "hash_000000000000"

        normalized = JoonggonaraScraper._normalize_link(link)

        try:
            parts = urlsplit(normalized)
            qs = parse_qs(parts.query or "")
            article_ids = qs.get("articleid") or qs.get("articleId") or qs.get("articleID")
            if article_ids and article_ids[0]:
                m = re.search(r"(\d+)", str(article_ids[0]))
                if m:
                    return m.group(1)
        except Exception:
            pass

        try:
            m = re.search(r"/(\d+)(?:\?|$)", normalized)
            if m:
                return m.group(1)
        except Exception:
            pass

        digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]
        return f"hash_{digest}"
    
    def search(self, keyword: str, location: str = None) -> list[Item]:
        """
        Search Joonggonara via Naver Search cafe tab.
        This works better than direct cafe access which often requires captcha.
        """
        encoded = quote(keyword)
        
        # Naver Search cafe-specific query for joonggonara
        url = f"https://search.naver.com/search.naver?where=article&query={encoded}%20site%3Acafe.naver.com%2Fjoonggonara"
        
        self.logger.info(f"Visiting {url}")
        self.driver.get(url)
        
        items = []
        
        try:
            # Wait for search results
            time.sleep(2)
            
            try:
                WebDriverWait(self.driver, self.wait_time).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 
                        "a.title_link, a.api_txt_lines.total_tit, .bx, ul.lst_total"))
                )
            except Exception:
                self.logger.info(f"No results found on Naver Search for '{keyword}' in Joonggonara")
                return []
            
            # Try multiple selector patterns for Naver Search results
            selectors = [
                "a.title_link",  # Main title links
                "a.api_txt_lines.total_tit",  # Alternative title format
                "ul.lst_total > li a.link_tit",  # List format
                "div.total_area a.api_txt_lines",  # Total search area
            ]
            
            article_elements = []
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    self.logger.debug(f"Found {len(elements)} elements with selector: {selector}")
                    article_elements = elements
                    break
            
            if not article_elements:
                # Fallback: find any cafe links
                all_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='cafe.naver.com/joonggonara']")
                article_elements = []
                for link in all_links:
                    text = link.text
                    if text and text.strip():
                        article_elements.append(link)
                self.logger.debug(f"Fallback: found {len(article_elements)} cafe links")
            
            for el in article_elements:
                try:
                    link = el.get_attribute("href") or ""
                    title = el.text.strip()
                    
                    # Must be joonggonara link
                    if "joonggonara" not in link and "cafe.naver.com" not in link:
                        continue
                    
                    # Extract deterministic article ID from URL
                    article_id = self.extract_article_id(link)
                    
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
            self.logger.error(f"Error scraping Joonggonara via Naver Search: {e}")
        
        self.logger.info(f"Found {len(items)} items on Joonggonara for '{keyword}'")
        return items
