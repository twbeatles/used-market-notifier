"""Database and settings backup/restore manager.

Canonical behaviors live in :mod:`backup.mixins` (creation, restore,
registry/retention) and in :mod:`backup.path_safety` /
:mod:`backup.size_format` (pure helpers). This module composes them into
``BackupManager`` while keeping the previous public surface intact.
"""

import logging
from pathlib import Path

from .mixins import CreatorMixin, RegistryMixin, RestorerMixin
from .path_safety import is_relative_to, safe_member_basename
from .size_format import format_size


class BackupManager(CreatorMixin, RestorerMixin, RegistryMixin):
    """Manages backup and restore of database and settings"""

    MANIFEST_NAME = "backup_manifest.json"
    INFO_NAME = "backup_info.txt"

    def __init__(self, backup_dir: str = "backup"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger("BackupManager")

    @staticmethod
    def _safe_member_basename(name: str) -> str | None:
        return safe_member_basename(name)

    @staticmethod
    def _is_relative_to(child: Path, parent: Path) -> bool:
        return is_relative_to(child, parent)

    def _format_size(self, size_bytes: int) -> str:
        """Format byte size to human readable string"""
        return format_size(size_bytes)
