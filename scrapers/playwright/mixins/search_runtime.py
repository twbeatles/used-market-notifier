"""Mixin module: search_runtime."""

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

class PlaywrightSearchRuntimeMixin:
    """Search Runtime behavior."""

    @abstractmethod
    async def search(self, keyword: str, location: str | None = None) -> list[Item]:
        """
        Search for the keyword on the platform and return a list of Items.
        
        Args:
            keyword: Search term
            location: Optional location filter (platform-specific)
        
        Returns:
            List of Item objects
        """
        pass
    

    @staticmethod
    def _run_async(coro_factory: Callable[[], Awaitable[T]]) -> T:
        async def _await_factory() -> T:
            return await coro_factory()

        try:
            return asyncio.run(_await_factory())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(_await_factory())
            finally:
                loop.close()

    def safe_search(self, keyword: str, location: str | None = None) -> list[Item]:
        """Synchronous compatibility entrypoint."""
        async def _search_session() -> list[Item]:
            temporary_session = not self._started
            if temporary_session:
                await self.start()
            try:
                return await self._safe_search_async(keyword, location)
            finally:
                if temporary_session:
                    await self.close()

        return self._run_async(_search_session)

    def enrich_item(self, item: Item) -> Item:
        """Default Playwright enrichment hook; subclasses can override."""
        async def _enrich_session() -> Item:
            temporary_session = not self._started
            if temporary_session:
                await self.start()
            try:
                return await self.enrich_item_async(item)
            finally:
                if temporary_session:
                    await self.close()

        return self._run_async(_enrich_session)

    async def enrich_item_async(self, item: Item) -> Item:
        """Async metadata enrichment hook; subclasses can override."""
        return item


    @async_retry(max_attempts=3, delay=1.0)
    async def _safe_search_async(self, keyword: str, location: str | None = None) -> list[Item]:
        """
        Safe wrapper around search with debugging and auto-retry.
        """
        # Create debugger for this session if debug mode is enabled
        if self.debug_mode:
            self.debugger = self._create_debugger(keyword)
        
        try:
            items = await self.search(keyword, location)
            if await self._page_looks_blocked():
                self._last_failure_kind = "captcha_or_blocked"
                return []
            self._last_failure_kind = None if items else "parser_zero"
            
            if self.debugger:
                self.debugger.log_items_found(len(items))
                await self.debugger.finalize("completed")
            
            return items
            
        except Exception as e:
            if self._last_failure_kind is None:
                self._last_failure_kind = "unknown"
            self.logger.error(
                f"Search failed for '{keyword}': kind={self._last_failure_kind} error={e}"
            )
            
            # Capture error diagnostics
            if self.debug_mode and self.debugger and self._page:
                await capture_on_error(self._page, self.debugger, e, f"search_{keyword}")
                await self.debugger.finalize("failed")
            raise
