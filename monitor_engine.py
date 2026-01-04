# monitor_engine.py
"""Core monitoring engine that orchestrates scraping and notifications"""

import asyncio
import logging
import concurrent.futures
from datetime import datetime
from typing import Optional, Callable
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from scrapers import DanggeunScraper, BunjangScraper, JoonggonaraScraper, Item
from notifiers import TelegramNotifier, DiscordNotifier, SlackNotifier
from db import DatabaseManager
from settings_manager import SettingsManager
from models import SearchKeyword, NotificationType


class MonitorEngine:
    """
    Core engine for monitoring used marketplaces.
    Coordinates scrapers, database, and notifications.
    """
    
    def __init__(self, settings_manager: SettingsManager):
        self.settings = settings_manager
        self.logger = logging.getLogger("MonitorEngine")
        self.db = DatabaseManager(self.settings.settings.db_path)
        
        # Selenium driver instance
        self._driver: Optional[webdriver.Chrome] = None
        
        self.scrapers = {}
        self.notifiers = []
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self.is_first_run = True  # Skip notifications on initial crawl
        
        # Thread pool for synchronous scraping
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        
        # Callbacks for UI updates
        self.on_new_item: Optional[Callable[[Item], None]] = None
        self.on_price_change: Optional[Callable[[Item, str, str], None]] = None
        self.on_status_update: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
    
    def _create_driver(self) -> webdriver.Chrome:
        """Create shared Chrome driver instance"""
        headless = self.settings.settings.headless_mode
        
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
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        return driver
    
    async def initialize_scrapers(self):
        """Initialize scrapers with shared Selenium driver instance"""
        headless = self.settings.settings.headless_mode
        self._update_status("스크래퍼 및 브라우저 초기화 중...")
        
        # 1. Create shared Selenium driver
        if not self._driver:
            try:
                self._driver = await asyncio.get_event_loop().run_in_executor(
                    self._executor, self._create_driver
                )
                self.logger.info("Shared Selenium driver initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Selenium driver: {e}")
                import traceback
                self.logger.debug(traceback.format_exc())
                self._update_status("브라우저 초기화 실패")
                return

        # 2. Initialize scrapers with shared driver
        # Danggeun
        try:
            scraper = DanggeunScraper(headless=headless, driver=self._driver)
            self.scrapers['danggeun'] = scraper
            self.logger.info("Danggeun scraper initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Danggeun scraper: {e}")
        
        # Bunjang
        try:
            scraper = BunjangScraper(headless=headless, driver=self._driver)
            self.scrapers['bunjang'] = scraper
            self.logger.info("Bunjang scraper initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Bunjang scraper: {e}")
        
        # Joonggonara (Skip in headless, but if enabled, share driver)
        if not headless:
            try:
                scraper = JoonggonaraScraper(headless=headless, driver=self._driver)
                self.scrapers['joonggonara'] = scraper
                self.logger.info("Joonggonara scraper initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Joonggonara scraper: {e}")
        else:
            self.logger.warning("Joonggonara skipped in headless mode (Naver bot detection)")
        
        # Report initialized scrapers
        active_count = len(self.scrapers)
        self.logger.info(f"Initialized {active_count} scraper(s): {list(self.scrapers.keys())}")
        self._update_status(f"스크래퍼 {active_count}개 초기화 완료 (Selenium)")
    
    def initialize_notifiers(self):
        """Initialize notification channels based on settings"""
        self.notifiers.clear()
        
        for config in self.settings.settings.notifiers:
            if not config.enabled:
                continue
            
            try:
                if config.type == NotificationType.TELEGRAM:
                    if config.token and config.chat_id:
                        notifier = TelegramNotifier(config.token, config.chat_id)
                        self.notifiers.append(notifier)
                        self.logger.info("Telegram notifier initialized")
                
                elif config.type == NotificationType.DISCORD:
                    if config.webhook_url:
                        notifier = DiscordNotifier(config.webhook_url)
                        self.notifiers.append(notifier)
                        self.logger.info("Discord notifier initialized")
                
                elif config.type == NotificationType.SLACK:
                    if config.webhook_url:
                        notifier = SlackNotifier(config.webhook_url)
                        self.notifiers.append(notifier)
                        self.logger.info("Slack notifier initialized")
            
            except Exception as e:
                self.logger.error(f"Failed to initialize {config.type.value} notifier: {e}")
    
    async def send_notifications(self, item: Item, is_price_change: bool = False, 
                                  old_price: str = None, new_price: str = None,
                                  listing_id: int = None):
        """Send notifications through all enabled channels"""
        # Check if notifications are enabled globally
        if not self.settings.settings.notifications_enabled:
            return
        
        # Check schedule
        schedule = self.settings.settings.notification_schedule
        if not schedule.is_active_now():
            self.logger.info("Notification skipped - outside scheduled hours")
            return
        
        for notifier in self.notifiers:
            try:
                success = False
                if is_price_change:
                    success = await notifier.send_price_change(item, old_price, new_price)
                else:
                    success = await notifier.send_item(item, with_image=True)
                
                if success and listing_id:
                     # Log notification
                     noti_type = notifier.__class__.__name__.replace("Notifier", "").lower()
                     msg_preview = f"{'📉 Price change' if is_price_change else '🆕 New item'}: {item.title}"
                     self.db.log_notification(listing_id, noti_type, msg_preview)
                     
            except Exception as e:
                self.logger.error(f"Notification error: {e}")
    
    async def search_keyword(self, keyword_config: SearchKeyword) -> int:
        """
        Search for a single keyword across all enabled platforms.
        
        Returns:
            Number of new items found
        """
        new_count = 0
        
        # Fetch blocked sellers once
        blocked_sellers = self.db.get_blocked_sellers()
        blocked_set = set()
        if blocked_sellers:
            blocked_set = {(row['seller_name'], row['platform']) for row in blocked_sellers}
            
        # Execute searches sequentially
        results = []
        active_platforms = []
        self._update_status(f"'{keyword_config.keyword}' 검색 중... ({', '.join(keyword_config.platforms)})")
        
        for platform in keyword_config.platforms:
            scraper = self.scrapers.get(platform)
            if not scraper:
                continue
            
            active_platforms.append(platform)
            try:
                # Run search in thread pool (Selenium is synchronous)
                loop = asyncio.get_event_loop()
                items = await loop.run_in_executor(
                    self._executor,
                    scraper.safe_search,
                    keyword_config.keyword,
                    keyword_config.location
                )
                results.append(items)
            except Exception as e:
                self.logger.error(f"Error searching {platform}: {e}")
                results.append([])
        
        # Process results
        for platform, items in zip(active_platforms, results):
            scraper = self.scrapers.get(platform)
            try:
                # Apply filters
                if keyword_config.min_price or keyword_config.max_price:
                    items = scraper.filter_by_price(
                        items, keyword_config.min_price, keyword_config.max_price
                    )
                
                if keyword_config.exclude_keywords:
                    items = scraper.filter_by_keywords(items, keyword_config.exclude_keywords)
                
                # Filter blocked sellers
                if blocked_set:
                    items = [
                        item for item in items 
                        if not item.seller or (item.seller, item.platform) not in blocked_set
                    ]

                self.logger.info(f"Found {len(items)} items on {platform} for '{keyword_config.keyword}'")
                
                # Process items
                platform_new = 0
                invalid_titles = ["판매완료", "거래완료", "예약중", "No Title", "배송비포함", "제목 없음"]
                
                for item in items:
                    # Validate title
                    if not item.title or len(item.title.strip()) < 2:
                        continue
                        
                    # Filter invalid titles
                    if any(inv in item.title for inv in invalid_titles):
                        continue
                        
                    # Check fuzzy duplicate for reposts
                    if self.db.is_fuzzy_duplicate(item):
                        continue

                    is_new, price_change, listing_id = self.db.add_listing(item)
                    
                    if is_new:
                        platform_new += 1
                        self.logger.info(f"New item: {item.title}")
                        
                        if self.on_new_item:
                            self.on_new_item(item)
                        
                        # Skip notifications on first run to avoid spam
                        # Also check per-keyword notification setting
                        if not self.is_first_run and getattr(keyword_config, 'notify_enabled', True):
                            await self.send_notifications(item, listing_id=listing_id)
                            await asyncio.sleep(0.5)  # Slight delay to prevent spam
                    
                    elif price_change:
                        self.logger.info(f"Price change: {item.title} ({price_change['old_price']} → {price_change['new_price']})")
                        
                        # Check target price in favorites
                        fav = self.db.get_favorite_details(listing_id)
                        new_price_display = price_change['new_price']
                        
                        if fav and fav.get('target_price') and price_change['new_numeric']:
                            if price_change['new_numeric'] <= fav['target_price']:
                                new_price_display += " (🎯 목표가 도달!)"
                                self.logger.info(f"Target price hit for {item.title}")
                        
                        if self.on_price_change:
                            self.on_price_change(item, price_change['old_price'], price_change['new_price'])
                        
                        # Check per-keyword notification setting
                        if getattr(keyword_config, 'notify_enabled', True):
                            await self.send_notifications(
                                item, is_price_change=True,
                                old_price=price_change['old_price'],
                                new_price=new_price_display,
                                listing_id=listing_id
                            )
                            await asyncio.sleep(0.5)
                
                # Record stats
                self.db.record_search_stats(
                    keyword_config.keyword, platform, len(items), platform_new
                )
                new_count += platform_new
                
            except Exception as e:
                self.logger.error(f"Error processing {platform}: {e}")
                if self.on_error:
                    self.on_error(f"{platform} 처리 오류: {e}")
        
        return new_count
    
    async def run_cycle(self) -> int:
        """
        Run one complete monitoring cycle.
        
        Returns:
            Total number of new items found
        """
        total_new = 0
        keywords = self.settings.settings.keywords
        
        for kw in keywords:
            if not kw.enabled:
                continue
            
            # Check custom interval (per-keyword scheduling)
            if kw.custom_interval:
                last_time = self.db.get_last_search_time(kw.keyword)
                if last_time:
                    elapsed = (datetime.now() - last_time).total_seconds() / 60
                    if elapsed < kw.custom_interval:
                        self.logger.info(f"Skipping '{kw.keyword}': interval {kw.custom_interval}m not passed (elapsed: {elapsed:.1f}m)")
                        continue
            
            try:
                new_count = await self.search_keyword(kw)
                total_new += new_count
            except Exception as e:
                self.logger.error(f"Error processing keyword '{kw.keyword}': {e}")
            
            await asyncio.sleep(2)  # Pause between keywords
        
        # After first cycle, enable notifications for future runs
        if self.is_first_run:
            self.is_first_run = False
            self.logger.info(f"Initial crawl complete. Found {total_new} items (notifications skipped for initial run)")
            self._update_status(f"초기 크롤링 완료: {total_new}개 발견 (알림 스킵됨)")
        
        return total_new
    
    async def start(self):
        """Start the monitoring loop"""
        if self.running:
            return
        
        self.running = True
        self.logger.info("Starting monitor engine...")
        
        await self.initialize_scrapers()
        self.initialize_notifiers()
        
        # Send startup notification
        for notifier in self.notifiers:
            try:
                await notifier.send_message("🚀 중고거래 알리미가 시작되었습니다!")
            except Exception as e:
                self.logger.debug(f"Startup notification failed: {e}")
        
        self._update_status("모니터링 시작됨")
        
        while self.running:
            try:
                self._update_status("검색 사이클 시작...")
                new_items = await self.run_cycle()
                
                interval = self.settings.settings.check_interval_seconds
                self._update_status(f"다음 검색까지 {interval}초 대기 중... (새 상품 {new_items}개 발견)")
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                if self.on_error:
                    self.on_error(f"모니터링 오류: {e}")
                await asyncio.sleep(30)  # Wait before retry
        
        self._update_status("모니터링 중지됨")
    
    async def stop(self):
        """Stop the monitoring loop gracefully"""
        self.running = False
        self.logger.info("Stopping monitor engine...")
        
        # Close scrapers (don't close driver individually, they share it)
        self.scrapers.clear()
        
        # Close shared driver with timeout
        if self._driver:
            try:
                loop = asyncio.get_event_loop()
                await asyncio.wait_for(
                    loop.run_in_executor(self._executor, self._driver.quit),
                    timeout=10.0
                )
                self._driver = None
                self.logger.info("Selenium driver closed")
            except asyncio.TimeoutError:
                self.logger.warning("Driver quit timed out, forcing close")
                self._driver = None
            except Exception as e:
                self.logger.error(f"Error closing driver: {e}")
                self._driver = None
        
        # Shutdown thread pool with wait
        try:
            self._executor.shutdown(wait=True, cancel_futures=True)
            self.logger.info("Thread pool shut down")
        except Exception as e:
            self.logger.error(f"Error shutting down executor: {e}")
    
    def _update_status(self, status: str):
        """Update status and notify callback"""
        self.logger.info(status)
        if self.on_status_update:
            self.on_status_update(status)
    
    def get_stats(self) -> dict:
        """Get current statistics"""
        return {
            'total_listings': self.db.get_total_listings(),
            'by_platform': self.db.get_listings_by_platform(),
            'by_keyword': self.db.get_listings_by_keyword(),
            'daily_stats': self.db.get_daily_stats(7),
            'recent_listings': self.db.get_recent_listings(10),
            'price_changes': self.db.get_price_changes(7),
            'price_analysis': self.db.get_keyword_price_stats(),
        }
    
    async def close(self):
        """Clean up resources"""
        await self.stop()
        self.db.close()
