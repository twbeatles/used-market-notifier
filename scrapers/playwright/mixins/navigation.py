"""Mixin module: navigation."""

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

class PlaywrightNavigationMixin:
    """Navigation behavior."""

    async def navigate_with_retry(
        self, 
        url: str, 
        wait_until: WaitUntil = "domcontentloaded",
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
                    if response.status in {403, 429}:
                        self._last_failure_kind = f"http_{response.status}"
                    if self.debugger:
                        self.debugger.log_warning(f"HTTP {response.status}")
                        await self.debugger.take_screenshot(page, f"http_error_{response.status}")
                    if response.status in {403, 429}:
                        return False
                
                if self.debug_mode and self.debugger:
                    await self.debugger.take_screenshot(page, "navigation_complete")
                
                return True
                
            except Exception as e:
                self.logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
                self._last_failure_kind = "navigation_timeout"
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
    

    async def _page_looks_blocked(self) -> bool:
        if self._page is None:
            return False
        try:
            text = (await self._page.locator("body").inner_text(timeout=1000) or "").lower()
        except Exception:
            return False
        indicators = (
            "captcha",
            "보안문자",
            "자동입력",
            "비정상적인 접근",
            "잠시 후 다시 시도",
            "access denied",
            "too many requests",
        )
        return any(token in text for token in indicators)
