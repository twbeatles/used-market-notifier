# settings_manager.py
"""JSON-based settings manager"""

import json
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional
from models import (
    AppSettings, SearchKeyword, NotifierConfig, 
    NotificationSchedule, NotificationType, ThemeMode, SellerFilter,
    KeywordPreset, TagRule, MessageTemplate
)

SETTINGS_FILE = "settings.json"


class SettingsManager:
    """Manages application settings with JSON persistence"""
    
    def __init__(self, settings_path: Optional[str] = None):
        self.settings_path = Path(settings_path or SETTINGS_FILE)
        self.load_recovery_state: dict[str, object] = {
            "used_default": False,
            "recovered_from_backup": False,
            "broken_settings_path": None,
            "recovered_backup_path": None,
            "error": None,
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
        except Exception as e:
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
        schedule_data = data.get('notification_schedule', {})
        schedule = NotificationSchedule(
            enabled=schedule_data.get('enabled', True),
            start_hour=schedule_data.get('start_hour', 0),
            end_hour=schedule_data.get('end_hour', 24),
            days=schedule_data.get('days', [0, 1, 2, 3, 4, 5, 6]),
        )
        
        notifiers = []
        for n in data.get('notifiers', []):
            try:
                notifiers.append(NotifierConfig(
                    type=NotificationType(n.get('type', 'telegram')),
                    enabled=n.get('enabled', False),
                    token=n.get('token', ''),
                    chat_id=n.get('chat_id', ''),
                    webhook_url=n.get('webhook_url', ''),
                ))
            except Exception:
                pass
        
        keywords = []
        for k in data.get('keywords', []):
            keywords.append(SearchKeyword(
                keyword=k.get('keyword', ''),
                min_price=k.get('min_price'),
                max_price=k.get('max_price'),
                location=k.get('location'),
                exclude_keywords=k.get('exclude_keywords', []),
                platforms=k.get('platforms', ['danggeun', 'bunjang', 'joonggonara']),
                enabled=k.get('enabled', True),
                group_name=k.get('group_name'),
                custom_interval=k.get('custom_interval'),
                target_price=k.get('target_price'),
                notify_enabled=k.get('notify_enabled', True),
            ))
        
        keyword_presets = []
        for p in data.get('keyword_presets', []):
            keyword_presets.append(KeywordPreset(
                name=p.get('name', ''),
                min_price=p.get('min_price'),
                max_price=p.get('max_price'),
                location=p.get('location'),
                exclude_keywords=p.get('exclude_keywords', []),
                platforms=p.get('platforms', ['danggeun', 'bunjang', 'joonggonara']),
            ))
            
        seller_filters = []
        for s in data.get('seller_filters', []):
            seller_filters.append(SellerFilter(
                seller_name=s.get('seller_name', ''),
                platform=s.get('platform', ''),
                is_blocked=s.get('is_blocked', True),
                notes=s.get('notes', ''),
            ))
        
        # Parse new settings for features #28, #29
        tag_rules = []
        for t in data.get('tag_rules', []):
            tag_rules.append(TagRule(
                tag_name=t.get('tag_name', ''),
                keywords=t.get('keywords', []),
                color=t.get('color', '#89b4fa'),
                icon=t.get('icon', '🏷️'),
                enabled=t.get('enabled', True),
            ))
        
        message_templates = []
        for m in data.get('message_templates', []):
            message_templates.append(MessageTemplate(
                name=m.get('name', ''),
                content=m.get('content', ''),
                platform=m.get('platform', 'all'),
            ))
        
        scraper_mode = data.get('scraper_mode', 'playwright_primary')
        if scraper_mode not in ('playwright_primary', 'selenium_primary', 'selenium_only'):
            scraper_mode = 'playwright_primary'

        return AppSettings(
            check_interval_seconds=data.get('check_interval_seconds', 300),
            headless_mode=data.get('headless_mode', True),
            db_path=data.get('db_path', 'listings.db'),
            minimize_to_tray=data.get('minimize_to_tray', True),
            start_minimized=data.get('start_minimized', False),
            auto_start_monitoring=data.get('auto_start_monitoring', False),
            theme_mode=ThemeMode(data.get('theme_mode', 'dark')),
            confirm_link_open=data.get('confirm_link_open', True),
            notifications_enabled=data.get('notifications_enabled', False),
            notification_schedule=schedule,
            notifiers=notifiers,
            keywords=keywords,
            keyword_presets=keyword_presets,
            seller_filters=seller_filters,
            # New settings
            auto_backup_enabled=data.get('auto_backup_enabled', True),
            auto_backup_interval_days=data.get('auto_backup_interval_days', 7),
            backup_keep_count=data.get('backup_keep_count', 5),
            auto_cleanup_enabled=data.get('auto_cleanup_enabled', False),
            cleanup_days=data.get('cleanup_days', 30),
            cleanup_exclude_favorites=data.get('cleanup_exclude_favorites', True),
            cleanup_exclude_noted=data.get('cleanup_exclude_noted', True),
            auto_tagging_enabled=data.get('auto_tagging_enabled', True),
            metadata_enrichment_enabled=data.get('metadata_enrichment_enabled', False),
            scraper_mode=scraper_mode,
            fallback_on_empty_results=data.get('fallback_on_empty_results', True),
            max_fallback_per_cycle=data.get('max_fallback_per_cycle', 3),
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
