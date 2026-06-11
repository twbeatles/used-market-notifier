# pyright: reportAttributeAccessIssue=false
"""MetadataEnrichmentMixin for MonitorEngine."""

from .common import *


class MetadataEnrichmentMixin:
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

    def _needs_metadata_enrichment(self, item: Item) -> bool:
        return not bool(getattr(item, "seller", None)) or not bool(getattr(item, "location", None))

    @staticmethod
    def _blocked_seller_applies_to_platform(blocked_platform: str | None, platform: str) -> bool:
        value = str(blocked_platform or "").strip().lower()
        return not value or value == platform

    def _item_is_blocked(self, item: Item, blocked_set: set[tuple[str, Optional[str]]]) -> bool:
        seller = str(getattr(item, "seller", "") or "").strip()
        platform = str(getattr(item, "platform", "") or "").strip().lower()
        if not seller or not blocked_set:
            return False
        for blocked_seller, blocked_platform in blocked_set:
            if blocked_seller != seller:
                continue
            if self._blocked_seller_applies_to_platform(blocked_platform, platform):
                return True
        return False

    def _needs_prefilter_metadata_enrichment(
        self,
        item: Item,
        keyword_config: SearchKeyword,
        blocked_set: set[tuple[str, Optional[str]]],
    ) -> bool:
        if not self._needs_metadata_enrichment(item):
            return False

        if keyword_config.location and not getattr(item, "location", None):
            return True

        if blocked_set and not getattr(item, "seller", None):
            platform = str(getattr(item, "platform", "") or "").strip().lower()
            return any(
                self._blocked_seller_applies_to_platform(blocked_platform, platform)
                for _, blocked_platform in blocked_set
            )

        return False

    async def _run_enrichment(self, scraper: ScraperProtocol, item: Item) -> Item:
        async_enrich = getattr(scraper, "enrich_item_async", None)
        if callable(async_enrich):
            result = async_enrich(item)
            if inspect.isawaitable(result):
                return cast(Item, await cast(Awaitable[object], result))
        if self._executor is None:
            return scraper.enrich_item(item)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, scraper.enrich_item, item)

    async def enrich_item_metadata(self, item: Item, platform: str | None = None) -> Item:
        """Best-effort metadata enrichment for seller/location fields."""
        target_platform = str(platform or getattr(item, "platform", "") or "").strip().lower()
        if not target_platform or not self._needs_metadata_enrichment(item):
            return item
        article_id = str(getattr(item, "article_id", "") or "").strip()
        cache_key = (target_platform, article_id)
        if article_id and cache_key in self._enrichment_cache:
            return self._enrichment_cache[cache_key]

        current = item
        for use_fallback in (False, True):
            if not self._needs_metadata_enrichment(current):
                break
            if not await self._ensure_scraper(target_platform, use_fallback=use_fallback):
                continue

            scraper_map = self.fallback_scrapers if use_fallback else self.primary_scrapers
            scraper_kind_map = self.fallback_scraper_kind if use_fallback else self.primary_scraper_kind
            scraper = scraper_map.get(target_platform)
            if scraper is None:
                continue

            try:
                enriched = await self._run_enrichment(scraper, current)
                if isinstance(enriched, Item):
                    current = enriched
            except Exception as e:
                self.logger.warning(
                    f"Metadata enrichment failed: platform={target_platform} "
                    f"engine={scraper_kind_map.get(target_platform, 'unknown')} error={e}"
                )

        if article_id:
            self._enrichment_cache[cache_key] = current
        return current

    async def _enrich_items_with_budget(
        self,
        platform: str,
        keyword: str,
        items: list[Item],
        budget: int,
        *,
        phase: str,
        predicate: Callable[[Item], bool],
        force: bool = False,
    ) -> tuple[list[Item], int]:
        if (
            budget <= 0
            or not items
            or (
                not force
                and not getattr(self.settings.settings, "metadata_enrichment_enabled", False)
            )
        ):
            return items, 0

        enriched_items: list[Item] = []
        attempted = 0
        for item in items:
            if attempted >= budget or not predicate(item):
                enriched_items.append(item)
                continue

            attempted += 1
            try:
                enriched = await self.enrich_item_metadata(item, platform=platform)
                if (
                    getattr(enriched, "seller", None) != getattr(item, "seller", None)
                    or getattr(enriched, "location", None) != getattr(item, "location", None)
                    or getattr(enriched, "sale_status", None) != getattr(item, "sale_status", None)
                ):
                    self.logger.info(
                        f"Metadata enriched: phase={phase} platform={platform} keyword='{keyword}' "
                        f"article_id={getattr(item, 'article_id', '')}"
                    )
                enriched_items.append(enriched)
            except Exception as e:
                self.logger.warning(
                    f"Metadata enrichment warning: phase={phase} platform={platform} keyword='{keyword}' "
                    f"article_id={getattr(item, 'article_id', '')} error={e}"
                )
                enriched_items.append(item)

        return enriched_items, attempted

    def enrich_item_metadata_once(self, item: Item, platform: str | None = None) -> Item:
        """Synchronous one-shot enrichment for UI actions."""
        target_platform = str(platform or getattr(item, "platform", "") or "").strip().lower()
        if not target_platform or not self._needs_metadata_enrichment(item):
            return item

        current = item
        headless = self.settings.settings.headless_mode
        for kind in self._get_engine_order():
            if not self._needs_metadata_enrichment(current):
                break
            if kind == "playwright":
                try:
                    self._probe_playwright_runtime_sync()
                except Exception as e:
                    self.logger.warning(f"Skipping Playwright enrichment for {target_platform}: {e}")
                    continue

            try:
                scraper = self._create_scraper(target_platform, headless, kind)
            except Exception as e:
                self.logger.warning(f"Failed to create enrichment scraper {target_platform}/{kind}: {e}")
                continue

            try:
                enriched = scraper.enrich_item(current)
                if isinstance(enriched, Item):
                    current = enriched
            except Exception as e:
                self.logger.warning(f"One-shot metadata enrichment failed {target_platform}/{kind}: {e}")
            finally:
                self._close_scraper_safe(target_platform, scraper)

        return current
