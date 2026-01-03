# scrapers/__init__.py
"""
Scrapers package - Playwright-based web scrapers for used market platforms.

Features:
- Advanced stealth mode (15 bot detection bypass techniques)
- Comprehensive debugging and diagnostics
- Parallel scraping with asyncio
- Automatic retry with exponential backoff
"""

from .base import BaseScraper
from .playwright_base import PlaywrightScraper
from .danggeun import DanggeunScraper
from .bunjang import BunjangScraper
from .joonggonara import JoonggonaraScraper

# Stealth and debug utilities
from .stealth import (
    apply_full_stealth,
    get_random_user_agent,
    get_random_viewport,
    check_bot_detection,
    random_delay,
    scroll_like_human,
    type_like_human
)
from .debug import (
    ScraperDebugger,
    capture_on_error,
    setup_debug_logging
)

# Re-export Item from models for convenience
from models import Item

__all__ = [
    # Scrapers
    'BaseScraper', 
    'PlaywrightScraper',
    'Item', 
    'DanggeunScraper', 
    'BunjangScraper', 
    'JoonggonaraScraper',
    
    # Stealth utilities
    'apply_full_stealth',
    'get_random_user_agent',
    'get_random_viewport',
    'check_bot_detection',
    'random_delay',
    'scroll_like_human',
    'type_like_human',
    
    # Debug utilities
    'ScraperDebugger',
    'capture_on_error',
    'setup_debug_logging',
]
