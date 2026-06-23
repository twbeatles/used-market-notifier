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

from ..stealth import (
    apply_full_stealth,
    get_random_user_agent,
    get_random_viewport,
    check_bot_detection,
    random_delay,
    scroll_like_human,
)
from ..debug import ScraperDebugger, capture_on_error
from .retry import async_retry

WaitUntil = Literal["commit", "domcontentloaded", "load", "networkidle"]
T = TypeVar("T")

from .mixins import (
    PlaywrightLifecycleMixin,
    PlaywrightNavigationMixin,
    PlaywrightSearchRuntimeMixin,
    PlaywrightDebugMixin,
    PlaywrightFiltersMixin,
)

class PlaywrightScraper(
    PlaywrightLifecycleMixin,
    PlaywrightNavigationMixin,
    PlaywrightSearchRuntimeMixin,
    PlaywrightDebugMixin,
    PlaywrightFiltersMixin,
    ABC,
):
    """Playwright scraper base class."""

    DEFAULT_TIMEOUT = 15000
    NAVIGATION_TIMEOUT = 20000
    SELECTOR_TIMEOUT = 10000
    WAIT_STRATEGIES = ["domcontentloaded", "load", "networkidle"]
    DEBUG_OUTPUT_DIR = Path("debug_output")
    INVALID_TITLE_PATTERNS = [
        "판매완료", "예약중", "거래완료", "No Title", "광고", 
        "배송비포함", "검수가능", "제목 없음"
    ]
