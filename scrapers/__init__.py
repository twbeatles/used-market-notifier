# scrapers/__init__.py
from .base import BaseScraper, ScraperDependencyUnavailable

try:
    from .danggeun import DanggeunScraper
    from .bunjang import BunjangScraper
    from .joonggonara import JoonggonaraScraper
    from .selenium_base import SeleniumScraper
except Exception:
    # Optional runtime dependency: Selenium may not be installed.
    DanggeunScraper = None
    BunjangScraper = None
    JoonggonaraScraper = None
    SeleniumScraper = None

try:
    from .playwright_danggeun import PlaywrightDanggeunScraper
    from .playwright_bunjang import PlaywrightBunjangScraper
    from .playwright_joonggonara import PlaywrightJoonggonaraScraper
except Exception:
    # Optional runtime dependency: Playwright might not be installed.
    PlaywrightDanggeunScraper = None
    PlaywrightBunjangScraper = None
    PlaywrightJoonggonaraScraper = None

# Re-export Item from models for convenience
from models import Item

__all__ = [
    'BaseScraper',
    'ScraperDependencyUnavailable',
    'SeleniumScraper',
    'Item',
    'DanggeunScraper',
    'BunjangScraper',
    'JoonggonaraScraper',
    'PlaywrightDanggeunScraper',
    'PlaywrightBunjangScraper',
    'PlaywrightJoonggonaraScraper',
]
