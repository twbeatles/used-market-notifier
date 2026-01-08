# scrapers/selenium_base.py
"""Selenium-based scraper base class for web scraping"""

import time
import functools
import logging
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from .base import BaseScraper, Item


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Retry decorator with exponential backoff"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
            raise last_exception
        return wrapper
    return decorator


class SeleniumScraper(BaseScraper):
    """Base class for Selenium-based scrapers"""
    
    def __init__(self, headless: bool = True, disable_images: bool = True, 
                 driver: webdriver.Chrome = None):
        super().__init__()
        self._owned_driver = False
        if driver:
            self.driver = driver
        else:
            self.driver = self._create_driver(headless, disable_images)
            self._owned_driver = True
        self.wait_time = 10
    
    def _create_driver(self, headless: bool, disable_images: bool) -> webdriver.Chrome:
        """Initialize and configure Chrome driver"""
        options = Options()
        if headless:
            options.add_argument('--headless=new')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
        
        # Performance optimizations
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-background-timer-throttling')
        options.page_load_strategy = 'eager'  # DOM ready, don't wait for all resources
        
        if disable_images:
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
            }
            options.add_experimental_option("prefs", prefs)
        
        try:
            # Use cached driver path if possible
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(30)  # 30 second timeout
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            return driver
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome driver: {e}")
            raise e
    
    def search(self, keyword: str, location: str = None) -> List[Item]:
        """
        Abstract search method - must be implemented by subclasses.
        
        Args:
            keyword: Search term
            location: Optional location filter
            
        Returns:
            List of Item objects
        """
        raise NotImplementedError("Subclasses must implement search()")
    
    @retry(max_attempts=3, delay=1.0)
    def safe_search(self, keyword: str, location: str = None) -> List[Item]:
        """Search with automatic retry on failure"""
        return self.search(keyword, location)
    
    def set_shared_driver(self, driver: webdriver.Chrome):
        """Set shared driver instance (for engine-managed driver)"""
        if self._owned_driver and self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
        self.driver = driver
        self._owned_driver = False
    
    def close(self):
        """Clean up Selenium resources"""
        if hasattr(self, 'driver') and self.driver and self._owned_driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.error(f"Error closing driver: {e}")
