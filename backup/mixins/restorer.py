from typing import TYPE_CHECKING
# pyright: reportAttributeAccessIssue=false
"""Backup restore with manifest/basename allowlist validation."""

import os
import shutil
import sqlite3
import zipfile


if TYPE_CHECKING:
    from backup.manager import BackupManager
    _HostBase_RestorerMixin = BackupManager
else:
    _HostBase_RestorerMixin = object

def _sqlite_copy(src_path: str, dst_path: str) -> None:
    """SQLite online backup API로 src 내용을 dst에 복사합니다.

    대상 DB가 다른 연결에서 WAL 모드로 열려 있어도 일관되게 적용됩니다.
    파일을 직접 덮어쓰면 남은 -wal 프레임이 재생되어 DB가 손상될 수 있습니다.
    """
    src = sqlite3.connect(src_path)
    try:
        dst = sqlite3.connect(dst_path, timeout=30)
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()


def _verify_sqlite_file(path: str) -> None:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()
        if not result or str(result[0]).lower() != "ok":
            raise ValueError(f"Backup database failed integrity check: {result}")
    finally:
        conn.close()


def _remove_sqlite_file(path: str) -> None:
    for suffix in ("", "-wal", "-shm", "-journal"):
        try:
            os.remove(path + suffix)
        except FileNotFoundError:
            pass


def _replace_file_atomic(src: str, dst: str) -> None:
    tmp = f"{dst}.restore_tmp"
    shutil.copy2(src, tmp)
    os.replace(tmp, dst)


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

                    # Validate everything before touching current data.
                    temp_db = temp_dir / os.path.basename(db_path)
                    if temp_db.exists():
                        _verify_sqlite_file(str(temp_db))

                    # Restore database (consistent snapshot of current data first)
                    if temp_db.exists():
                        if os.path.exists(db_path):
                            pre_restore = f"{db_path}.pre_restore"
                            _remove_sqlite_file(pre_restore)
                            _sqlite_copy(db_path, pre_restore)
                        _sqlite_copy(str(temp_db), db_path)
                        self.logger.info(f"Restored database: {db_path}")

                    # Restore settings
                    temp_settings = temp_dir / os.path.basename(settings_path)
                    if temp_settings.exists():
                        if os.path.exists(settings_path):
                            shutil.copy2(settings_path, f"{settings_path}.pre_restore")
                        _replace_file_atomic(str(temp_settings), settings_path)
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
