# monitor_engine.py
"""Core monitoring engine that orchestrates scraping and notifications."""

import asyncio
import concurrent.futures
import logging
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from typing import Callable, Optional

from auto_tagger import AutoTagger
from db import DatabaseManager
from models import NotificationType, SearchKeyword
from notifiers import DiscordNotifier, SlackNotifier, TelegramNotifier
from scrapers import BunjangScraper, DanggeunScraper, Item, JoonggonaraScraper
from settings_manager import SettingsManager


@dataclass
class NotificationJob:
    """Queued notification payload."""

    item: Item
    is_price_change: bool = False
    old_price: Optional[str] = None
    new_price: Optional[str] = None
    listing_id: Optional[int] = None
    attempts: int = 0
    enqueued_at: float = 0.0


class MonitorEngine:
    """
    Core engine for monitoring used marketplaces.
    Coordinates scrapers, database, and notifications.
    """

    SCRAPER_CONCURRENCY = 2
    NOTIFICATION_MAX_RETRIES = 3
    NOTIFICATION_DRAIN_TIMEOUT = 20.0

    def __init__(self, settings_manager: SettingsManager, db: Optional[DatabaseManager] = None):
        self.settings = settings_manager
        self.logger = logging.getLogger("MonitorEngine")
        self.db = db or DatabaseManager(self.settings.settings.db_path)
        self._owns_db = db is None

        self.scrapers: dict[str, object] = {}
        self.notifiers: list[object] = []
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

        # Notification queue worker
        self._notification_queue: Optional[asyncio.Queue] = None
        self._notification_worker_task: Optional[asyncio.Task] = None

        # Auto-tagger for automatic tag detection (optionally from settings.tag_rules)
        self.auto_tagger = self._create_auto_tagger_from_settings()

        # Consecutive empty result tracking per platform
        self._empty_result_counter: dict[str, int] = {}

        # Per-cycle aggregates (set by run_cycle)
        self._cycle_platform_raw_counts: Optional[dict[str, int]] = None
        self._cycle_platform_attempts: Optional[dict[str, int]] = None
        self._cycle_blocked_set: set[tuple[str, Optional[str]]] = set()

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

    def _create_scraper(self, platform: str, headless: bool):
        """Create a scraper instance for a platform."""
        if platform == "danggeun":
            return DanggeunScraper(headless=headless)
        if platform == "bunjang":
            return BunjangScraper(headless=headless)
        if platform == "joonggonara":
            if headless:
                self.logger.warning("중고나라: 헤드리스 모드에서 네이버 봇 탐지로 결과가 제한될 수 있습니다")
            return JoonggonaraScraper(headless=headless)
        raise ValueError(f"Unsupported platform: {platform}")

    def _close_scraper_safe(self, platform: str, scraper: object) -> None:
        """Best-effort scraper close."""
        try:
            if hasattr(scraper, "close"):
                scraper.close()
        except Exception as e:
            self.logger.warning(f"Failed to close scraper '{platform}': {e}")

    def _check_scraper_health(self, scraper: object) -> bool:
        """Best-effort scraper driver health check."""
        try:
            drv = getattr(scraper, "driver", None)
            if drv is None:
                return False
            _ = drv.current_url
            return True
        except Exception:
            return False

    async def initialize_scrapers(self, platforms: Optional[list[str]] = None):
        """Initialize scrapers, optionally only for target platforms."""
        headless = self.settings.settings.headless_mode
        targets = platforms or ["danggeun", "bunjang", "joonggonara"]
        self._update_status("스크래퍼 초기화 중...")

        if self._executor is None:
            raise RuntimeError("Executor is not initialized")

        loop = asyncio.get_running_loop()
        for platform in targets:
            old_scraper = self.scrapers.pop(platform, None)
            if old_scraper is not None:
                await loop.run_in_executor(self._executor, self._close_scraper_safe, platform, old_scraper)

            try:
                scraper = await loop.run_in_executor(self._executor, self._create_scraper, platform, headless)
                self.scrapers[platform] = scraper
                self.logger.info(f"{platform} scraper initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize {platform} scraper: {e}")

        active_count = len(self.scrapers)
        self.logger.info(f"Initialized {active_count} scraper(s): {list(self.scrapers.keys())}")
        self._update_status(f"스크래퍼 {active_count}개 초기화 완료")

    async def _ensure_scraper(self, platform: str) -> bool:
        """Ensure platform scraper exists and its driver is healthy."""
        scraper = self.scrapers.get(platform)
        if scraper is None:
            await self.initialize_scrapers([platform])
            scraper = self.scrapers.get(platform)
            if scraper is None:
                return False

        if self._executor is None:
            return False
        loop = asyncio.get_running_loop()
        healthy = await loop.run_in_executor(self._executor, self._check_scraper_health, scraper)
        if healthy:
            return True

        self.logger.warning(f"Scraper health check failed for {platform}; reinitializing")
        await self.initialize_scrapers([platform])
        return platform in self.scrapers

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
        """Initialize notification channels based on settings."""
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

    async def _start_notification_worker(self) -> None:
        """Ensure notification queue worker is running."""
        if self._notification_queue is None:
            self._notification_queue = asyncio.Queue()
        if self._notification_worker_task is None or self._notification_worker_task.done():
            self._notification_worker_task = asyncio.create_task(
                self._notification_worker(), name="notification-worker"
            )

    async def _notification_worker(self) -> None:
        """Background worker that drains notification queue with retry."""
        queue = self._notification_queue
        if queue is None:
            return

        while True:
            if self._stop_event is not None and self._stop_event.is_set() and queue.empty():
                break
            try:
                job: NotificationJob = await asyncio.wait_for(queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            try:
                queue_wait_ms = (perf_counter() - job.enqueued_at) * 1000 if job.enqueued_at else 0.0
                ok = await self._deliver_notification(job, queue_wait_ms=queue_wait_ms)
                if not ok and job.attempts < self.NOTIFICATION_MAX_RETRIES - 1:
                    retry = NotificationJob(
                        item=job.item,
                        is_price_change=job.is_price_change,
                        old_price=job.old_price,
                        new_price=job.new_price,
                        listing_id=job.listing_id,
                        attempts=job.attempts + 1,
                        enqueued_at=perf_counter(),
                    )
                    backoff = min(2 ** retry.attempts, 8)
                    self.logger.warning(
                        f"Notification retry scheduled attempt={retry.attempts + 1}/{self.NOTIFICATION_MAX_RETRIES}"
                    )
                    await self._sleep_or_stop(backoff)
                    await queue.put(retry)
            except Exception as e:
                self.logger.error(f"Notification worker error: {e}")
            finally:
                queue.task_done()

    async def _deliver_notification(self, job: NotificationJob, queue_wait_ms: float = 0.0) -> bool:
        """Send one notification job to all configured channels."""
        if not self.settings.settings.notifications_enabled:
            return True
        schedule = self.settings.settings.notification_schedule
        if not schedule.is_active_now():
            self.logger.info("Notification skipped - outside scheduled hours")
            return True
        if not self.notifiers:
            return True

        sent_count = 0
        for notifier in self.notifiers:
            try:
                if job.is_price_change:
                    success = await notifier.send_price_change(job.item, job.old_price, job.new_price)
                else:
                    success = await notifier.send_item(job.item, with_image=True)

                if success:
                    sent_count += 1
                    if job.listing_id:
                        noti_type = notifier.__class__.__name__.replace("Notifier", "").lower()
                        msg_preview = (
                            f"{'📉 Price change' if job.is_price_change else '🆕 New item'}: {job.item.title}"
                        )
                        self.db.log_notification(job.listing_id, noti_type, msg_preview)
            except Exception as e:
                self.logger.error(f"Notification error: {e}")

        self.logger.info(
            f"[perf] notification queue_wait_ms={queue_wait_ms:.1f} "
            f"targets={len(self.notifiers)} sent={sent_count}"
        )
        return sent_count > 0

    async def send_notifications(
        self,
        item: Item,
        is_price_change: bool = False,
        old_price: str = None,
        new_price: str = None,
        listing_id: int = None,
    ):
        """Queue notifications so the search loop is never blocked by network I/O."""
        if not self.settings.settings.notifications_enabled:
            return
        if self._notification_queue is None:
            # Fallback (worker not ready yet): deliver inline.
            await self._deliver_notification(
                NotificationJob(
                    item=item,
                    is_price_change=is_price_change,
                    old_price=old_price,
                    new_price=new_price,
                    listing_id=listing_id,
                    enqueued_at=perf_counter(),
                )
            )
            return

        job = NotificationJob(
            item=item,
            is_price_change=is_price_change,
            old_price=old_price,
            new_price=new_price,
            listing_id=listing_id,
            enqueued_at=perf_counter(),
        )
        await self._notification_queue.put(job)
        qsize = self._notification_queue.qsize()
        if qsize >= 20:
            self.logger.warning(f"Notification queue backlog size={qsize}")

    async def search_keyword(self, keyword_config: SearchKeyword, blocked_set: Optional[set] = None) -> int:
        """Search a single keyword across enabled platforms and return new-item count."""
        search_start = perf_counter()
        new_count = 0
        blocked_set = blocked_set or set()

        platform_results: dict[str, list[Item]] = {}
        active_platforms: list[str] = []
        semaphore = asyncio.Semaphore(self.SCRAPER_CONCURRENCY)

        self._update_status(f"검색중: '{keyword_config.keyword}' ({', '.join(keyword_config.platforms)})")

        async def scrape_platform(platform: str):
            if self._cycle_platform_attempts is not None:
                self._cycle_platform_attempts[platform] = self._cycle_platform_attempts.get(platform, 0) + 1

            if not await self._ensure_scraper(platform):
                return platform, []

            scraper = self.scrapers.get(platform)
            if scraper is None:
                return platform, []

            async with semaphore:
                started = perf_counter()
                try:
                    loop = asyncio.get_running_loop()
                    items_raw = await loop.run_in_executor(
                        self._executor,
                        scraper.safe_search,
                        keyword_config.keyword,
                        keyword_config.location,
                    )
                except Exception as e:
                    self.logger.error(f"Error searching {platform}: {e}")
                    items_raw = []
                elapsed_ms = (perf_counter() - started) * 1000
                self.logger.info(
                    f"[perf] scrape keyword='{keyword_config.keyword}' platform={platform} "
                    f"items={len(items_raw)} elapsed_ms={elapsed_ms:.1f}"
                )
            return platform, items_raw

        scrape_tasks = []
        for platform in keyword_config.platforms:
            if platform not in ("danggeun", "bunjang", "joonggonara"):
                continue
            active_platforms.append(platform)
            scrape_tasks.append(scrape_platform(platform))

        if scrape_tasks:
            results = await asyncio.gather(*scrape_tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Unexpected scraping task failure: {result}")
                    continue
                platform, items_raw = result
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

            if blocked_set:
                items = [it for it in items if not it.seller or (it.seller, it.platform) not in blocked_set]

            self.logger.info(f"Found {len(items)} items on {platform} for '{keyword_config.keyword}'")
            process_start = perf_counter()
            platform_new = 0
            db_ms_total = 0.0

            existing_ids = self.db.get_existing_article_ids(
                platform, [str(it.article_id) for it in items if getattr(it, "article_id", None)]
            )

            for item in items:
                if not item.title or len(item.title.strip()) < 2:
                    continue

                # Skip fuzzy duplicate checks for known article IDs.
                if str(item.article_id) not in existing_ids and self.db.is_fuzzy_duplicate(item):
                    continue

                db_started = perf_counter()
                is_new, price_change, listing_id = self.db.add_listing(item)
                db_ms_total += (perf_counter() - db_started) * 1000

                if is_new:
                    platform_new += 1
                    self.logger.info(f"New item: {item.title}")

                    if self.settings.settings.auto_tagging_enabled and listing_id:
                        tags = self.auto_tagger.analyze(item.title)
                        if tags:
                            self.db.add_auto_tags(listing_id, tags)
                            self.logger.debug(f"Auto-tagged '{item.title}' with: {tags}")

                    if listing_id:
                        detected_status = self.db.detect_sale_status(item.title)
                        if detected_status != "for_sale":
                            self.db.update_sale_status(listing_id, detected_status)
                            self.logger.debug(f"Detected sale status '{detected_status}' for: {item.title}")

                    if self.on_new_item:
                        self.on_new_item(item)

                    if not self.is_first_run and getattr(keyword_config, "notify_enabled", True):
                        await self.send_notifications(item, listing_id=listing_id)

                elif price_change:
                    self.logger.info(
                        f"Price change: {item.title} ({price_change['old_price']} -> {price_change['new_price']})"
                    )
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

            self.db.record_search_stats(keyword_config.keyword, platform, len(items), platform_new)
            new_count += platform_new
            elapsed_ms = (perf_counter() - process_start) * 1000
            self.logger.info(
                f"[perf] process keyword='{keyword_config.keyword}' platform={platform} "
                f"items={len(items)} new={platform_new} db_ms={db_ms_total:.1f} elapsed_ms={elapsed_ms:.1f}"
            )

        total_ms = (perf_counter() - search_start) * 1000
        self.logger.info(f"[perf] keyword '{keyword_config.keyword}' total_elapsed_ms={total_ms:.1f}")
        return new_count

    async def run_cycle(self) -> int:
        """Run one complete monitoring cycle."""
        cycle_started = perf_counter()
        total_new = 0
        keywords = self.settings.settings.keywords

        self._cycle_platform_raw_counts = {p: 0 for p in ("danggeun", "bunjang", "joonggonara")}
        self._cycle_platform_attempts = {p: 0 for p in ("danggeun", "bunjang", "joonggonara")}
        blocked_sellers = self.db.get_blocked_sellers()
        self._cycle_blocked_set = {
            (row.get("seller_name"), row.get("platform")) for row in blocked_sellers if row.get("seller_name")
        }

        try:
            for kw in keywords:
                if not kw.enabled:
                    continue

                if kw.custom_interval:
                    last_time = self.db.get_last_search_time(kw.keyword)
                    if last_time:
                        elapsed = (datetime.now() - last_time).total_seconds() / 60
                        if elapsed < kw.custom_interval:
                            self.logger.info(
                                f"Skipping '{kw.keyword}': interval {kw.custom_interval}m not passed "
                                f"(elapsed: {elapsed:.1f}m)"
                            )
                            continue

                try:
                    total_new += await self.search_keyword(kw, blocked_set=self._cycle_blocked_set)
                except Exception as e:
                    self.logger.error(f"Error processing keyword '{kw.keyword}': {e}")

                await self._sleep_or_stop(2)

            for platform in ("danggeun", "bunjang", "joonggonara"):
                attempts = (self._cycle_platform_attempts or {}).get(platform, 0)
                if attempts <= 0:
                    continue
                raw_total = (self._cycle_platform_raw_counts or {}).get(platform, 0)
                if raw_total == 0:
                    self._empty_result_counter[platform] = self._empty_result_counter.get(platform, 0) + 1
                    if self._empty_result_counter[platform] == 3:
                        self.logger.warning(f"{platform}: 3 cycles with 0 raw results - scraper may be blocked/broken")
                        if self.on_error:
                            self.on_error(f"{platform} scraper may be blocked/broken (3 cycles 0 raw results)")
                        await self.initialize_scrapers([platform])
                else:
                    self._empty_result_counter[platform] = 0

        finally:
            self._cycle_platform_raw_counts = None
            self._cycle_platform_attempts = None
            self._cycle_blocked_set = set()

        if total_new == 0 and not self.is_first_run:
            self._update_status("검색 결과가 없습니다. 키워드/필터를 확인해주세요.")

        if self.is_first_run:
            self.is_first_run = False
            self.logger.info(
                f"Initial crawl complete. Found {total_new} items (notifications skipped for initial run)"
            )
            self._update_status(f"초기 스크래핑 완료: 새 상품 {total_new}개 (초기 알림 스킵)")

        cycle_ms = (perf_counter() - cycle_started) * 1000
        self.logger.info(f"[perf] cycle total_new={total_new} elapsed_ms={cycle_ms:.1f}")
        return total_new

    async def start(self):
        """Start the monitoring loop."""
        if self.running:
            return

        if self._executor is None:
            # Scraping runs in executor; keep >2 workers for search + cleanup + health checks.
            self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

        self.running = True
        self._resources_closed = False
        self._stop_event = asyncio.Event()
        self._start_task = asyncio.current_task()

        self.logger.info("Starting monitor engine...")

        try:
            await self.initialize_scrapers()
            self.initialize_notifiers()
            await self._start_notification_worker()

            if not self.scrapers:
                self.logger.error("No scrapers initialized, cannot start monitoring")
                if self.on_error:
                    self.on_error("No scrapers initialized")
                return

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
                    if not self.scrapers:
                        self.logger.warning("No active scrapers; attempting reinitialize...")
                        await self.initialize_scrapers()
                        if not self.scrapers:
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

    async def _drain_notification_queue(self) -> None:
        """Drain pending notifications, then stop worker."""
        queue = self._notification_queue
        worker = self._notification_worker_task
        if queue is not None:
            try:
                await asyncio.wait_for(queue.join(), timeout=self.NOTIFICATION_DRAIN_TIMEOUT)
            except asyncio.TimeoutError:
                self.logger.warning("Notification queue drain timed out; forcing shutdown")

        if worker is not None and not worker.done():
            worker.cancel()
            try:
                await worker
            except Exception:
                pass

        self._notification_worker_task = None
        self._notification_queue = None

    async def _cleanup_resources(self) -> None:
        """Idempotent resource teardown (scrapers + notification queue + executor)."""
        if self._resources_closed:
            return
        self._resources_closed = True

        try:
            await self._drain_notification_queue()
        except Exception as e:
            self.logger.warning(f"Notification queue cleanup failed: {e}")

        scrapers = list(self.scrapers.items())
        self.scrapers.clear()
        if scrapers and self._executor is not None:
            try:
                loop = asyncio.get_running_loop()
                close_tasks = [
                    loop.run_in_executor(self._executor, self._close_scraper_safe, platform, scraper)
                    for platform, scraper in scrapers
                ]
                if close_tasks:
                    await asyncio.wait_for(asyncio.gather(*close_tasks, return_exceptions=True), timeout=20.0)
            except Exception as e:
                self.logger.warning(f"Scraper close failed: {e}")

        ex = self._executor
        self._executor = None
        if ex is not None:
            try:
                ex.shutdown(wait=True, cancel_futures=True)
            except Exception as e:
                self.logger.warning(f"Executor shutdown failed: {e}")

    def _update_status(self, status: str):
        """Update status and notify callback."""
        self.logger.info(status)
        if self.on_status_update:
            self.on_status_update(status)

    def get_stats(self) -> dict:
        """Get current statistics."""
        snap = self.db.get_dashboard_snapshot(
            recent_limit=10,
            price_change_limit=50,
            price_change_days=7,
            daily_days=7,
        )
        return {
            "total_listings": snap["total"],
            "by_platform": snap["by_platform"],
            "by_keyword": self.db.get_listings_by_keyword(),
            "daily_stats": snap["daily_stats"],
            "recent_listings": snap["recent"],
            "price_changes": snap["price_changes"],
            "price_analysis": snap["analysis"],
        }

    async def close(self):
        """Clean up resources."""
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
