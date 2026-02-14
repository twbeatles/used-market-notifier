import os
import sqlite3
import tempfile
import unittest
import zipfile

from backup_manager import BackupManager


class TestBackupManager(unittest.TestCase):
    def test_create_backup_contains_db_and_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            backup_dir = os.path.join(tmp, "backup")
            db_path = os.path.join(tmp, "listings.db")
            settings_path = os.path.join(tmp, "settings.json")

            # Create a tiny sqlite db
            conn = sqlite3.connect(db_path)
            try:
                conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
                conn.execute("INSERT INTO t (v) VALUES ('x')")
                conn.commit()
            finally:
                conn.close()

            # Create a settings file
            with open(settings_path, "w", encoding="utf-8") as f:
                f.write("{\"ok\": true}\n")

            mgr = BackupManager(backup_dir=backup_dir)
            backup_path = mgr.create_backup(db_path=db_path, settings_path=settings_path)
            self.assertIsNotNone(backup_path)
            self.assertTrue(os.path.exists(backup_path))

            with zipfile.ZipFile(backup_path, "r") as zf:
                names = set(zf.namelist())
                self.assertIn(os.path.basename(db_path), names)
                self.assertIn(os.path.basename(settings_path), names)


if __name__ == "__main__":
    unittest.main()

