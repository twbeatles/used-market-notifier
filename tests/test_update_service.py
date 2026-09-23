"""UpdateService 확인, 스테이징, 개발 환경 교체 거부."""

from __future__ import annotations

import base64
import hashlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from updater.manifest import ReleaseManifest, canonical_manifest_payload
from updater.service import UpdateService


def _keypair():
    private_key = Ed25519PrivateKey.generate()
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return private_key, base64.b64encode(public_bytes).decode("ascii")


def _document(private_key, version: str) -> bytes:
    future = (datetime.now(timezone.utc) + timedelta(days=30)).replace(microsecond=0)
    payload = {
        "version": version,
        "artifact_url": "https://example.invalid/app.exe",
        "sha256": "f" * 64,
        "size": 5000,
        "expires_at": future.isoformat().replace("+00:00", "Z"),
    }
    signature = base64.b64encode(private_key.sign(canonical_manifest_payload(payload))).decode("ascii")
    return canonical_manifest_payload({"payload": payload, "signature": signature})


class TestUpdateService(unittest.TestCase):
    def test_check_for_update_found(self):
        private_key, public_b64 = _keypair()
        with tempfile.TemporaryDirectory() as tmp:
            service = UpdateService(current_version="1.0.0", public_key=public_b64, storage_root=tmp)
            with patch("updater.service.download_release_manifest", return_value=_document(private_key, "1.2.0")):
                manifest = service.check_for_update()
            self.assertIsNotNone(manifest)
            assert manifest is not None
            self.assertEqual(manifest.version, "1.2.0")

    def test_check_for_update_up_to_date(self):
        private_key, public_b64 = _keypair()
        with tempfile.TemporaryDirectory() as tmp:
            service = UpdateService(current_version="1.0.0", public_key=public_b64, storage_root=tmp)
            with patch("updater.service.download_release_manifest", return_value=_document(private_key, "1.0.0")):
                self.assertIsNone(service.check_for_update())

    def test_download_and_stage_streams_chunks_without_buffering(self):
        data = [b"first", b"second"]
        manifest = ReleaseManifest(
            version="1.1.0",
            artifact_url="https://example.invalid/app.exe",
            artifact_sha256=hashlib.sha256(b"".join(data)).hexdigest(),
            artifact_size=sum(map(len, data)),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            signature="dummy",
        )
        progress = []
        consumed = []

        def source(*_args, **_kwargs):
            for chunk in data:
                consumed.append(chunk)
                yield chunk

        def staging(_manifest, *, chunks, staging_root, **_kwargs):
            iterator = iter(chunks)
            self.assertEqual(consumed, [])
            self.assertEqual(next(iterator), b"first")
            self.assertEqual(consumed, [b"first"])
            self.assertEqual(next(iterator), b"second")
            path = Path(staging_root) / "staged.exe"
            path.write_bytes(b"".join(consumed))
            return path

        with tempfile.TemporaryDirectory() as tmp:
            service = UpdateService(storage_root=tmp)
            with patch("updater.service.stream_update_artifact", source), patch(
                "updater.service.prepare_staged_update",
                staging,
            ):
                staged = service.download_and_stage(
                    manifest,
                    progress_callback=lambda current, total: progress.append((current, total)),
                )
            self.assertEqual(staged.read_bytes(), b"firstsecond")
        self.assertEqual(progress, [(5, 11), (11, 11)])

    def test_launch_refuses_when_not_frozen(self):
        manifest = ReleaseManifest(
            version="1.1.0",
            artifact_url="https://example.invalid/app.exe",
            artifact_sha256="a" * 64,
            artifact_size=1,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            signature="dummy",
        )
        with tempfile.TemporaryDirectory() as tmp:
            staged = Path(tmp) / "staged.exe"
            staged.write_bytes(b"x")
            service = UpdateService(storage_root=tmp)
            with self.assertRaisesRegex(RuntimeError, "개발 환경"):
                service.launch_update_and_exit(staged, manifest)

    def test_launch_frozen_starts_helper_then_exits(self):
        manifest = ReleaseManifest(
            version="1.1.0",
            artifact_url="https://example.invalid/app.exe",
            artifact_sha256="ab" * 32,
            artifact_size=4,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            signature="dummy",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            staged = root / "staged.exe"
            staged.write_bytes(b"new!")
            service = UpdateService(current_version="1.0.0", storage_root=root)
            with patch.object(sys, "frozen", True, create=True), patch.object(
                sys, "executable", str(root / "UsedMarketNotifier.exe"), create=True
            ), patch("updater.service.launch_update_helper") as launch, patch(
                "updater.service.os._exit",
                side_effect=SystemExit,
            ) as exit_:
                with self.assertRaises(SystemExit):
                    service.launch_update_and_exit(staged, manifest)
            launch.assert_called_once()
            kwargs = launch.call_args.kwargs
            self.assertEqual(kwargs["expected_sha256"], manifest.artifact_sha256)
            self.assertEqual(kwargs["expected_size"], 4)
            self.assertTrue(str(kwargs["backup"]).endswith("UsedMarketNotifier.exe.v1.0.0.bak"))
            exit_.assert_called_once_with(0)


if __name__ == "__main__":
    unittest.main()
