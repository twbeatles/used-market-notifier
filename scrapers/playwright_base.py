# scrapers/playwright_base.py
"""Playwright-based scraper base class with advanced stealth and debugging support"""

import asyncio
import logging
import functools
from abc import ABC, abstractmethod
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

# Import Item from models - single source of truth
from models import Item

# Import enhanced stealth and debug modules
from .stealth import (
    apply_full_stealth, 
    get_random_user_agent, 
    get_random_viewport,
    check_bot_detection,
    random_delay,
    scroll_like_human
)
from .debug import ScraperDebugger, capture_on_error


def async_retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Async retry decorator with exponential backoff and logging"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            last_exception = None
            current_delay = delay
            for attempt in range(max_attempts):
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    last_exception = e
                    self.logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed: {type(e).__name__}: {e}"
                    )
                    if attempt < max_attempts - 1:
                        self.logger.info(f"Retrying in {current_delay:.1f}s...")
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            
            # All attempts failed
            self.logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            raise last_exception
        return wrapper
    return decorator


class PlaywrightScraper(ABC):
    """
    Base class for Playwright-based scrapers with:
    - Advanced stealth mode (15 techniques)
    - Comprehensive debugging
    - Automatic retry with exponential backoff
    - Human-like behavior simulation
    - Performance optimizations
    """
    
    # ===== PERFORMANCE TUNING =====
    DEFAULT_TIMEOUT = 15000       # 15 seconds (reduced from 30)
    NAVIGATION_TIMEOUT = 20000    # 20 seconds for page navigation
    SELECTOR_TIMEOUT = 10000      # 10 seconds for element wait
    
    # Wait strategies (faster to slower)
    WAIT_STRATEGIES = ["domcontentloaded", "load", "networkidle"]
    
    # Invalid title patterns to filter out (shared across scrapers)
    INVALID_TITLE_PATTERNS = [
        "판매완료", "예약중", "거래완료", "No Title", "광고", 
        "배송비포함", "검수가능", "제목 없음"
    ]
    
    def __init__(
        self, 
        headless: bool = True, 
        disable_images: bool = True,
        context: BrowserContext = None,
        use_stealth: bool = False,
        debug_mode: bool = False,
        debug_level: str = "info",
        random_fingerprint: bool = True
    ):
        """
        Initialize scraper.
        
        Args:
            headless: Run browser in headless mode
            disable_images: Block image loading for performance
            context: Shared browser context (optional)
            use_stealth: Enable stealth mode to bypass bot detection
            debug_mode: Enable comprehensive debugging
            debug_level: Debug level (debug, info, warning, error)
            random_fingerprint: Randomize user agent and viewport
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.headless = headless
        self.disable_images = disable_images
        self._context = context
        self._owned_context = False
        self._page: Optional[Page] = None
        self.use_stealth = use_stealth
        self.debug_mode = debug_mode
        self.debug_level = debug_level
        self.random_fingerprint = random_fingerprint
        
        # Debugger instance (created per search if debug_mode is True)
        self.debugger: Optional[ScraperDebugger] = None
        
        # Track bot detection status
        self._bot_detection_passed = None
        
    async def initialize(self, playwright: Playwright = None, browser: Browser = None):
        """
        Initialize browser context.
        
        Args:
            playwright: Shared Playwright instance (optional)
            browser: Shared browser instance (optional)
        """
        if self._context:
            # Using shared context - apply stealth if needed
            if self.use_stealth:
                await apply_full_stealth(self._context)
            return
        
        if browser:
            # Create context from shared browser
            self._context = await self._create_context(browser)
            self._owned_context = True
        elif playwright:
            # Create browser and context
            browser = await self._launch_browser(playwright)
            self._context = await self._create_context(browser)
            self._owned_context = True
        else:
            raise ValueError("Either playwright, browser, or context must be provided")
    
    async def _launch_browser(self, playwright: Playwright) -> Browser:
        """Launch browser with optimized settings"""
        launch_options = {
            "headless": self.headless,
            "args": [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-infobars",
                "--disable-blink-features=AutomationControlled",  # Key for stealth
            ]
        }
        
        browser = await playwright.chromium.launch(**launch_options)
        self.logger.info(f"Chromium browser launched (headless={self.headless})")
        return browser
    
    async def _create_context(self, browser: Browser) -> BrowserContext:
        """Create browser context with optimized settings"""
        # Use random fingerprint if enabled
        if self.random_fingerprint:
            user_agent = get_random_user_agent()
            viewport = get_random_viewport()
        else:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            viewport = {"width": 1920, "height": 1080}
        
        context_options = {
            "viewport": viewport,
            "user_agent": user_agent,
            "locale": "ko-KR",
            "timezone_id": "Asia/Seoul",
            "permissions": ["geolocation"],
            "geolocation": {"latitude": 37.5665, "longitude": 126.9780},  # Seoul
            "color_scheme": "light",
            "has_touch": False,
            "is_mobile": False,
        }
        
        context = await browser.new_context(**context_options)
        
        # Block images for performance
        if self.disable_images:
            await context.route("**/*.{png,jpg,jpeg,gif,webp,svg}", lambda route: route.abort())
        
        # Apply full stealth mode if enabled
        if self.use_stealth:
            await apply_full_stealth(context)
            self.logger.info("🛡️ Full stealth mode applied (15 techniques)")
        
        context.set_default_timeout(self.DEFAULT_TIMEOUT)
        self.logger.debug(f"Browser context created (UA: {user_agent[:50]}...)")
        return context
    
    async def get_page(self) -> Page:
        """Get or create a page with debugging attached"""
        if not self._context:
            raise RuntimeError("Browser context not initialized. Call initialize() first.")
        
        if not self._page or self._page.is_closed():
            self._page = await self._context.new_page()
            
            # Attach debugger if debug mode is enabled
            if self.debug_mode and self.debugger:
                await self.debugger.attach_to_page(self._page)
        
        return self._page
    
    async def navigate_with_retry(
        self, 
        url: str, 
        wait_until: str = "domcontentloaded",
        max_retries: int = 3
    ) -> bool:
        """
        Navigate to URL with automatic retry on failure.
        
        Args:
            url: URL to navigate to
            wait_until: Wait condition (domcontentloaded, load, networkidle)
            max_retries: Maximum retry attempts
            
        Returns:
            True if navigation succeeded
        """
        page = await self.get_page()
        
        for attempt in range(max_retries):
            try:
                response = await page.goto(url, wait_until=wait_until)
                
                if response and response.status >= 400:
                    self.logger.warning(f"HTTP {response.status} for {url}")
                    if self.debugger:
                        self.debugger.log_warning(f"HTTP {response.status}")
                        await self.debugger.take_screenshot(page, f"http_error_{response.status}")
                
                if self.debug_mode and self.debugger:
                    await self.debugger.take_screenshot(page, "navigation_complete")
                
                return True
                
            except Exception as e:
                self.logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return False
    
    async def verify_stealth(self) -> bool:
        """
        Verify that stealth mode is working by checking bot detection.
        
        Returns:
            True if stealth is working (bot detection passed)
        """
        if not self._page:
            return False
        
        result = await check_bot_detection(self._page)
        self._bot_detection_passed = not result.get('webdriver', True)
        
        if not self._bot_detection_passed:
            self.logger.warning("⚠️ Bot detection check FAILED - may be blocked")
            if self.debugger:
                self.debugger.log_warning("Bot detection check failed")
        else:
            self.logger.info("✅ Bot detection check PASSED")
        
        return self._bot_detection_passed
    
    def _create_debugger(self, keyword: str) -> ScraperDebugger:
        """Create a debugger for the current search session"""
        return ScraperDebugger(
            platform=self.__class__.__name__.replace("Scraper", "").lower(),
            keyword=keyword,
            debug_level=self.debug_level,
            save_screenshots=True,
            save_html=True,
            save_network_logs=True,
            save_console_logs=True
        )
    
    @abstractmethod
    async def search(self, keyword: str, location: str = None) -> list[Item]:
        """
        Search for the keyword on the platform and return a list of Items.
        
        Args:
            keyword: Search term
            location: Optional location filter (platform-specific)
        
        Returns:
            List of Item objects
        """
        pass
    
    @async_retry(max_attempts=3, delay=1.0)
    async def safe_search(self, keyword: str, location: str = None) -> list[Item]:
        """
        Safe wrapper around search with debugging and auto-retry.
        """
        # Create debugger for this session if debug mode is enabled
        if self.debug_mode:
            self.debugger = self._create_debugger(keyword)
        
        try:
            items = await self.search(keyword, location)
            
            if self.debugger:
                self.debugger.log_items_found(len(items))
                await self.debugger.finalize("completed")
            
            return items
            
        except Exception as e:
            self.logger.error(f"Search failed for '{keyword}': {e}")
            
            # Capture error diagnostics
            if self.debug_mode and self.debugger and self._page:
                await capture_on_error(self._page, self.debugger, e, f"search_{keyword}")
                await self.debugger.finalize("failed")
            
            return []
    
    async def wait_and_check(
        self, 
        selector: str, 
        timeout: int = 10000,
        on_timeout: str = "screenshot"
    ) -> bool:
        """
        Wait for selector and capture debug info on timeout.
        
        Args:
            selector: CSS selector to wait for
            timeout: Timeout in milliseconds
            on_timeout: Action on timeout ("screenshot", "html", "both", "none")
            
        Returns:
            True if element found, False on timeout
        """
        page = await self.get_page()
        
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            self.logger.warning(f"Timeout waiting for '{selector}': {e}")
            
            if self.debugger and on_timeout != "none":
                if on_timeout in ["screenshot", "both"]:
                    await self.debugger.take_screenshot(page, f"timeout_{selector[:20]}")
                if on_timeout in ["html", "both"]:
                    await self.debugger.save_page_html(page, f"timeout_{selector[:20]}")
            
            return False
    
    def _is_valid_title(self, title: str) -> bool:
        """Check if title is valid (not sold out or placeholder)"""
        if not title or len(title.strip()) < 2:
            return False
        title_lower = title.strip().lower()
        for pattern in self.INVALID_TITLE_PATTERNS:
            if pattern.lower() in title_lower:
                return False
        return True
    
    def filter_by_price(self, items: list[Item], min_price: int = None, max_price: int = None) -> list[Item]:
        """Filter items by price range"""
        result = []
        for item in items:
            price = item.parse_price()
            if price == 0:
                result.append(item)
                continue
            if min_price and price < min_price:
                continue
            if max_price and price > max_price:
                continue
            result.append(item)
        return result
    
    def filter_by_keywords(self, items: list[Item], exclude_keywords: list[str] = None) -> list[Item]:
        """Filter out items containing excluded keywords"""
        if not exclude_keywords:
            return items
        result = []
        for item in items:
            title_lower = item.title.lower()
            if not any(ex.lower() in title_lower for ex in exclude_keywords):
                result.append(item)
        return result
    
    async def take_screenshot(self, filename: str = None) -> bytes:
        """Take a screenshot for debugging"""
        if not self._page:
            return None
        
        if filename:
            await self._page.screenshot(path=filename, full_page=True)
            self.logger.info(f"📸 Screenshot saved: {filename}")
        
        return await self._page.screenshot(full_page=True)
    
    async def close(self):
        """Clean up resources"""
        try:
            if self._page and not self._page.is_closed():
                await self._page.close()
                self._page = None
            
            if self._owned_context and self._context:
                await self._context.close()
                self._context = None
                self.logger.debug("Browser context closed")
        except Exception as e:
            self.logger.error(f"Error closing resources: {e}")
