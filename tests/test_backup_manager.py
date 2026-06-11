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
            assert backup_path is not None
            self.assertTrue(os.path.exists(backup_path))

            with zipfile.ZipFile(backup_path, "r") as zf:
                names = set(zf.namelist())
                self.assertIn(os.path.basename(db_path), names)
                self.assertIn(os.path.basename(settings_path), names)
                self.assertIn("backup_manifest.json", names)

    def test_restore_rejects_path_traversal_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            backup_dir = os.path.join(tmp, "backup")
            os.makedirs(backup_dir, exist_ok=True)
            db_path = os.path.join(tmp, "listings.db")
            settings_path = os.path.join(tmp, "settings.json")
            outside_path = os.path.join(tmp, "outside.txt")

            mgr = BackupManager(backup_dir=backup_dir)
            for index, unsafe_name in enumerate(("../outside.txt", "C:/outside.txt", "nested/../../outside.txt")):
                with self.subTest(unsafe_name=unsafe_name):
                    backup_path = os.path.join(backup_dir, f"backup_malicious_{index}.zip")
                    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
                        zf.writestr("listings.db", b"not really sqlite")
                        zf.writestr("settings.json", "{}")
                        zf.writestr(unsafe_name, "bad")

                    self.assertFalse(mgr.restore_backup(backup_path, db_path=db_path, settings_path=settings_path))
                    self.assertFalse(os.path.exists(outside_path))
                    self.assertFalse(os.path.exists(db_path))
                    self.assertFalse(os.path.exists(settings_path))

    def test_restore_legacy_backup_without_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            backup_dir = os.path.join(tmp, "backup")
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, "backup_legacy.zip")
            db_path = os.path.join(tmp, "listings.db")
            settings_path = os.path.join(tmp, "settings.json")

            source_db = os.path.join(tmp, "source.db")
            conn = sqlite3.connect(source_db)
            try:
                conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
                conn.execute("INSERT INTO t (v) VALUES ('legacy')")
                conn.commit()
            finally:
                conn.close()

            with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(source_db, "listings.db")
                zf.writestr("settings.json", "{\"legacy\": true}\n")
                zf.writestr("backup_info.txt", "legacy")

            mgr = BackupManager(backup_dir=backup_dir)
            self.assertTrue(mgr.restore_backup(backup_path, db_path=db_path, settings_path=settings_path))
            self.assertTrue(os.path.exists(db_path))
            self.assertTrue(os.path.exists(settings_path))

            conn = sqlite3.connect(db_path)
            try:
                value = conn.execute("SELECT v FROM t").fetchone()[0]
            finally:
                conn.close()
            self.assertEqual(value, "legacy")


if __name__ == "__main__":
    unittest.main()
