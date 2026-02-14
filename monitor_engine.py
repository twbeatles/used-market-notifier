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
    
    def __init__(self, settings_manager: SettingsManager, db: Optional[DatabaseManager] = None):
        self.settings = settings_manager
        self.logger = logging.getLogger("MonitorEngine")
        self.db = db or DatabaseManager(self.settings.settings.db_path)
        self._owns_db = db is None
        
        # Selenium driver instance
        self._driver: Optional[webdriver.Chrome] = None
        
        self.scrapers = {}
        self.notifiers = []
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self.is_first_run = True  # Skip notifications on initial crawl
        
        # Thread pool for synchronous scraping (created lazily on start()).
        self._executor: Optional[concurrent.futures.ThreadPoolExecutor] = None

        # Stop/close state for idempotent teardown
        self._resources_closed = False
        self._close_called = False
        self._start_task: Optional[asyncio.Task] = None
        self._stop_event: Optional[asyncio.Event] = None
        
        # Auto-tagger for automatic tag detection (optionally from settings.tag_rules)
        self.auto_tagger = self._create_auto_tagger_from_settings()
        
        # Consecutive empty result tracking per platform
        self._empty_result_counter = {}

        # Per-cycle aggregates (set by run_cycle)
        self._cycle_platform_raw_counts: Optional[dict] = None
        self._cycle_platform_attempts: Optional[dict] = None
        
        # Callbacks for UI updates
        self.on_new_item: Optional[Callable[[Item], None]] = None
        self.on_price_change: Optional[Callable[[Item, str, str], None]] = None
        self.on_status_update: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

    def _create_auto_tagger_from_settings(self) -> AutoTagger:
        """
        Build AutoTagger rules from settings.tag_rules if present.
        Falls back to AutoTagger defaults if tag_rules is empty/invalid.
        """
        try:
            tag_rules = getattr(self.settings.settings, "tag_rules", None) or []
            if not tag_rules:
                return AutoTagger()

            rules = []
            for tr in tag_rules:
                # tr is expected to be models.TagRule, but accept dict-like too.
                try:
                    tag_name = getattr(tr, "tag_name", None) or tr.get("tag_name")
                    keywords = getattr(tr, "keywords", None) or tr.get("keywords") or []
                    color = getattr(tr, "color", None) or tr.get("color") or "#89b4fa"
                    icon = getattr(tr, "icon", None) or tr.get("icon") or "🏷️"
                    enabled = getattr(tr, "enabled", None)
                    if enabled is None:
                        enabled = tr.get("enabled", True) if hasattr(tr, "get") else True
                    if not tag_name:
                        continue
                    rules.append(
                        {
                            "tag_name": tag_name,
                            "keywords": list(keywords) if keywords else [],
                            "color": color,
                            "icon": icon,
                            "enabled": bool(enabled),
                        }
                    )
                except Exception:
                    continue

            return AutoTagger(custom_rules=rules) if rules else AutoTagger()
        except Exception:
            return AutoTagger()
    
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
    
    async def _sleep_or_stop(self, seconds: float) -> None:
        """Sleep unless a stop has been requested (improves responsiveness on stop/close)."""
        if seconds <= 0:
            return
        ev = self._stop_event
        if ev is None:
            await asyncio.sleep(seconds)
            return
        if ev.is_set():
            return
        try:
            await asyncio.wait_for(ev.wait(), timeout=seconds)
        except asyncio.TimeoutError:
            return

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
        """Search a single keyword across enabled platforms.

        Returns:
            Number of new items found.
        """
        new_count = 0

        # Fetch blocked sellers once
        blocked_sellers = self.db.get_blocked_sellers()
        blocked_set = set()
        if blocked_sellers:
            blocked_set = {(row["seller_name"], row["platform"]) for row in blocked_sellers}

        platform_results: dict[str, list[Item]] = {}
        active_platforms: list[str] = []

        self._update_status(f"검색중: '{keyword_config.keyword}' ({', '.join(keyword_config.platforms)})")

        for platform in keyword_config.platforms:
            scraper = self.scrapers.get(platform)
            if not scraper:
                continue

            active_platforms.append(platform)
            if self._cycle_platform_attempts is not None:
                self._cycle_platform_attempts[platform] = self._cycle_platform_attempts.get(platform, 0) + 1

            try:
                loop = asyncio.get_event_loop()
                items_raw = await loop.run_in_executor(
                    self._executor,
                    scraper.safe_search,
                    keyword_config.keyword,
                    keyword_config.location,
                )
            except Exception as e:
                self.logger.error(f"Error searching {platform}: {e}")
                items_raw = []

            if self._cycle_platform_raw_counts is not None:
                self._cycle_platform_raw_counts[platform] = self._cycle_platform_raw_counts.get(platform, 0) + len(
                    items_raw
                )
            platform_results[platform] = items_raw

        for platform in active_platforms:
            items_raw = platform_results.get(platform) or []
            raw_count = len(items_raw)

            # Apply per-keyword filters (price/location/exclude keywords)
            items: list[Item] = []
            for it in items_raw:
                if not getattr(it, "keyword", None):
                    it.keyword = keyword_config.keyword
                if keyword_config.matches(it):
                    items.append(it)

            if raw_count > 0 and len(items) == 0:
                self.logger.info(
                    f"{platform}: all {raw_count} raw items filtered out "
                    f"(location={keyword_config.location!r}, min={keyword_config.min_price}, "
                    f"max={keyword_config.max_price}, exclude={len(keyword_config.exclude_keywords or [])})"
                )

            # Filter blocked sellers (best-effort: only if scraper provides seller)
            if blocked_set:
                items = [
                    it
                    for it in items
                    if not it.seller or (it.seller, it.platform) not in blocked_set
                ]

            self.logger.info(f"Found {len(items)} items on {platform} for '{keyword_config.keyword}'")

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
                        if detected_status != "for_sale":
                            self.db.update_sale_status(listing_id, detected_status)
                            self.logger.debug(f"Detected sale status '{detected_status}' for: {item.title}")

                    if self.on_new_item:
                        self.on_new_item(item)

                    # Skip notifications on first run to avoid spam
                    if not self.is_first_run and getattr(keyword_config, "notify_enabled", True):
                        await self.send_notifications(item, listing_id=listing_id)
                        await self._sleep_or_stop(0.5)

                elif price_change:
                    self.logger.info(
                        f"Price change: {item.title} ({price_change['old_price']} -> {price_change['new_price']})"
                    )

                    # Check target price in favorites
                    fav = self.db.get_favorite_details(listing_id)
                    new_price_display = price_change["new_price"]

                    if fav and fav.get("target_price") and price_change.get("new_numeric"):
                        if price_change["new_numeric"] <= fav["target_price"]:
                            new_price_display += " (target hit)"
                            self.logger.info(f"Target price hit for {item.title}")

                    if self.on_price_change:
                        self.on_price_change(item, price_change["old_price"], price_change["new_price"])

                    if getattr(keyword_config, "notify_enabled", True):
                        await self.send_notifications(
                            item,
                            is_price_change=True,
                            old_price=price_change["old_price"],
                            new_price=new_price_display,
                            listing_id=listing_id,
                        )
                        await self._sleep_or_stop(0.5)

            # Record stats (items_found is the number after filters)
            self.db.record_search_stats(keyword_config.keyword, platform, len(items), platform_new)
            new_count += platform_new

        return new_count

    async def run_cycle(self) -> int:
        """Run one complete monitoring cycle."""
        # Driver health check - ensure session is alive
        if self._driver:
            try:
                _ = self._driver.current_url
            except Exception as e:
                self.logger.warning(f"Driver session expired: {e}")
                self._cleanup_driver()
                await self.initialize_scrapers()

        total_new = 0
        keywords = self.settings.settings.keywords

        # Aggregate raw scrape counts per platform for this cycle (reduces false positives).
        self._cycle_platform_raw_counts = {p: 0 for p in self.scrapers.keys()}
        self._cycle_platform_attempts = {p: 0 for p in self.scrapers.keys()}

        try:
            for kw in keywords:
                if not kw.enabled:
                    continue

                # Check custom interval (per-keyword scheduling)
                if kw.custom_interval:
                    last_time = self.db.get_last_search_time(kw.keyword)
                    if last_time:
                        elapsed = (datetime.now() - last_time).total_seconds() / 60
                        if elapsed < kw.custom_interval:
                            self.logger.info(
                                f"Skipping '{kw.keyword}': interval {kw.custom_interval}m not passed (elapsed: {elapsed:.1f}m)"
                            )
                            continue

                try:
                    total_new += await self.search_keyword(kw)
                except Exception as e:
                    self.logger.error(f"Error processing keyword '{kw.keyword}': {e}")

                # Pause between keywords (interruptible on stop)
                await self._sleep_or_stop(2)

            # Evaluate platform health once per cycle (only if attempted).
            for platform in list(self.scrapers.keys()):
                attempts = (self._cycle_platform_attempts or {}).get(platform, 0)
                if attempts <= 0:
                    continue
                raw_total = (self._cycle_platform_raw_counts or {}).get(platform, 0)
                if raw_total == 0:
                    self._empty_result_counter[platform] = self._empty_result_counter.get(platform, 0) + 1
                    if self._empty_result_counter[platform] == 3:
                        self.logger.warning(
                            f"{platform}: 3 cycles with 0 raw results - scraper may be blocked/broken"
                        )
                        if self.on_error:
                            self.on_error(f"{platform} scraper may be blocked/broken (3 cycles 0 raw results)")
                else:
                    self._empty_result_counter[platform] = 0

        finally:
            self._cycle_platform_raw_counts = None
            self._cycle_platform_attempts = None

        # After processing all platforms
        if total_new == 0 and not self.is_first_run:
            self._update_status("검색 결과가 없습니다. 키워드/필터를 확인해주세요.")

        # Reset first run flag after first cycle
        if self.is_first_run:
            self.is_first_run = False
            self.logger.info(
                f"Initial crawl complete. Found {total_new} items (notifications skipped for initial run)"
            )
            self._update_status(f"초기 스크래핑 완료: 새 상품 {total_new}개 (초기 알림 스킵)")

        return total_new

    async def start(self):
        """Start the monitoring loop."""
        if self.running:
            return

        # Ensure executor exists (may be shut down after a previous stop/close).
        if self._executor is None:
            self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        self.running = True
        self._resources_closed = False
        self._stop_event = asyncio.Event()
        self._start_task = asyncio.current_task()

        self.logger.info("Starting monitor engine...")

        try:
            await self.initialize_scrapers()
            self.initialize_notifiers()

            if not self.scrapers:
                self.logger.error("No scrapers initialized, cannot start monitoring")
                if self.on_error:
                    self.on_error("No scrapers initialized")
                return

            # Send startup notification (best-effort)
            for notifier in self.notifiers:
                try:
                    await notifier.send_message("Used Market Notifier started")
                except Exception:
                    pass

            self._update_status("모니터링 시작")

            error_count = 0
            max_errors = 5

            while self.running:
                try:
                    if not self._ensure_driver():
                        self.logger.warning("Driver not available, attempting to reinitialize scrapers...")
                        try:
                            await self.initialize_scrapers()
                        except Exception as e:
                            self.logger.error(f"Failed to reinitialize scrapers: {e}")
                            error_count += 1
                            if error_count >= max_errors:
                                if self.on_error:
                                    self.on_error("Too many errors, stopping monitoring")
                                break
                            await self._sleep_or_stop(30)
                            continue

                    self._update_status("검색 사이클 시작...")
                    new_items = await self.run_cycle()
                    error_count = 0

                    interval = self.settings.settings.check_interval_seconds
                    self._update_status(f"다음 검색까지 {interval}초 대기중... (새 상품 {new_items}개)")
                    await self._sleep_or_stop(interval)

                except asyncio.CancelledError:
                    self.logger.info("Monitor loop cancelled")
                    break
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"Error in monitoring loop (attempt {error_count}): {e}")
                    if self.on_error:
                        self.on_error(str(e))
                    if error_count >= max_errors:
                        if self.on_error:
                            self.on_error("Too many consecutive errors, stopping")
                        break
                    await self._sleep_or_stop(min(30 * error_count, 120))

        finally:
            self.running = False
            try:
                self._update_status("모니터링 중지")
            except Exception:
                pass
            try:
                await self._cleanup_resources()
            except Exception:
                pass
            self._start_task = None
            self._stop_event = None

    async def stop(self):
        """Stop the monitoring loop gracefully (idempotent)."""
        self.running = False
        if self._stop_event is not None:
            try:
                self._stop_event.set()
            except Exception:
                pass

        # If start() is still running in this loop, wait for it to exit (or cancel).
        try:
            loop = asyncio.get_running_loop()
        except Exception:
            loop = None

        t = self._start_task
        if t is not None and loop is not None:
            try:
                if t.get_loop() is loop and asyncio.current_task() is not t and not t.done():
                    try:
                        await asyncio.wait_for(t, timeout=15.0)
                    except asyncio.TimeoutError:
                        t.cancel()
                        try:
                            await asyncio.wait_for(t, timeout=5.0)
                        except Exception:
                            pass
            except Exception:
                pass

        await self._cleanup_resources()

    async def _cleanup_resources(self) -> None:
        """Idempotent resource teardown (driver + executor)."""
        if self._resources_closed:
            return
        self._resources_closed = True

        # Close scrapers (they share the driver)
        try:
            self.scrapers.clear()
        except Exception:
            pass

        drv = self._driver
        self._driver = None
        if drv is not None:
            try:
                ex = self._executor
                if ex is not None:
                    loop = asyncio.get_running_loop()
                    await asyncio.wait_for(loop.run_in_executor(ex, drv.quit), timeout=10.0)
                else:
                    drv.quit()
            except Exception as e:
                self.logger.warning(f"Driver close failed: {e}")

        ex = self._executor
        self._executor = None
        if ex is not None:
            try:
                ex.shutdown(wait=True, cancel_futures=True)
            except Exception as e:
                self.logger.warning(f"Executor shutdown failed: {e}")

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
        if self._close_called:
            return
        self._close_called = True

        try:
            await self.stop()
        finally:
            if self._owns_db:
                try:
                    self.db.close()
                except Exception:
                    pass
