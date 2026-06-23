"""Mixin module: debug."""

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

class PlaywrightDebugMixin:
    """Debug behavior."""

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
    

    async def take_screenshot(self, filename: str | None = None) -> bytes | None:
        """Take a screenshot for debugging"""
        if not self._page:
            return None
        
        if filename:
            await self._page.screenshot(path=filename, full_page=True)
            self.logger.info(f"📸 Screenshot saved: {filename}")
        
        return await self._page.screenshot(full_page=True)


    async def dump_debug_artifacts(self, keyword: str, summary: dict, *, prefix: str = "anomaly") -> dict[str, str]:
        """Persist lightweight HTML/screenshot/summary artifacts for anomalous searches."""
        page = await self.get_page()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_keyword = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(keyword or ""))[:40] or "keyword"
        base_name = f"{self.__class__.__name__.lower()}_{safe_keyword}_{prefix}_{timestamp}"
        self.DEBUG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        html_path = self.DEBUG_OUTPUT_DIR / f"{base_name}.html"
        json_path = self.DEBUG_OUTPUT_DIR / f"{base_name}.json"
        png_path = self.DEBUG_OUTPUT_DIR / f"{base_name}.png"

        html = await page.content()
        html_path.write_text(html, encoding="utf-8")
        json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        await page.screenshot(path=str(png_path), full_page=True)

        self.logger.warning(
            f"Debug artifacts written: html={html_path} screenshot={png_path} summary={json_path}"
        )
        return {
            "html": str(html_path),
            "summary": str(json_path),
            "screenshot": str(png_path),
        }
