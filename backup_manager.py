# backup_manager.py
"""Database and settings backup/restore manager"""

import os
import shutil
import zipfile
import logging
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional


class BackupManager:
    """Manages backup and restore of database and settings"""
    
    def __init__(self, backup_dir: str = "backup"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger("BackupManager")
    
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

                        zf.write(tmp_db_path, os.path.basename(db_path))
                        self.logger.info(f"Backed up database snapshot: {db_path}")
                    except Exception as e:
                        # Fallback: zip the raw file if snapshot fails.
                        self.logger.warning(f"DB snapshot backup failed, falling back to raw file: {e}")
                        zf.write(db_path, os.path.basename(db_path))
                        self.logger.info(f"Backed up database: {db_path}")
                    finally:
                        if tmp_db_path:
                            try:
                                os.remove(tmp_db_path)
                            except Exception:
                                pass
                
                # Backup settings
                if os.path.exists(settings_path):
                    zf.write(settings_path, os.path.basename(settings_path))
                    self.logger.info(f"Backed up settings: {settings_path}")
                
                # Create metadata
                metadata = f"Created: {datetime.now().isoformat()}\nDB: {db_path}\nSettings: {settings_path}"
                zf.writestr("backup_info.txt", metadata)
            
            self.logger.info(f"Backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return None
    
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
                temp_dir.mkdir(exist_ok=True)
                
                try:
                    zf.extractall(temp_dir)
                    
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
    
    def _format_size(self, size_bytes: int) -> str:
        """Format byte size to human readable string"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"


if __name__ == "__main__":
    # Test backup manager
    manager = BackupManager()
    
    # Create a test backup
    backup_path = manager.create_backup()
    print(f"Created backup: {backup_path}")
    
    # List backups
    backups = manager.list_backups()
    print(f"Available backups: {len(backups)}")
    for b in backups:
        print(f"  - {b['filename']} ({b['size_str']}) - {b['date']}")
