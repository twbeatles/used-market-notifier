"""Mixin module: serialization."""

from models import (
    AppSettings, SearchKeyword, NotifierConfig,
    NotificationSchedule, NotificationType, ThemeMode, SellerFilter,
    KeywordPreset, TagRule, MessageTemplate
)

class SettingsSerializationMixin:
    """Settings serialization behavior."""

    def _to_dict(self, settings: AppSettings) -> dict:
        """Convert AppSettings to dictionary"""
        data = {
            'check_interval_seconds': settings.check_interval_seconds,
            'headless_mode': settings.headless_mode,
            'db_path': settings.db_path,
            'minimize_to_tray': settings.minimize_to_tray,
            'start_minimized': settings.start_minimized,
            'auto_start_monitoring': settings.auto_start_monitoring,
            'theme_mode': settings.theme_mode.value,
            'confirm_link_open': settings.confirm_link_open,
            'notifications_enabled': settings.notifications_enabled,
            'notification_schedule': {
                'enabled': settings.notification_schedule.enabled,
                'start_hour': settings.notification_schedule.start_hour,
                'end_hour': settings.notification_schedule.end_hour,
                'days': settings.notification_schedule.days,
            },
            'notifiers': [
                {
                    'type': n.type.value,
                    'enabled': n.enabled,
                    'token': n.token,
                    'chat_id': n.chat_id,
                    'webhook_url': n.webhook_url,
                }
                for n in settings.notifiers
            ],
            'keywords': [
                {
                    'keyword': k.keyword,
                    'min_price': k.min_price,
                    'max_price': k.max_price,
                    'location': k.location,
                    'exclude_keywords': k.exclude_keywords,
                    'platforms': k.platforms,
                    'enabled': k.enabled,
                    'group_name': k.group_name,
                    'custom_interval': k.custom_interval,
                    'target_price': k.target_price,
                    'notify_enabled': k.notify_enabled,
                }
                for k in settings.keywords
            ],
            'keyword_presets': [
                {
                    'name': p.name,
                    'min_price': p.min_price,
                    'max_price': p.max_price,
                    'location': p.location,
                    'exclude_keywords': p.exclude_keywords,
                    'platforms': p.platforms,
                }
                for p in getattr(settings, 'keyword_presets', [])
            ],
            'seller_filters': [
                {
                    'seller_name': s.seller_name,
                    'platform': s.platform,
                    'is_blocked': s.is_blocked,
                    'notes': s.notes,
                }
                for s in settings.seller_filters
            ],
            # New settings for features #17, #18, #28, #29
            'auto_backup_enabled': settings.auto_backup_enabled,
            'auto_backup_interval_days': settings.auto_backup_interval_days,
            'backup_keep_count': settings.backup_keep_count,
            'auto_cleanup_enabled': settings.auto_cleanup_enabled,
            'cleanup_days': settings.cleanup_days,
            'cleanup_exclude_favorites': settings.cleanup_exclude_favorites,
            'cleanup_exclude_noted': settings.cleanup_exclude_noted,
            'auto_tagging_enabled': settings.auto_tagging_enabled,
            'metadata_enrichment_enabled': getattr(settings, 'metadata_enrichment_enabled', False),
            'conditional_metadata_enrichment_enabled': getattr(
                settings, 'conditional_metadata_enrichment_enabled', True
            ),
            'scraper_mode': getattr(settings, 'scraper_mode', 'playwright_primary'),
            'fallback_on_empty_results': getattr(settings, 'fallback_on_empty_results', True),
            'max_fallback_per_cycle': getattr(settings, 'max_fallback_per_cycle', 3),
            'tag_rules': [
                {
                    'tag_name': t.tag_name,
                    'keywords': t.keywords,
                    'color': t.color,
                    'icon': t.icon,
                    'enabled': t.enabled,
                }
                for t in settings.tag_rules
            ],
            'message_templates': [
                {
                    'name': m.name,
                    'content': m.content,
                    'platform': m.platform,
                }
                for m in settings.message_templates
            ]
        }
        return data

