# pyright: reportAttributeAccessIssue=false
"""ScraperLifecycleMixin for MonitorEngine."""

from .common import *


class ScraperLifecycleMixin:
    def _get_scraper_mode(self) -> str:
        mode = str(getattr(self.settings.settings, "scraper_mode", "playwright_primary") or "").strip().lower()
        if mode not in ("playwright_primary", "selenium_primary", "selenium_only"):
            return "playwright_primary"
        return mode

    def _get_engine_order(self) -> list[str]:
        mode = self._get_scraper_mode()
        if mode == "selenium_only":
            return ["selenium"]
        if mode == "selenium_primary":
            return ["selenium", "playwright"]
        return ["playwright", "selenium"]

    @staticmethod
    def _probe_playwright_runtime_sync() -> bool:
        """Check Playwright package + chromium runtime availability."""
        from playwright.async_api import async_playwright

        async def _probe():
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                try:
                    page = await browser.new_page()
                    await page.goto("about:blank")
                    await page.close()
                finally:
                    await browser.close()

        asyncio.run(_probe())
        return True

    async def _ensure_playwright_runtime(self) -> bool:
        """Probe Playwright runtime once; cache result for this engine lifetime."""
        if self._playwright_runtime_checked:
            return self._playwright_runtime_available
        self._playwright_runtime_checked = True

        if self._executor is None:
            return False

        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(self._executor, self._probe_playwright_runtime_sync)
            self._playwright_runtime_available = True
        except Exception as e:
            self._playwright_runtime_available = False
            self.logger.warning(
                "Playwright runtime unavailable. Falling back to Selenium where possible. "
                f"reason={e} hint='python -m playwright install chromium'"
            )
        return self._playwright_runtime_available

    def _create_scraper(self, platform: str, headless: bool, engine_kind: str) -> ScraperProtocol:
        """Create a scraper instance for a platform and engine kind."""
        if platform not in ("danggeun", "bunjang", "joonggonara"):
            raise ValueError(f"Unsupported platform: {platform}")

        if engine_kind == "selenium":
            if platform == "danggeun":
                if DanggeunScraper is None:
                    raise ScraperDependencyUnavailable("Danggeun Selenium scraper unavailable")
                return DanggeunScraper(headless=headless)
            if platform == "bunjang":
                if BunjangScraper is None:
                    raise ScraperDependencyUnavailable("Bunjang Selenium scraper unavailable")
                return BunjangScraper(headless=headless)
            if platform == "joonggonara":
                if JoonggonaraScraper is None:
                    raise ScraperDependencyUnavailable("Joonggonara Selenium scraper unavailable")
                if headless:
                    self.logger.warning("중고나라: 헤드리스 모드에서 네이버 봇 탐지로 결과가 제한될 수 있습니다")
                return JoonggonaraScraper(headless=headless)

        if engine_kind == "playwright":
            if platform == "danggeun":
                if PlaywrightDanggeunScraper is None:
                    raise ScraperDependencyUnavailable("PlaywrightDanggeunScraper unavailable")
                return PlaywrightDanggeunScraper(headless=headless)
            if platform == "bunjang":
                if PlaywrightBunjangScraper is None:
                    raise ScraperDependencyUnavailable("PlaywrightBunjangScraper unavailable")
                return PlaywrightBunjangScraper(headless=headless)
            if platform == "joonggonara":
                if PlaywrightJoonggonaraScraper is None:
                    raise ScraperDependencyUnavailable("PlaywrightJoonggonaraScraper unavailable")
                return PlaywrightJoonggonaraScraper(headless=headless)

        raise ValueError(f"Unsupported scraper kind: platform={platform}, kind={engine_kind}")

    @staticmethod
    async def _await_awaitable(awaitable: Awaitable[object]) -> object:
        return await awaitable

    def _close_scraper_safe(self, platform: str, scraper: ScraperProtocol) -> None:
        """Best-effort scraper close."""
        try:
            close_fn = getattr(scraper, "close", None)
            if close_fn is None:
                return
            result = close_fn()
            if inspect.isawaitable(result):
                awaitable = cast(Awaitable[object], result)
                asyncio.run(self._await_awaitable(awaitable))
        except Exception as e:
            self.logger.warning(f"Failed to close scraper '{platform}': {e}")

    async def _close_scraper(self, platform: str, scraper: ScraperProtocol) -> None:
        """Close sync or async scraper resources."""
        close_fn = getattr(scraper, "close", None)
        if close_fn is None:
            return
        try:
            if self._executor is not None and not inspect.iscoroutinefunction(close_fn):
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(self._executor, close_fn)
                return
            result = close_fn()
            if inspect.isawaitable(result):
                await cast(Awaitable[object], result)
        except Exception as e:
            self.logger.warning(f"Failed to close scraper '{platform}': {e}")

    async def _start_scraper(self, platform: str, scraper: ScraperProtocol) -> None:
        start_fn = getattr(scraper, "start", None)
        if not callable(start_fn):
            return
        result = start_fn()
        if inspect.isawaitable(result):
            await cast(Awaitable[object], result)

    def _check_scraper_health(self, scraper: object) -> bool:
        """Best-effort scraper driver health check."""
        try:
            is_healthy_fn = getattr(scraper, "is_healthy", None)
            if callable(is_healthy_fn):
                return bool(is_healthy_fn())
            drv = getattr(scraper, "driver", None)
            if drv is None:
                return True
            _ = drv.current_url
            return True
        except Exception:
            return False

    def _platform_is_backed_off(self, platform: str) -> bool:
        until = self._platform_backoff_until.get(platform, 0.0)
        if until <= perf_counter():
            if until:
                self._platform_backoff_until.pop(platform, None)
            return False
        remaining = max(0.0, until - perf_counter())
        self.logger.warning(f"Skipping {platform} scrape due to temporary backoff ({remaining:.1f}s remaining)")
        return True

    def _maybe_schedule_platform_backoff(self, platform: str, reason: str | None) -> None:
        text = str(reason or "").lower()
        if not text:
            return
        if not any(token in text for token in ("http_403", "http_429", "captcha", "blocked", "too many requests")):
            return
        self._platform_backoff_until[platform] = perf_counter() + 300.0
        self.logger.warning(f"Scheduled temporary scrape backoff: platform={platform} reason={reason}")

    def _quality_failure_reason(self, platform: str, items: list[Item]) -> str | None:
        report = evaluate_scrape_quality(platform, items)
        if not report.get("malformed"):
            return None
        return (
            "parser_malformed: "
            f"total={report.get('total')} valid={report.get('valid_count')} "
            f"malformed={report.get('malformed_count')} reasons={report.get('reasons')}"
        )

    async def initialize_scrapers(self, platforms: Optional[list[str]] = None):
        """Initialize primary/fallback scrapers, optionally only for target platforms."""
        headless = self.settings.settings.headless_mode
        targets = platforms or ["danggeun", "bunjang", "joonggonara"]
        self._update_status("스크래퍼 초기화 중...")

        if self._executor is None:
            raise RuntimeError("Executor is not initialized")

        loop = asyncio.get_running_loop()
        engine_order = self._get_engine_order()
        for platform in targets:
            old_primary = self.primary_scrapers.pop(platform, None)
            old_fallback = self.fallback_scrapers.pop(platform, None)
            self.primary_scraper_kind.pop(platform, None)
            self.fallback_scraper_kind.pop(platform, None)
            if old_primary is not None:
                await self._close_scraper(platform, old_primary)
            if old_fallback is not None and old_fallback is not old_primary:
                await self._close_scraper(platform, old_fallback)

            resolved: list[tuple[str, ScraperProtocol]] = []
            for kind in engine_order:
                scraper: ScraperProtocol | None = None
                try:
                    scraper = await loop.run_in_executor(self._executor, self._create_scraper, platform, headless, kind)
                    assert scraper is not None
                    if kind == "playwright":
                        await self._start_scraper(platform, scraper)
                    resolved.append((kind, scraper))
                except ScraperDependencyUnavailable as e:
                    self.logger.info(f"Engine unavailable for {platform} ({kind}): {e}")
                except Exception as e:
                    try:
                        if scraper is not None:
                            await self._close_scraper(platform, scraper)
                    except Exception:
                        pass
                    self.logger.warning(f"Failed to initialize {platform} ({kind}): {e}")

            if not resolved:
                self.logger.error(f"No scraper initialized for {platform}")
                continue

            primary_kind, primary_scraper = resolved[0]
            self.primary_scrapers[platform] = primary_scraper
            self.primary_scraper_kind[platform] = primary_kind

            if len(resolved) > 1:
                fallback_kind, fallback_scraper = resolved[1]
                self.fallback_scrapers[platform] = fallback_scraper
                self.fallback_scraper_kind[platform] = fallback_kind

            self.logger.info(
                f"{platform} scraper initialized primary={self.primary_scraper_kind.get(platform)} "
                f"fallback={self.fallback_scraper_kind.get(platform)}"
            )

        active_count = len(self.primary_scrapers)
        self.logger.info(f"Initialized primary scraper(s)={active_count}: {list(self.primary_scrapers.keys())}")
        self._update_status(f"스크래퍼 {active_count}개 초기화 완료")

    async def _ensure_scraper(self, platform: str, use_fallback: bool = False) -> bool:
        """Ensure platform scraper exists and its health is acceptable."""
        scraper_map = self.fallback_scrapers if use_fallback else self.primary_scrapers
        scraper = scraper_map.get(platform)
        if scraper is None:
            await self.initialize_scrapers([platform])
            scraper = scraper_map.get(platform)
            if scraper is None:
                return False

        if self._executor is None:
            return False
        loop = asyncio.get_running_loop()
        healthy = await loop.run_in_executor(self._executor, self._check_scraper_health, scraper)
        if healthy:
            return True

        scraper_label = "fallback" if use_fallback else "primary"
        self.logger.warning(f"{scraper_label} scraper health check failed for {platform}; reinitializing")
        await self.initialize_scrapers([platform])
        return platform in scraper_map
