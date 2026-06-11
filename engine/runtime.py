# pyright: reportAttributeAccessIssue=false
"""RuntimeMixin for MonitorEngine."""

from .common import *


class RuntimeMixin:
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

        self.logger.info(f"Starting monitor engine... mode={self._get_scraper_mode()}")

        try:
            await self.initialize_scrapers()
            self.initialize_notifiers()
            await self._start_notification_worker()

            if not self.primary_scrapers:
                self.logger.error("No scrapers initialized, cannot start monitoring")
                if self.on_error:
                    self.on_error("No scrapers initialized")
                return

            await self._send_system_message("Used Market Notifier started")

            self._update_status("모니터링 시작")
            error_count = 0
            max_errors = 5

            while self.running:
                try:
                    if not self.primary_scrapers:
                        self.logger.warning("No active scrapers; attempting reinitialize...")
                        await self.initialize_scrapers()
                        if not self.primary_scrapers:
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
                self.logger.warning(
                    f"Notification queue drain timed out; forcing shutdown remaining_jobs={queue.qsize()}"
                )

        if worker is not None and not worker.done():
            worker.cancel()
            try:
                await cast(asyncio.Task[object], worker)
            except asyncio.CancelledError:
                pass
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

        close_targets: list[tuple[str, ScraperProtocol]] = []
        seen_obj_ids: set[int] = set()
        for platform, scraper in self.primary_scrapers.items():
            if scraper is None:
                continue
            oid = id(scraper)
            if oid in seen_obj_ids:
                continue
            seen_obj_ids.add(oid)
            close_targets.append((platform, scraper))
        for platform, scraper in self.fallback_scrapers.items():
            if scraper is None:
                continue
            oid = id(scraper)
            if oid in seen_obj_ids:
                continue
            seen_obj_ids.add(oid)
            close_targets.append((platform, scraper))

        self.primary_scrapers.clear()
        self.fallback_scrapers.clear()
        self.primary_scraper_kind.clear()
        self.fallback_scraper_kind.clear()

        scrapers = close_targets
        if scrapers:
            try:
                close_tasks = [self._close_scraper(platform, scraper) for platform, scraper in scrapers]
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
            "status_history": snap.get("status_history", []),
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
