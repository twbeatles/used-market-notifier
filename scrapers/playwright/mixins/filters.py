"""Mixin module: filters."""

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

class PlaywrightFiltersMixin:
    """Filters behavior."""

    def _is_valid_title(self, title: str) -> bool:
        """Check if title is valid (not sold out or placeholder)"""
        if not title or len(title.strip()) < 2:
            return False
        title_lower = title.strip().lower()
        for pattern in self.INVALID_TITLE_PATTERNS:
            if pattern.lower() in title_lower:
                return False
        return True
    

    def filter_by_price(
        self,
        items: list[Item],
        min_price: int | None = None,
        max_price: int | None = None,
    ) -> list[Item]:
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
    

    def filter_by_keywords(
        self,
        items: list[Item],
        exclude_keywords: list[str] | None = None,
    ) -> list[Item]:
        """Filter out items containing excluded keywords"""
        if not exclude_keywords:
            return items
        result = []
        for item in items:
            title_lower = item.title.lower()
            if not any(ex.lower() in title_lower for ex in exclude_keywords):
                result.append(item)
        return result
    

    @staticmethod
    def _metric_int(metrics: dict[str, object], key: str) -> int:
        value = metrics.get(key, 0)
        try:
            return int(value)  # type: ignore[arg-type]
        except Exception:
            return 0
