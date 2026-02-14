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
from auto_tagger import AutoTagger


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
        
        # Auto-tagger for automatic tag detection
        self.auto_tagger = AutoTagger()
        
        # Consecutive empty result tracking per platform
        self._empty_result_counter = {}
        
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
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-background-timer-throttling')
        options.page_load_strategy = 'eager'  # Don't wait for all resources
        
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
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
    
    def _cleanup_driver(self):
        """Safe driver cleanup to prevent memory leaks"""
        if self._driver:
            try:
                self._driver.quit()
                self.logger.info("Selenium driver cleaned up")
            except Exception as e:
                self.logger.warning(f"Error during driver cleanup: {e}")
            finally:
                self._driver = None
    
    def _ensure_driver(self) -> bool:
        """Ensure driver is alive, recreate if needed"""
        if self._driver:
            try:
                # Health check - try to access current_url
                _ = self._driver.current_url
                return True
            except Exception as e:
                self.logger.warning(f"Driver health check failed: {e}")
                self._cleanup_driver()
        
        try:
            self._driver = self._create_driver()
            self.logger.info("Driver recreated successfully")
            return True
        except Exception as e:
            self.logger.error(f"Driver creation failed: {e}")
            return False
    
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
        
        # Joonggonara (works with limitations in headless due to Naver bot detection)
        try:
            if headless:
                self.logger.warning("중고나라: 헤드리스 모드에서 네이버 봇 탐지로 결과가 제한될 수 있습니다")
            scraper = JoonggonaraScraper(headless=headless, driver=self._driver)
            self.scrapers['joonggonara'] = scraper
            self.logger.info("Joonggonara scraper initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Joonggonara scraper: {e}")
        
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
                import time as _time
                start_time = _time.time()
                
                loop = asyncio.get_event_loop()
                items = await loop.run_in_executor(
                    self._executor,
                    scraper.safe_search,
                    keyword_config.keyword,
                    keyword_config.location
                )
                
                elapsed = _time.time() - start_time
                self.logger.debug(f"{platform} 검색 완료: {len(items)}개, {elapsed:.2f}초")
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
                
                # Track consecutive empty results per platform
                if len(items) == 0:
                    self._empty_result_counter[platform] = self._empty_result_counter.get(platform, 0) + 1
                    if self._empty_result_counter[platform] >= 3:
                        self.logger.warning(f"{platform}: 3회 연속 빈 결과 - 플랫폼 상태 확인 필요")
                        if self.on_error:
                            self.on_error(f"⚠️ {platform} 스크래핑 문제 감지 (3회 연속 빈 결과)")
                else:
                    self._empty_result_counter[platform] = 0
                
                # Process items
                platform_new = 0
                
                for item in items:
                    # Basic title validation (scrapers already filter invalid titles)
                    if not item.title or len(item.title.strip()) < 2:
                        continue
                        
                    # Check fuzzy duplicate for reposts
                    if self.db.is_fuzzy_duplicate(item):
                        continue

                    is_new, price_change, listing_id = self.db.add_listing(item)
                    
                    if is_new:
                        platform_new += 1
                        self.logger.info(f"New item: {item.title}")
                        
                        # Auto-tagging: analyze title and add tags
                        if self.settings.settings.auto_tagging_enabled and listing_id:
                            tags = self.auto_tagger.analyze(item.title)
                            if tags:
                                self.db.add_auto_tags(listing_id, tags)
                                self.logger.debug(f"Auto-tagged '{item.title}' with: {tags}")
                        
                        # Auto-detect sale status from title
                        if listing_id:
                            detected_status = self.db.detect_sale_status(item.title)
                            if detected_status != 'for_sale':
                                self.db.update_sale_status(listing_id, detected_status)
                                self.logger.debug(f"Detected sale status '{detected_status}' for: {item.title}")
                        
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
        # Driver health check - ensure session is alive
        if self._driver:
            try:
                _ = self._driver.current_url
            except Exception as e:
                self.logger.warning(f"Driver session expired: {e}")
                self._update_status("브라우저 세션 복구 중...")
                self._cleanup_driver()
                await self.initialize_scrapers()
        
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
        
        # After processing all platforms
        if total_new == 0 and not self.is_first_run:
            self._update_status("검색 결과가 없습니다. 키워드나 필터를 확인해주세요.")
        # Reset first run flag after first cycle
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
        
        try:
            await self.initialize_scrapers()
            self.initialize_notifiers()
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            if self.on_error:
                self.on_error(f"초기화 실패: {e}")
            self.running = False
            return
        
        # Check if we have any scrapers
        if not self.scrapers:
            self.logger.error("No scrapers initialized, cannot start monitoring")
            if self.on_error:
                self.on_error("스크래퍼가 없습니다. 브라우저를 확인해주세요.")
            self.running = False
            return
        
        # Send startup notification
        for notifier in self.notifiers:
            try:
                await notifier.send_message("🚀 중고거래 알리미가 시작되었습니다!")
            except Exception as e:
                self.logger.debug(f"Startup notification failed: {e}")
        
        self._update_status("모니터링 시작됨")
        
        error_count = 0
        max_errors = 5  # Maximum consecutive errors before stopping
        
        while self.running:
            try:
                # Validate driver before each cycle
                if not self._ensure_driver():
                    self.logger.warning("Driver not available, attempting to reinitialize scrapers...")
                    try:
                        await self.initialize_scrapers()
                    except Exception as e:
                        self.logger.error(f"Failed to reinitialize scrapers: {e}")
                        error_count += 1
                        if error_count >= max_errors:
                            self.logger.error("Too many errors, stopping monitoring")
                            if self.on_error:
                                self.on_error("오류가 너무 많습니다. 모니터링 중지.")
                            break
                        await asyncio.sleep(30)
                        continue
                
                self._update_status("검색 사이클 시작...")
                new_items = await self.run_cycle()
                
                # Reset error count on success
                error_count = 0
                
                interval = self.settings.settings.check_interval_seconds
                self._update_status(f"다음 검색까지 {interval}초 대기 중... (새 상품 {new_items}개 발견)")
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                self.logger.info("Monitor loop cancelled")
                break
            except Exception as e:
                error_count += 1
                self.logger.error(f"Error in monitoring loop (attempt {error_count}): {e}")
                import traceback
                self.logger.debug(traceback.format_exc())
                
                if self.on_error:
                    self.on_error(f"모니터링 오류: {e}")
                
                if error_count >= max_errors:
                    self.logger.error("Too many consecutive errors, stopping")
                    if self.on_error:
                        self.on_error("오류가 반복되어 모니터링을 중지합니다.")
                    break
                
                # Wait before retry, increasing delay with error count
                await asyncio.sleep(min(30 * error_count, 120))
        
        self.running = False
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
