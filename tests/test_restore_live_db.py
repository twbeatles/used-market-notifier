"""Regression: restoring a backup while the app keeps its WAL connection open (ISSUE-001)."""

import os
import sqlite3
import tempfile
import unittest

from backup_manager import BackupManager
from db import DatabaseManager
from models import Item


def _item(i: int) -> Item:
    return Item(
        platform="bunjang",
        article_id=str(i),
        title=f"아이폰 {i}번 매물 테스트",
        price="10,000원",
        link=f"https://m.bunjang.co.kr/products/{i}",
        keyword="아이폰",
    )


def _count(path: str) -> tuple[str, int]:
    conn = sqlite3.connect(path)
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        return integrity, conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
    finally:
        conn.close()


class RestoreWithLiveConnectionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "listings.db")
        self.settings_path = os.path.join(self.tmp.name, "settings.json")
        with open(self.settings_path, "w", encoding="utf-8") as f:
            f.write('{"check_interval_seconds": 300}')
        self.manager = BackupManager(os.path.join(self.tmp.name, "backup"))

    def tearDown(self):
        self.tmp.cleanup()

    def _prepare(self, before: int, after: int) -> tuple[DatabaseManager, str]:
        live = DatabaseManager(self.db_path)
        for i in range(1, before + 1):
            live.add_listing(_item(i))
        backup = self.manager.create_backup(self.db_path, self.settings_path)
        self.assertIsNotNone(backup)
        for i in range(before + 1, before + after + 1):
            live.add_listing(_item(i))
        return live, str(backup)

    def test_restore_over_large_wal_keeps_database_valid(self):
        live, backup = self._prepare(50, 300)
        self.assertTrue(self.manager.restore_backup(backup, self.db_path, self.settings_path))
        live.close()
        self.assertEqual(_count(self.db_path), ("ok", 50))

    def test_restore_is_not_undone_by_small_wal(self):
        live, backup = self._prepare(200, 1)
        self.assertTrue(self.manager.restore_backup(backup, self.db_path, self.settings_path))
        live.add_listing(_item(9999))  # the live connection must see restored content
        live.close()
        self.assertEqual(_count(self.db_path), ("ok", 201))

    def test_pre_restore_snapshot_includes_wal_rows(self):
        live, backup = self._prepare(10, 25)
        self.assertTrue(self.manager.restore_backup(backup, self.db_path, self.settings_path))
        live.close()
        self.assertEqual(_count(self.db_path + ".pre_restore"), ("ok", 35))

    def test_corrupt_backup_database_leaves_current_data_untouched(self):
        live, backup = self._prepare(5, 5)
        broken = os.path.join(self.tmp.name, "broken.zip")
        import zipfile

        with zipfile.ZipFile(broken, "w") as zf:
            zf.writestr("listings.db", b"this is not a sqlite database" * 100)
        self.assertFalse(self.manager.restore_backup(broken, self.db_path, self.settings_path))
        live.close()
        self.assertEqual(_count(self.db_path), ("ok", 10))


if __name__ == "__main__":
    unittest.main()
