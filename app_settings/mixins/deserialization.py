"""Mixin module: serialization."""

from models import (
    AppSettings, SearchKeyword, NotifierConfig,
    NotificationSchedule, NotificationType, ThemeMode, SellerFilter,
    KeywordPreset, TagRule, MessageTemplate
)

class SettingsDeserializationMixin:
    """Settings deserialization behavior."""

    def _from_dict(self, data: dict) -> AppSettings:
        """Convert dictionary to AppSettings"""
        if not isinstance(data, dict):
            self._mark_normalized("settings_root", data, {})
            data = {}

        schedule = self._normalize_schedule(data.get('notification_schedule', {}))

        notifiers = []
        raw_notifiers = data.get('notifiers', [])
        if not isinstance(raw_notifiers, list):
            self._mark_normalized("notifiers", raw_notifiers, [])
            raw_notifiers = []
        for n in raw_notifiers:
            try:
                if not isinstance(n, dict):
                    self._mark_normalized("notifiers[]", n, None)
                    continue
                raw_type = n.get('type', 'telegram')
                try:
                    notifier_type = NotificationType(raw_type)
                except Exception:
                    self._mark_normalized("notifiers[].type", raw_type, NotificationType.TELEGRAM.value)
                    notifier_type = NotificationType.TELEGRAM
                notifiers.append(NotifierConfig(
                    type=notifier_type,
                    enabled=bool(n.get('enabled', False)),
                    token=str(n.get('token', '') or ''),
                    chat_id=str(n.get('chat_id', '') or ''),
                    webhook_url=str(n.get('webhook_url', '') or ''),
                ))
            except Exception as e:
                self._mark_normalized("notifiers[]", n, f"skipped: {e}")

        keywords = []
        raw_keywords = data.get('keywords', [])
        if not isinstance(raw_keywords, list):
            self._mark_normalized("keywords", raw_keywords, [])
            raw_keywords = []
        for index, k in enumerate(raw_keywords):
            if not isinstance(k, dict):
                self._mark_normalized(f"keywords[{index}]", k, None)
                continue
            keywords.append(SearchKeyword(
                keyword=str(k.get('keyword', '') or ''),
                min_price=self._as_optional_int(k.get('min_price'), f"keywords[{index}].min_price"),
                max_price=self._as_optional_int(k.get('max_price'), f"keywords[{index}].max_price"),
                location=str(k.get('location')) if k.get('location') else None,
                exclude_keywords=self._as_str_list(k.get('exclude_keywords', []), f"keywords[{index}].exclude_keywords"),
                platforms=self._as_platforms(k.get('platforms', list(self.VALID_PLATFORMS)), f"keywords[{index}].platforms"),
                enabled=bool(k.get('enabled', True)),
                group_name=str(k.get('group_name')) if k.get('group_name') else None,
                custom_interval=self._as_optional_int(k.get('custom_interval'), f"keywords[{index}].custom_interval"),
                target_price=self._as_optional_int(k.get('target_price'), f"keywords[{index}].target_price"),
                notify_enabled=bool(k.get('notify_enabled', True)),
            ))

        keyword_presets = []
        raw_presets = data.get('keyword_presets', [])
        if not isinstance(raw_presets, list):
            self._mark_normalized("keyword_presets", raw_presets, [])
            raw_presets = []
        for index, p in enumerate(raw_presets):
            if not isinstance(p, dict):
                self._mark_normalized(f"keyword_presets[{index}]", p, None)
                continue
            keyword_presets.append(KeywordPreset(
                name=str(p.get('name', '') or ''),
                min_price=self._as_optional_int(p.get('min_price'), f"keyword_presets[{index}].min_price"),
                max_price=self._as_optional_int(p.get('max_price'), f"keyword_presets[{index}].max_price"),
                location=str(p.get('location')) if p.get('location') else None,
                exclude_keywords=self._as_str_list(p.get('exclude_keywords', []), f"keyword_presets[{index}].exclude_keywords"),
                platforms=self._as_platforms(p.get('platforms', list(self.VALID_PLATFORMS)), f"keyword_presets[{index}].platforms"),
            ))

        seller_filters = []
        raw_seller_filters = data.get('seller_filters', [])
        if not isinstance(raw_seller_filters, list):
            self._mark_normalized("seller_filters", raw_seller_filters, [])
            raw_seller_filters = []
        for index, s in enumerate(raw_seller_filters):
            if not isinstance(s, dict):
                self._mark_normalized(f"seller_filters[{index}]", s, None)
                continue
            seller_filters.append(SellerFilter(
                seller_name=str(s.get('seller_name', '') or ''),
                platform=str(s.get('platform', '') or ''),
                is_blocked=bool(s.get('is_blocked', True)),
                notes=str(s.get('notes', '') or ''),
            ))

        # Parse new settings for features #28, #29
        tag_rules = []
        raw_tag_rules = data.get('tag_rules', [])
        if not isinstance(raw_tag_rules, list):
            self._mark_normalized("tag_rules", raw_tag_rules, [])
            raw_tag_rules = []
        for index, t in enumerate(raw_tag_rules):
            if not isinstance(t, dict):
                self._mark_normalized(f"tag_rules[{index}]", t, None)
                continue
            tag_rules.append(TagRule(
                tag_name=str(t.get('tag_name', '') or ''),
                keywords=self._as_str_list(t.get('keywords', []), f"tag_rules[{index}].keywords"),
                color=str(t.get('color', '#89b4fa') or '#89b4fa'),
                icon=str(t.get('icon', '🏷️') or '🏷️'),
                enabled=bool(t.get('enabled', True)),
            ))

        message_templates = []
        raw_templates = data.get('message_templates', [])
        if not isinstance(raw_templates, list):
            self._mark_normalized("message_templates", raw_templates, [])
            raw_templates = []
        for index, m in enumerate(raw_templates):
            if not isinstance(m, dict):
                self._mark_normalized(f"message_templates[{index}]", m, None)
                continue
            message_templates.append(MessageTemplate(
                name=str(m.get('name', '') or ''),
                content=str(m.get('content', '') or ''),
                platform=str(m.get('platform', 'all') or 'all'),
            ))

        scraper_mode = self._as_scraper_mode(data.get('scraper_mode', 'playwright_primary'))

        return AppSettings(
            check_interval_seconds=self._as_int(data, 'check_interval_seconds', 300, min_value=30, max_value=86400),
            headless_mode=self._as_bool(data, 'headless_mode', True),
            db_path=str(data.get('db_path', 'listings.db') or 'listings.db'),
            minimize_to_tray=self._as_bool(data, 'minimize_to_tray', True),
            start_minimized=self._as_bool(data, 'start_minimized', False),
            auto_start_monitoring=self._as_bool(data, 'auto_start_monitoring', False),
            theme_mode=self._as_theme(data.get('theme_mode', 'dark')),
            confirm_link_open=self._as_bool(data, 'confirm_link_open', True),
            notifications_enabled=self._as_bool(data, 'notifications_enabled', False),
            notification_schedule=schedule,
            notifiers=notifiers,
            keywords=keywords,
            keyword_presets=keyword_presets,
            seller_filters=seller_filters,
            # New settings
            auto_backup_enabled=self._as_bool(data, 'auto_backup_enabled', True),
            auto_backup_interval_days=self._as_int(data, 'auto_backup_interval_days', 7, min_value=1, max_value=365),
            backup_keep_count=self._as_int(data, 'backup_keep_count', 5, min_value=1, max_value=100),
            auto_cleanup_enabled=self._as_bool(data, 'auto_cleanup_enabled', False),
            cleanup_days=self._as_int(data, 'cleanup_days', 30, min_value=1, max_value=3650),
            cleanup_exclude_favorites=self._as_bool(data, 'cleanup_exclude_favorites', True),
            cleanup_exclude_noted=self._as_bool(data, 'cleanup_exclude_noted', True),
            auto_tagging_enabled=self._as_bool(data, 'auto_tagging_enabled', True),
            metadata_enrichment_enabled=self._as_bool(data, 'metadata_enrichment_enabled', False),
            conditional_metadata_enrichment_enabled=self._as_bool(
                data, 'conditional_metadata_enrichment_enabled', True
            ),
            scraper_mode=scraper_mode,
            fallback_on_empty_results=self._as_bool(data, 'fallback_on_empty_results', True),
            max_fallback_per_cycle=self._as_int(data, 'max_fallback_per_cycle', 3, min_value=0, max_value=50),
            tag_rules=tag_rules,
            message_templates=message_templates,
        )

