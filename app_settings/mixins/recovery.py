"""Mixin module: recovery."""

import json
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
from ..constants import SETTINGS_FILE


class SettingsRecoveryMixin:
    """Recovery behavior."""

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
