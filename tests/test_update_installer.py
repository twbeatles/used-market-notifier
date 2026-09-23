"""스테이징, 교체, 스모크 실패 롤백, 백업 정리."""

from __future__ import annotations

import hashlib
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from updater.installer import (
    UpdateApplyError,
    UpdateCancelledError,
    apply_staged_update,
    cleanup_update_backups,
    consume_update_result,
    prepare_staged_update,
    write_update_result,
)
from updater.manifest import ReleaseManifest


def _manifest(**overrides) -> ReleaseManifest:
    data = {
        "version": "1.1.0",
        "artifact_url": "https://example.invalid/test.exe",
        "artifact_sha256": "",
        "artifact_size": 0,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=1),
        "signature": "dummy",
    }
    data.update(overrides)
    return ReleaseManifest(**data)


class TestUpdateInstaller(unittest.TestCase):
    def test_prepare_staged_update_success(self):
        data = b"hello update binary content"
        manifest = _manifest(
            artifact_sha256=hashlib.sha256(data).hexdigest(),
            artifact_size=len(data),
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            staged = prepare_staged_update(
                manifest,
                chunks=[data[:10], data[10:]],
                staging_root=root,
            )
            self.assertIsNotNone(staged)
            assert staged is not None
            self.assertTrue(staged.is_file())
            self.assertEqual(staged.read_bytes(), data)

    def test_prepare_staged_update_hash_mismatch(self):
        data = b"hello update binary content"
        manifest = _manifest(artifact_sha256="0" * 64, artifact_size=len(data))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                prepare_staged_update(manifest, chunks=[data], staging_root=root)
            self.assertEqual(list(root.glob("update-*.exe")), [])

    def test_apply_staged_update_success_and_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "app.exe"
            target.write_bytes(b"version 1.0.0")
            staged = root / "update.exe"
            staged.write_bytes(b"version 1.1.0")
            backup = root / "app.exe.v1.0.0.bak"
            apply_staged_update(
                target=target,
                staged=staged,
                backup=backup,
                smoke_runner=lambda _path: True,
            )
            self.assertEqual(target.read_bytes(), b"version 1.1.0")
            self.assertEqual(backup.read_bytes(), b"version 1.0.0")
            self.assertFalse(staged.exists())

    def test_apply_staged_update_smoke_fail_triggers_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "app.exe"
            target.write_bytes(b"good version 1.0.0")
            staged = root / "update.exe"
            staged.write_bytes(b"corrupted version 1.1.0")
            backup = root / "app.exe.v1.0.0.bak"
            with self.assertRaisesRegex(UpdateApplyError, "rolled back"):
                apply_staged_update(
                    target=target,
                    staged=staged,
                    backup=backup,
                    smoke_runner=lambda _path: False,
                )
            self.assertEqual(target.read_bytes(), b"good version 1.0.0")

    def test_cleanup_update_backups(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "app.exe"
            target.write_text("main", encoding="utf-8")
            for index in range(4):
                backup = root / f"app.exe.v1.0.{index}.bak"
                backup.write_text(f"bk{index}", encoding="utf-8")
            cleanup_update_backups(target, keep_count=2)
            self.assertLessEqual(len(list(root.glob("app.exe.v*.bak"))), 2)

    def test_write_and_consume_update_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            result_file = Path(tmp) / "last-update-result.json"
            self.assertIsNone(consume_update_result(result_file))
            write_update_result(result_file, {"status": "applied", "version": "1.1.0"})
            self.assertTrue(result_file.is_file())
            consumed = consume_update_result(result_file)
            self.assertIsNotNone(consumed)
            assert consumed is not None
            self.assertEqual(consumed["status"], "applied")
            self.assertEqual(consumed["version"], "1.1.0")
            self.assertFalse(result_file.exists())
            self.assertIsNone(consume_update_result(result_file))

    def test_prepare_staged_update_cancel_event(self):
        data = b"test cancellation content"
        manifest = _manifest(
            artifact_sha256=hashlib.sha256(data).hexdigest(),
            artifact_size=len(data),
        )
        cancel_event = threading.Event()
        cancel_event.set()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(UpdateCancelledError, "취소"):
                prepare_staged_update(
                    manifest,
                    chunks=[data],
                    staging_root=Path(tmp),
                    cancel_event=cancel_event,
                )


if __name__ == "__main__":
    unittest.main()
