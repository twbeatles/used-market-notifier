"""Compatibility facade for Playwright scraper base."""

from scrapers.playwright import PlaywrightScraper, async_retry

__all__ = ["PlaywrightScraper", "async_retry"]
