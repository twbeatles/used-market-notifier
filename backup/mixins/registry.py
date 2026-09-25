# pyright: reportAttributeAccessIssue=false
"""Backup registry: listing, age-based auto-backup, and retention cleanup."""

import os
from datetime import datetime
from typing import Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from backup.manager import BackupManager
    _HostBase_RegistryMixin = BackupManager
else:
    _HostBase_RegistryMixin = object

class RegistryMixin(_HostBase_RegistryMixin):
    """Backup inventory/retention behavior (needs ``backup_dir``/``logger``)."""

    def list_backups(self) -> list:
        """
        List all available backups.

        Returns:
            List of dicts with backup info (filename, date, size)
        """
        backups = []
        try:
            for file in sorted(self.backup_dir.glob("backup_*.zip"), reverse=True):
                stat = file.stat()
                backups.append({
                    'filename': file.name,
                    'path': str(file),
                    'date': datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    'size': stat.st_size,
                    'size_str': self._format_size(stat.st_size)
                })
        except Exception as e:
            self.logger.error(f"Failed to list backups: {e}")

        return backups

    def auto_backup_if_needed(self, max_age_days: int = 7,
                               db_path: str = "listings.db",
                               settings_path: str = "settings.json") -> Optional[str]:
        """
        Create backup if last backup is older than max_age_days.

        Returns:
            Path to new backup if created, None otherwise
        """
        backups = self.list_backups()

        if not backups:
            # No backups exist, create one
            return self.create_backup(db_path, settings_path)

        # Check age of most recent backup
        latest = backups[0]
        try:
            latest_date = datetime.strptime(latest['date'], "%Y-%m-%d %H:%M")
            age_days = (datetime.now() - latest_date).days

            if age_days >= max_age_days:
                self.logger.info(f"Last backup is {age_days} days old, creating new backup")
                return self.create_backup(db_path, settings_path)
            else:
                self.logger.debug(f"Recent backup exists ({age_days} days old)")
                return None

        except Exception as e:
            self.logger.error(f"Error checking backup age: {e}")
            return None

    def cleanup_old_backups(self, keep_count: int = 5):
        """
        Remove old backups, keeping only the most recent ones.

        Args:
            keep_count: Number of backups to keep
        """
        try:
            backups = self.list_backups()

            if len(backups) <= keep_count:
                return

            # Delete excess backups (oldest first)
            for backup in backups[keep_count:]:
                try:
                    os.remove(backup['path'])
                    self.logger.info(f"Deleted old backup: {backup['filename']}")
                except Exception as e:
                    self.logger.error(f"Failed to delete backup {backup['filename']}: {e}")

        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")


__all__ = ["RegistryMixin"]
