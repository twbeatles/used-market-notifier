"""Mixin module: lifecycle."""

"""Playwright scraper base package."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Awaitable, Callable, Literal, Optional, TypeVar

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from models import Item

from ...stealth import (
    apply_full_stealth,
    get_random_user_agent,
    get_random_viewport,
    check_bot_detection,
    random_delay,
    scroll_like_human,
)
from ...debug import ScraperDebugger, capture_on_error
from ..retry import async_retry

WaitUntil = Literal["commit", "domcontentloaded", "load", "networkidle"]
T = TypeVar("T")

class PlaywrightLifecycleMixin:
    """Lifecycle behavior."""

    def __init__(
        self, 
        headless: bool = True, 
        disable_images: bool = True,
        context: BrowserContext | None = None,
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
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._started = False
        self._last_failure_kind: str | None = None
        self._page: Optional[Page] = None
        self.use_stealth = use_stealth
        self.debug_mode = debug_mode
        self.debug_level = debug_level
        self.random_fingerprint = random_fingerprint
        
        # Debugger instance (created per search if debug_mode is True)
        self.debugger: Optional[ScraperDebugger] = None
        
        # Track bot detection status
        self._bot_detection_passed = None


    async def start(self) -> None:
        """Start and retain a Playwright browser/context for repeated searches."""
        if self._started and self._context:
            return
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._launch_browser(self._playwright)
            self._context = await self._create_context(self._browser)
            self._owned_context = True
            self._started = True
            self._last_failure_kind = None
        except Exception:
            self._last_failure_kind = "runtime_unavailable"
            await self.close()
            raise
        

    async def initialize(
        self,
        playwright: Playwright | None = None,
        browser: Browser | None = None,
    ):
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
            self._browser = browser
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
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            self._started = False
        except Exception as e:
            self.logger.error(f"Error closing resources: {e}")


    def is_healthy(self) -> bool:
        """Return whether the retained Playwright resources appear usable."""
        if self._last_failure_kind in {"runtime_unavailable", "blocked_or_empty"}:
            return False
        if not self._started:
            return True
        if self._context is None or self._browser is None:
            return False
        try:
            return self._browser.is_connected()
        except Exception:
            return False


    def get_last_failure_kind(self) -> str | None:
        return self._last_failure_kind
