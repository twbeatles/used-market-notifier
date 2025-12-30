# settings_manager.py
"""JSON-based settings manager"""

import json
import os
from pathlib import Path
from dataclasses import asdict
from typing import Optional
from models import (
    AppSettings, SearchKeyword, NotifierConfig, 
    NotificationSchedule, NotificationType
)

SETTINGS_FILE = "settings.json"


class SettingsManager:
    """Manages application settings with JSON persistence"""
    
    def __init__(self, settings_path: Optional[str] = None):
        self.settings_path = Path(settings_path or SETTINGS_FILE)
        self.settings = self.load()
    
    def load(self) -> AppSettings:
        """Load settings from JSON file"""
        if not self.settings_path.exists():
            return self._create_default()
        
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self._from_dict(data)
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self._create_default()
    
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
                }
                for k in settings.keywords
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
            notifiers.append(NotifierConfig(
                type=NotificationType(n.get('type', 'telegram')),
                enabled=n.get('enabled', False),
                token=n.get('token', ''),
                chat_id=n.get('chat_id', ''),
                webhook_url=n.get('webhook_url', ''),
            ))
        
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
            ))
        
        return AppSettings(
            check_interval_seconds=data.get('check_interval_seconds', 300),
            headless_mode=data.get('headless_mode', True),
            db_path=data.get('db_path', 'listings.db'),
            minimize_to_tray=data.get('minimize_to_tray', True),
            start_minimized=data.get('start_minimized', False),
            auto_start_monitoring=data.get('auto_start_monitoring', False),
            notification_schedule=schedule,
            notifiers=notifiers,
            keywords=keywords,
        )
    
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
