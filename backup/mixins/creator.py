# pyright: reportAttributeAccessIssue=false
"""Backup creation (consistent SQLite snapshot + settings + manifest)."""

import json
import os
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional


class CreatorMixin:
    """Backup-archive creation behavior (needs ``backup_dir``/``logger``)."""

    def create_backup(self, db_path: str = "listings.db",
                      settings_path: str = "settings.json") -> Optional[str]:
        """
        Create a backup of database and settings.

        Returns:
            Path to the backup file, or None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.zip"
            backup_path = self.backup_dir / backup_name

            db_basename = os.path.basename(db_path)
            settings_basename = os.path.basename(settings_path)
            files: list[str] = []
            created_at = datetime.now().isoformat()

            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Backup database
                if os.path.exists(db_path):
                    # Use SQLite backup API to get a consistent snapshot (safer with WAL/open connections).
                    tmp_db_path = None
                    try:
                        suffix = Path(db_path).suffix or ".db"
                        fd, tmp_db_path = tempfile.mkstemp(prefix="backup_snapshot_", suffix=suffix)
                        os.close(fd)

                        src = sqlite3.connect(db_path)
                        dst = sqlite3.connect(tmp_db_path)
                        try:
                            src.backup(dst)
                        finally:
                            try:
                                dst.close()
                            except Exception:
                                pass
                            try:
                                src.close()
                            except Exception:
                                pass

                        zf.write(tmp_db_path, db_basename)
                        files.append(db_basename)
                        self.logger.info(f"Backed up database snapshot: {db_path}")
                    except Exception as e:
                        # Fallback: zip the raw file if snapshot fails.
                        self.logger.warning(f"DB snapshot backup failed, falling back to raw file: {e}")
                        zf.write(db_path, db_basename)
                        files.append(db_basename)
                        self.logger.info(f"Backed up database: {db_path}")
                    finally:
                        if tmp_db_path:
                            try:
                                os.remove(tmp_db_path)
                            except Exception:
                                pass

                # Backup settings
                if os.path.exists(settings_path):
                    zf.write(settings_path, settings_basename)
                    files.append(settings_basename)
                    self.logger.info(f"Backed up settings: {settings_path}")

                # Create metadata
                metadata = f"Created: {created_at}\nDB: {db_path}\nSettings: {settings_path}"
                zf.writestr(self.INFO_NAME, metadata)
                files.append(self.INFO_NAME)
                manifest = {
                    "version": 1,
                    "created_at": created_at,
                    "files": [*files, self.MANIFEST_NAME],
                    "db_basename": db_basename,
                    "settings_basename": settings_basename,
                }
                zf.writestr(self.MANIFEST_NAME, json.dumps(manifest, ensure_ascii=False, indent=2))

            self.logger.info(f"Backup created: {backup_path}")
            return str(backup_path)

        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return None


__all__ = ["CreatorMixin"]
