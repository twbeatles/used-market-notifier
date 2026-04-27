# settings_manager.py
"""JSON-based settings manager"""

import json
import logging
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from models import (
    AppSettings, SearchKeyword, NotifierConfig, 
    NotificationSchedule, NotificationType, ThemeMode, SellerFilter,
    KeywordPreset, TagRule, MessageTemplate
)

SETTINGS_FILE = "settings.json"


class SettingsManager:
    """Manages application settings with JSON persistence"""

    VALID_PLATFORMS = ("danggeun", "bunjang", "joonggonara")
    VALID_SCRAPER_MODES = ("playwright_primary", "selenium_primary", "selenium_only")
    
    def __init__(self, settings_path: Optional[str] = None):
        self.settings_path = Path(settings_path or SETTINGS_FILE)
        self.logger = logging.getLogger("SettingsManager")
        self.load_recovery_state: dict[str, object] = {
            "used_default": False,
            "recovered_from_backup": False,
            "broken_settings_path": None,
            "recovered_backup_path": None,
            "error": None,
            "normalized_fields": [],
        }
        self.last_recovered_backup: Optional[str] = None
        self.settings = self.load()

    def _reset_load_recovery_state(self) -> None:
        self.load_recovery_state = {
            "used_default": False,
            "recovered_from_backup": False,
            "broken_settings_path": None,
            "recovered_backup_path": None,
            "error": None,
            "normalized_fields": [],
        }
        self.last_recovered_backup = None
    
    def load(self) -> AppSettings:
        """Load settings from JSON file"""
        if not self.settings_path.exists():
            self._reset_load_recovery_state()
            return self._create_default()
        
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._reset_load_recovery_state()
            return self._from_dict(data)
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
            print(f"Error loading settings: {e}")
            return self._recover_from_broken_settings(e)
    
    def save(self) -> bool:
        """Save settings to JSON file"""
        try:
            data = self._to_dict(self.settings)
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def _create_default(self) -> AppSettings:
        """Create default settings"""
        settings = AppSettings(
            notifiers=[
                NotifierConfig(type=NotificationType.TELEGRAM, enabled=True),
                NotifierConfig(type=NotificationType.DISCORD, enabled=False),
                NotifierConfig(type=NotificationType.SLACK, enabled=False),
            ],
            keywords=[
                SearchKeyword(keyword="맥북 에어 M2"),
                SearchKeyword(keyword="아이폰 15 프로"),
            ]
        )
        return settings

    def _mark_normalized(self, field: str, raw_value: Any, default_value: Any) -> None:
        normalized = self.load_recovery_state.setdefault("normalized_fields", [])
        if isinstance(normalized, list):
            normalized.append(field)
        self.logger.warning(
            "Invalid settings field normalized: %s=%r -> %r",
            field,
            raw_value,
            default_value,
        )

    def _as_bool(self, data: dict, key: str, default: bool) -> bool:
        raw = data.get(key, default)
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, str):
            lowered = raw.strip().lower()
            if lowered in ("true", "1", "yes", "y", "on"):
                self._mark_normalized(key, raw, True)
                return True
            if lowered in ("false", "0", "no", "n", "off"):
                self._mark_normalized(key, raw, False)
                return False
        self._mark_normalized(key, raw, default)
        return default

    def _as_int(self, data: dict, key: str, default: int, *, min_value: int, max_value: int | None = None) -> int:
        raw = data.get(key, default)
        try:
            value = int(raw)
        except Exception:
            self._mark_normalized(key, raw, default)
            return default
        if value < min_value or (max_value is not None and value > max_value):
            self._mark_normalized(key, raw, default)
            return default
        if raw != value:
            self._mark_normalized(key, raw, value)
        return value

    def _as_optional_int(self, value: Any, field: str) -> int | None:
        if value in (None, ""):
            return None
        try:
            parsed = int(value)
        except Exception:
            self._mark_normalized(field, value, None)
            return None
        if parsed < 0:
            self._mark_normalized(field, value, None)
            return None
        return parsed

    def _as_str_list(self, value: Any, field: str) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            self._mark_normalized(field, value, [value])
            return [value]
        if not isinstance(value, list):
            self._mark_normalized(field, value, [])
            return []
        result = [str(item).strip() for item in value if str(item).strip()]
        if len(result) != len(value):
            self._mark_normalized(field, value, result)
        return result

    def _as_platforms(self, value: Any, field: str) -> list[str]:
        raw_values = self._as_str_list(value, field)
        result = [platform for platform in raw_values if platform in self.VALID_PLATFORMS]
        if not result:
            result = [str(platform) for platform in self.VALID_PLATFORMS]
            if value != result:
                self._mark_normalized(field, value, result)
        elif result != raw_values:
            self._mark_normalized(field, value, result)
        return result

    def _as_theme(self, value: Any) -> ThemeMode:
        try:
            return ThemeMode(str(value or ThemeMode.DARK.value))
        except Exception:
            self._mark_normalized("theme_mode", value, ThemeMode.DARK.value)
            return ThemeMode.DARK

    def _as_scraper_mode(self, value: Any) -> str:
        mode = str(value or "playwright_primary").strip().lower()
        if mode not in self.VALID_SCRAPER_MODES:
            self._mark_normalized("scraper_mode", value, "playwright_primary")
            return "playwright_primary"
        return mode

    def _normalize_schedule(self, data: Any) -> NotificationSchedule:
        schedule_data = data if isinstance(data, dict) else {}
        if not isinstance(data, dict):
            self._mark_normalized("notification_schedule", data, {})
        days_raw = schedule_data.get("days", [0, 1, 2, 3, 4, 5, 6])
        days: list[int] = []
        if isinstance(days_raw, list):
            for day in days_raw:
                try:
                    parsed = int(day)
                except Exception:
                    continue
                if 0 <= parsed <= 6 and parsed not in days:
                    days.append(parsed)
        if not days:
            days = [0, 1, 2, 3, 4, 5, 6]
            self._mark_normalized("notification_schedule.days", days_raw, days)
        return NotificationSchedule(
            enabled=self._as_bool(schedule_data, "enabled", True),
            start_hour=self._as_int(schedule_data, "start_hour", 0, min_value=0, max_value=23),
            end_hour=self._as_int(schedule_data, "end_hour", 24, min_value=0, max_value=24),
            days=days,
        )
    
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
            scraper_mode=scraper_mode,
            fallback_on_empty_results=self._as_bool(data, 'fallback_on_empty_results', True),
            max_fallback_per_cycle=self._as_int(data, 'max_fallback_per_cycle', 3, min_value=0, max_value=50),
            tag_rules=tag_rules,
            message_templates=message_templates,
        )

    def _recover_from_broken_settings(self, error: Exception) -> AppSettings:
        """Quarantine a broken settings file and restore from backup when possible."""
        broken_path: Optional[Path] = None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            broken_path = self.settings_path.with_name(
                f"{self.settings_path.stem}.broken-{timestamp}{self.settings_path.suffix}"
            )
            shutil.move(str(self.settings_path), str(broken_path))
        except Exception:
            broken_path = None

        self.load_recovery_state = {
            "used_default": False,
            "recovered_from_backup": False,
            "broken_settings_path": str(broken_path) if broken_path else None,
            "recovered_backup_path": None,
            "error": str(error),
            "normalized_fields": [],
        }

        recovered = self._restore_settings_from_backup()
        if recovered is not None:
            self.load_recovery_state["recovered_from_backup"] = True
            self.load_recovery_state["recovered_backup_path"] = self.last_recovered_backup
            return recovered

        self.load_recovery_state["used_default"] = True
        return self._create_default()

    def _restore_settings_from_backup(self) -> Optional[AppSettings]:
        """Restore settings from the newest valid backup archive."""
        backup_dir = self.settings_path.parent / "backup"
        if not backup_dir.exists():
            return None

        settings_name = self.settings_path.name
        candidates = sorted(backup_dir.glob("backup_*.zip"), reverse=True)
        for archive_path in candidates:
            try:
                with zipfile.ZipFile(archive_path, "r") as zf:
                    if settings_name not in zf.namelist():
                        if SETTINGS_FILE not in zf.namelist():
                            continue
                        member_name = SETTINGS_FILE
                    else:
                        member_name = settings_name

                    raw = zf.read(member_name)
                    data = json.loads(raw.decode("utf-8"))
            except Exception:
                continue

            try:
                self.settings_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.settings_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.last_recovered_backup = str(archive_path)
                return self._from_dict(data)
            except Exception:
                continue

        return None
    
    # Convenience methods
    def add_keyword(self, keyword: SearchKeyword) -> None:
        self.settings.keywords.append(keyword)
        self.save()
    
    def remove_keyword(self, index: int) -> None:
        if 0 <= index < len(self.settings.keywords):
            self.settings.keywords.pop(index)
            self.save()
    
    def update_keyword(self, index: int, keyword: SearchKeyword) -> None:
        if 0 <= index < len(self.settings.keywords):
            self.settings.keywords[index] = keyword
            self.save()
    
    def get_telegram_config(self) -> Optional[NotifierConfig]:
        for n in self.settings.notifiers:
            if n.type == NotificationType.TELEGRAM:
                return n
        return None
    
    def get_discord_config(self) -> Optional[NotifierConfig]:
        for n in self.settings.notifiers:
            if n.type == NotificationType.DISCORD:
                return n
        return None
    
    def get_slack_config(self) -> Optional[NotifierConfig]:
        for n in self.settings.notifiers:
            if n.type == NotificationType.SLACK:
                return n
        return None
    
    # Preset methods
    def add_preset(self, preset: KeywordPreset) -> None:
        """Add a new keyword preset"""
        self.settings.keyword_presets.append(preset)
        self.save()
    
    def remove_preset(self, index: int) -> None:
        """Remove a preset by index"""
        if 0 <= index < len(self.settings.keyword_presets):
            self.settings.keyword_presets.pop(index)
            self.save()
    
    def get_presets(self) -> list[KeywordPreset]:
        """Get all presets"""
        return self.settings.keyword_presets
    
    def apply_preset(self, preset: KeywordPreset, keyword_text: str) -> SearchKeyword:
        """Create a SearchKeyword from preset with given keyword text"""
        return SearchKeyword(
            keyword=keyword_text,
            min_price=preset.min_price,
            max_price=preset.max_price,
            location=preset.location,
            exclude_keywords=preset.exclude_keywords.copy(),
            platforms=preset.platforms.copy(),
        )
