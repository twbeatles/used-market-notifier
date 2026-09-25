from typing import TYPE_CHECKING
# pyright: reportAttributeAccessIssue=false
"""Backup restore with manifest/basename allowlist validation."""

import os
import shutil
import zipfile


if TYPE_CHECKING:
    from backup.manager import BackupManager
    _HostBase_RestorerMixin = BackupManager
else:
    _HostBase_RestorerMixin = object

class RestorerMixin(_HostBase_RestorerMixin):
    """Backup-restore behavior (needs ``backup_dir``/``logger``)."""

    def restore_backup(self, backup_file: str,
                       db_path: str = "listings.db",
                       settings_path: str = "settings.json") -> bool:
        """
        Restore database and settings from backup.

        Args:
            backup_file: Path to the backup zip file
            db_path: Where to restore the database
            settings_path: Where to restore settings

        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(backup_file):
                self.logger.error(f"Backup file not found: {backup_file}")
                return False

            with zipfile.ZipFile(backup_file, 'r') as zf:
                # Extract to temp directory first
                temp_dir = self.backup_dir / "temp_restore"
                shutil.rmtree(temp_dir, ignore_errors=True)
                temp_dir.mkdir(exist_ok=True)
                temp_root = temp_dir.resolve()
                allowed_names = {
                    os.path.basename(db_path),
                    os.path.basename(settings_path),
                    self.INFO_NAME,
                    self.MANIFEST_NAME,
                }

                try:
                    for member in zf.infolist():
                        basename = self._safe_member_basename(member.filename)
                        if basename is None or basename not in allowed_names:
                            raise ValueError(f"Unsafe or unsupported backup entry: {member.filename}")
                        target = (temp_dir / basename).resolve()
                        if not self._is_relative_to(target, temp_root):
                            raise ValueError(f"Unsafe backup entry target: {member.filename}")
                        if member.is_dir():
                            raise ValueError(f"Unexpected directory in backup: {member.filename}")
                        with zf.open(member, "r") as src, open(target, "wb") as dst:
                            shutil.copyfileobj(src, dst)

                    # Restore database
                    temp_db = temp_dir / os.path.basename(db_path)
                    if temp_db.exists():
                        # Create backup of current before overwriting
                        if os.path.exists(db_path):
                            shutil.copy2(db_path, f"{db_path}.pre_restore")
                        shutil.copy2(temp_db, db_path)
                        self.logger.info(f"Restored database: {db_path}")

                    # Restore settings
                    temp_settings = temp_dir / os.path.basename(settings_path)
                    if temp_settings.exists():
                        if os.path.exists(settings_path):
                            shutil.copy2(settings_path, f"{settings_path}.pre_restore")
                        shutil.copy2(temp_settings, settings_path)
                        self.logger.info(f"Restored settings: {settings_path}")

                finally:
                    # Cleanup temp directory
                    shutil.rmtree(temp_dir, ignore_errors=True)

            self.logger.info(f"Restore completed from: {backup_file}")
            return True

        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            return False


__all__ = ["RestorerMixin"]
