# pyright: reportAttributeAccessIssue=false
"""SearchFlowMixin for MonitorEngine."""

from .common import *


class SearchFlowMixin:
    @staticmethod
    def _dedupe_items(items: list[Item]) -> list[Item]:
        """
        Deduplicate merged scraper results.
        Priority key: (platform, article_id)
        Secondary key: URL/link
        """
        deduped: list[Item] = []
        seen_id_keys: set[tuple[str, str]] = set()
        seen_links: set[str] = set()

        for item in items or []:
            platform = str(getattr(item, "platform", "") or "")
            article_id = str(getattr(item, "article_id", "") or "").strip()
            link = str(getattr(item, "link", "") or "").strip()

            if platform and article_id:
                id_key = (platform, article_id)
                if id_key in seen_id_keys:
                    continue
            if link and link in seen_links:
                continue

            deduped.append(item)
            if platform and article_id:
                seen_id_keys.add((platform, article_id))
            if link:
                seen_links.add(link)

        return deduped

    def _fallback_budget_available(self, platform: str) -> bool:
        max_fallback = max(0, int(getattr(self.settings.settings, "max_fallback_per_cycle", 3) or 0))
        if max_fallback <= 0:
            return False
        if self._cycle_fallback_counts is None:
            return True
        return self._cycle_fallback_counts.get(platform, 0) < max_fallback

    def _increment_fallback_budget(self, platform: str) -> None:
        if self._cycle_fallback_counts is None:
            return
        self._cycle_fallback_counts[platform] = self._cycle_fallback_counts.get(platform, 0) + 1

    def _warn_danggeun_location_best_effort(self, keyword_config: SearchKeyword) -> None:
        location = str(getattr(keyword_config, "location", "") or "").strip()
        if not location or "danggeun" not in (keyword_config.platforms or []):
            return

        warning_key = (str(keyword_config.keyword or "").strip(), location)
        if warning_key in self._cycle_danggeun_location_warning_keys:
            return
        self._cycle_danggeun_location_warning_keys.add(warning_key)

        self.logger.warning(
            f"{self.DANGGEUN_LOCATION_WARNING}: keyword='{keyword_config.keyword}' location='{location}'"
        )
        if self.on_status_update:
            self.on_status_update(self.DANGGEUN_LOCATION_WARNING)

    async def search_keyword(self, keyword_config: SearchKeyword, blocked_set: Optional[set] = None) -> int:
        """Search a single keyword across enabled platforms and return new-item count."""
        search_start = perf_counter()
        new_count = 0
        blocked_set = blocked_set or set()

        platform_results: dict[str, list[Item]] = {}
        active_platforms: list[str] = []
        semaphore = asyncio.Semaphore(self.SCRAPER_CONCURRENCY)

        self._update_status(f"검색중: '{keyword_config.keyword}' ({', '.join(keyword_config.platforms)})")
        self._warn_danggeun_location_best_effort(keyword_config)

        async def scrape_platform(platform: str):
            if self._cycle_platform_attempts is not None:
                self._cycle_platform_attempts[platform] = self._cycle_platform_attempts.get(platform, 0) + 1

            if self._platform_is_backed_off(platform):
                return platform, [], 0, 0, False, "backoff"

            if not await self._ensure_scraper(platform, use_fallback=False):
                return platform, [], 0, 0, False, "primary_unavailable"

            primary_scraper = self.primary_scrapers.get(platform)
            primary_kind = self.primary_scraper_kind.get(platform, "unknown")
            fallback_scraper = self.fallback_scrapers.get(platform)
            fallback_kind = self.fallback_scraper_kind.get(platform, "none")

            if primary_scraper is None:
                return platform, [], 0, 0, False, "primary_unavailable"

            async def run_scrape(scraper: ScraperProtocol, engine_kind: str):
                started = perf_counter()
                try:
                    async with semaphore:
                        search_fn = getattr(scraper, "search", None)
                        if callable(search_fn) and inspect.iscoroutinefunction(search_fn):
                            items_raw = await search_fn(keyword_config.keyword, keyword_config.location)
                        else:
                            loop = asyncio.get_running_loop()
                            items_raw = await loop.run_in_executor(
                                self._executor,
                                scraper.safe_search,
                                keyword_config.keyword,
                                keyword_config.location,
                            )
                    error = None
                except Exception as e:
                    items_raw = []
                    kind = getattr(scraper, "get_last_failure_kind", lambda: None)() or "unknown"
                    error = f"{kind}: {e}"
                if error is None:
                    kind = getattr(scraper, "get_last_failure_kind", lambda: None)() or None
                    if kind in {"http_403", "http_429", "captcha_or_blocked"}:
                        error = kind
                    else:
                        quality_reason = self._quality_failure_reason(platform, items_raw)
                        if quality_reason:
                            error = quality_reason
                            items_raw = []
                elapsed_ms = (perf_counter() - started) * 1000
                self.logger.info(
                    f"[perf] scrape keyword='{keyword_config.keyword}' platform={platform} "
                    f"engine={engine_kind} items={len(items_raw)} elapsed_ms={elapsed_ms:.1f}"
                )
                return items_raw, error

            started_total = perf_counter()
            primary_items, primary_error = await run_scrape(primary_scraper, primary_kind)
            self._maybe_schedule_platform_backoff(platform, primary_error)

            fallback_used = False
            fallback_reason = ""
            fallback_items: list[Item] = []

            if primary_error:
                fallback_reason = "primary_malformed" if "parser_malformed" in primary_error else "primary_exception"
            elif (
                len(primary_items) == 0
                and bool(getattr(self.settings.settings, "fallback_on_empty_results", True))
            ):
                fallback_reason = "primary_empty"

            if fallback_reason:
                if fallback_scraper is None:
                    fallback_reason = f"{fallback_reason}_no_fallback"
                elif not self._fallback_budget_available(platform):
                    fallback_reason = f"{fallback_reason}_budget_exceeded"
                else:
                    ensured = await self._ensure_scraper(platform, use_fallback=True)
                    if ensured:
                        # Re-read fallback scraper in case ensure() reinitialized instances.
                        fallback_scraper = self.fallback_scrapers.get(platform)
                        fallback_kind = self.fallback_scraper_kind.get(platform, fallback_kind)
                        if fallback_scraper is None:
                            fallback_reason = f"{fallback_reason}_fallback_unavailable"
                        else:
                            fallback_used = True
                            self._increment_fallback_budget(platform)
                            fallback_items, fallback_error = await run_scrape(fallback_scraper, fallback_kind)
                            self._maybe_schedule_platform_backoff(platform, fallback_error)
                            if fallback_error:
                                self.logger.warning(
                                    f"Fallback scrape failed: platform={platform} "
                                    f"engine={fallback_kind} error={fallback_error}"
                                )
                    else:
                        fallback_reason = f"{fallback_reason}_fallback_unavailable"

            merged_items = self._dedupe_items([*primary_items, *fallback_items])
            total_elapsed_ms = (perf_counter() - started_total) * 1000
            self.logger.info(
                f"[scrape] platform={platform} primary_engine={primary_kind} primary_count={len(primary_items)} "
                f"fallback_used={fallback_used} fallback_engine={fallback_kind} fallback_count={len(fallback_items)} "
                f"fallback_reason={fallback_reason or '-'} merged_count={len(merged_items)} "
                f"elapsed_ms={total_elapsed_ms:.1f}"
            )
            return platform, merged_items, len(primary_items), len(fallback_items), fallback_used, fallback_reason

        scrape_tasks = []
        for platform in keyword_config.platforms:
            if platform not in ("danggeun", "bunjang", "joonggonara"):
                continue
            active_platforms.append(platform)
            scrape_tasks.append(scrape_platform(platform))

        if scrape_tasks:
            results = await asyncio.gather(*scrape_tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, BaseException):
                    self.logger.error(f"Unexpected scraping task failure: {result}")
                    continue
                platform, items_raw, _, _, _, _ = result
                if self._cycle_platform_raw_counts is not None:
                    self._cycle_platform_raw_counts[platform] = self._cycle_platform_raw_counts.get(platform, 0) + len(
                        items_raw
                    )
                platform_results[platform] = items_raw

        for platform in active_platforms:
            items_raw = platform_results.get(platform) or []
            raw_count = len(items_raw)
            metadata_enabled = bool(getattr(self.settings.settings, "metadata_enrichment_enabled", False))
            conditional_enabled = bool(
                getattr(self.settings.settings, "conditional_metadata_enrichment_enabled", True)
            )
            enrichment_budget = self.METADATA_ENRICHMENT_LIMIT if (metadata_enabled or conditional_enabled) else 0

            items_prefilter, used_prefilter = await self._enrich_items_with_budget(
                platform,
                keyword_config.keyword,
                items_raw,
                enrichment_budget,
                phase="prefilter",
                predicate=lambda item, kw=keyword_config, blocked=blocked_set: self._needs_prefilter_metadata_enrichment(
                    item,
                    kw,
                    blocked,
                ),
                force=conditional_enabled,
            )
            enrichment_budget = max(0, enrichment_budget - used_prefilter) if metadata_enabled else 0

            # Apply per-keyword filters (price/location/exclude keywords)
            items: list[Item] = []
            for it in items_prefilter:
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
                items = [it for it in items if not self._item_is_blocked(it, blocked_set)]

            items, _ = await self._enrich_items_with_budget(
                platform,
                keyword_config.keyword,
                items,
                enrichment_budget,
                phase="postfilter",
                predicate=self._needs_metadata_enrichment,
            )

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

                    if self.on_new_item:
                        self.on_new_item(item)

                    if not self.is_first_run and getattr(keyword_config, "notify_enabled", True):
                        await self.send_notifications(item, listing_id=listing_id)

                elif price_change:
                    self.logger.info(
                        f"Price change: {item.title} ({price_change['old_price']} -> {price_change['new_price']})"
                    )
                    fav = self.db.get_favorite_details(listing_id) if listing_id is not None else None
                    new_price_display = price_change["new_price"]

                    if fav and fav.get("target_price") and price_change.get("new_numeric"):
                        if price_change["new_numeric"] <= fav["target_price"]:
                            new_price_display += " (target hit)"
                            self.logger.info(f"Target price hit for {item.title}")

                    if self.on_price_change:
                        self.on_price_change(item, price_change["old_price"], price_change["new_price"])

                    if not self.is_first_run and getattr(keyword_config, "notify_enabled", True):
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
        self._cycle_fallback_counts = {p: 0 for p in ("danggeun", "bunjang", "joonggonara")}
        self._cycle_danggeun_location_warning_keys = set()
        self._enrichment_cache = {}
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
            self._cycle_fallback_counts = None
            self._cycle_blocked_set = set()
            self._cycle_danggeun_location_warning_keys = set()

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
