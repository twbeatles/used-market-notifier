# monitor_engine.py
"""
Core monitoring engine that orchestrates scraping and notifications.

Features:
- Playwright-based browser automation
- Parallel scraping with asyncio.gather
- Advanced stealth mode for bot detection bypass
- Comprehensive debugging and diagnostics
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Callable
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext
from scrapers import DanggeunScraper, BunjangScraper, JoonggonaraScraper, Item
from scrapers.stealth import apply_full_stealth, get_random_user_agent, get_random_viewport
from scrapers.debug import setup_debug_logging
from notifiers import TelegramNotifier, DiscordNotifier, SlackNotifier
from db import DatabaseManager
from settings_manager import SettingsManager
from models import SearchKeyword, NotificationType


class MonitorEngine:
    """
    Core engine for monitoring used marketplaces.
    Coordinates scrapers, database, and notifications.
    
    Features:
    - Playwright browser automation
    - Parallel scraping (asyncio.gather)
    - Advanced stealth mode (15 techniques)
    - Debug mode with screenshots and network logs
    """
    
    def __init__(self, settings_manager: SettingsManager, debug_mode: bool = False):
        self.settings = settings_manager
        self.debug_mode = debug_mode
        self.logger = logging.getLogger("MonitorEngine")
        self.db = DatabaseManager(self.settings.settings.db_path)
        
        # Setup debug logging if debug mode is enabled
        if debug_mode:
            setup_debug_logging("DEBUG")
        
        # Playwright instances
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        
        self.scrapers = {}
        self.notifiers = []
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self.is_first_run = True  # Skip notifications on initial crawl
        
        # Callbacks for UI updates
        self.on_new_item: Optional[Callable[[Item], None]] = None
        self.on_price_change: Optional[Callable[[Item, str, str], None]] = None
        self.on_status_update: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
    
    async def initialize_scrapers(self):
        """Initialize scrapers with Playwright browser"""
        import gc
        
        headless = self.settings.settings.headless_mode
        self._update_status("Playwright 브라우저 초기화 중...")
        
        try:
            # 1. Initialize Playwright
            if not self._playwright:
                self._playwright = await async_playwright().start()
                self.logger.info("Playwright started")
            
            # 2. Launch browser
            if not self._browser:
                launch_options = {
                    "headless": headless,
                    "args": [
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-extensions",
                        "--disable-infobars",
                        "--disable-blink-features=AutomationControlled",  # Key for stealth
                    ]
                }
                self._browser = await self._playwright.chromium.launch(**launch_options)
                self.logger.info(f"Chromium browser launched (headless={headless})")
            
            # 3. Create shared context with random fingerprint
            if not self._context:
                user_agent = get_random_user_agent()
                viewport = get_random_viewport()
                
                self._context = await self._browser.new_context(
                    viewport=viewport,
                    user_agent=user_agent,
                    locale="ko-KR",
                    timezone_id="Asia/Seoul",
                    permissions=["geolocation"],
                    geolocation={"latitude": 37.5665, "longitude": 126.9780},  # Seoul
                )
                
                # Apply full stealth mode
                await apply_full_stealth(self._context)
                self.logger.info("🛡️ Full stealth mode applied (15 techniques)")
                
                # ===== PERFORMANCE OPTIMIZATIONS =====
                # 1. Block images for performance
                await self._context.route("**/*.{png,jpg,jpeg,gif,webp,svg,ico}", lambda route: route.abort())
                
                # 2. Block fonts to reduce bandwidth
                await self._context.route("**/*.{woff,woff2,ttf,otf,eot}", lambda route: route.abort())
                
                # 3. Block analytics and tracking scripts
                await self._context.route("**/{analytics,tracking,ads,advertisement,google-analytics,gtag}*", lambda route: route.abort())
                await self._context.route("**/googlesyndication.com/**", lambda route: route.abort())
                await self._context.route("**/doubleclick.net/**", lambda route: route.abort())
                await self._context.route("**/facebook.net/**", lambda route: route.abort())
                
                self.logger.info("⚡ Performance optimization: blocking images, fonts, analytics")
                self.logger.info(f"Browser context created (UA: {user_agent[:50]}...)")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Playwright: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            self._update_status("브라우저 초기화 실패")
            return
        
        # 4. Initialize scrapers with shared context
        # Danggeun
        try:
            scraper = DanggeunScraper(
                headless=headless, 
                context=self._context,
                debug_mode=self.debug_mode
            )
            await scraper.initialize(browser=self._browser)
            self.scrapers['danggeun'] = scraper
            self.logger.info("Danggeun scraper initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Danggeun scraper: {e}")
        
        # Bunjang
        try:
            scraper = BunjangScraper(
                headless=headless, 
                context=self._context,
                debug_mode=self.debug_mode
            )
            await scraper.initialize(browser=self._browser)
            self.scrapers['bunjang'] = scraper
            self.logger.info("Bunjang scraper initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Bunjang scraper: {e}")
        
        # Joonggonara (with enhanced stealth mode)
        try:
            scraper = JoonggonaraScraper(
                headless=headless, 
                context=self._context,
                debug_mode=self.debug_mode
            )
            await scraper.initialize(browser=self._browser)
            self.scrapers['joonggonara'] = scraper
            self.logger.info("Joonggonara scraper initialized (enhanced stealth mode)")
        except Exception as e:
            self.logger.error(f"Failed to initialize Joonggonara scraper: {e}")
        
        # Report initialized scrapers
        active_count = len(self.scrapers)
        self.logger.info(f"Initialized {active_count} scraper(s): {list(self.scrapers.keys())}")
        stealth_status = "🛡️ Stealth ON" if True else ""
        debug_status = "🔍 Debug ON" if self.debug_mode else ""
        self._update_status(f"Playwright 스크래퍼 {active_count}개 초기화 완료 {stealth_status} {debug_status}".strip())
    
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
        Uses parallel scraping with asyncio.gather for better performance.
        
        Returns:
            Number of new items found
        """
        new_count = 0
        
        # Fetch blocked sellers once
        blocked_sellers = self.db.get_blocked_sellers()
        blocked_set = set()
        if blocked_sellers:
            blocked_set = {(row['seller_name'], row['platform']) for row in blocked_sellers}
        
        # Execute searches in PARALLEL using asyncio.gather
        active_platforms = []
        search_tasks = []
        
        self._update_status(f"'{keyword_config.keyword}' 검색 중... ({', '.join(keyword_config.platforms)})")
        
        for platform in keyword_config.platforms:
            scraper = self.scrapers.get(platform)
            if not scraper:
                continue
            
            active_platforms.append(platform)
            # Create async task for each platform
            search_tasks.append(scraper.safe_search(keyword_config.keyword, keyword_config.location))
        
        # Run all searches in parallel
        if search_tasks:
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
        else:
            results = []
        
        # Process results
        for i, platform in enumerate(active_platforms):
            items = results[i]
            
            # Handle exceptions
            if isinstance(items, Exception):
                self.logger.error(f"Error searching {platform}: {items}")
                items = []
            
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
                        if not self.is_first_run:
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
        self.logger.info("Starting monitor engine (Playwright)...")
        
        await self.initialize_scrapers()
        self.initialize_notifiers()
        
        # Send startup notification
        for notifier in self.notifiers:
            try:
                await notifier.send_message("🚀 중고거래 알리미가 시작되었습니다! (Playwright)")
            except Exception as e:
                self.logger.debug(f"Startup notification failed: {e}")
        
        self._update_status("모니터링 시작됨 (Playwright)")
        
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
    
    async def stop_async(self):
        """Stop the monitoring loop (async version)"""
        self.running = False
        self.logger.info("Stopping monitor engine...")
        
        # Close scrapers
        for name, scraper in self.scrapers.items():
            try:
                await scraper.close()
                self.logger.info(f"Closed {name} scraper")
            except Exception as e:
                self.logger.error(f"Error closing {name} scraper: {e}")
        
        self.scrapers.clear()
        
        # Close Playwright resources
        if self._context:
            try:
                await self._context.close()
                self._context = None
                self.logger.info("Browser context closed")
            except Exception as e:
                self.logger.error(f"Error closing context: {e}")
        
        if self._browser:
            try:
                await self._browser.close()
                self._browser = None
                self.logger.info("Browser closed")
            except Exception as e:
                self.logger.error(f"Error closing browser: {e}")
        
        if self._playwright:
            try:
                await self._playwright.stop()
                self._playwright = None
                self.logger.info("Playwright stopped")
            except Exception as e:
                self.logger.error(f"Error stopping Playwright: {e}")
    
    def stop(self):
        """Stop the monitoring loop (sync wrapper for compatibility)"""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.stop_async())
        except RuntimeError:
            # No running loop, try to run directly
            asyncio.run(self.stop_async())
    
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
    
    def close(self):
        """Clean up resources"""
        self.stop()
        self.db.close()
