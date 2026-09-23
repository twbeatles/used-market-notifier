"""릴리즈 매니페스트 파싱, 서명 검증, 버전 비교."""

from __future__ import annotations

import base64
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from updater.constants import UPDATE_PUBLIC_KEY_B64_DEFAULT
from updater.manifest import (
    NoUpdateAvailableError,
    ReleaseManifest,
    canonical_manifest_payload,
    download_release_manifest,
    is_newer_version,
    verify_release_manifest,
)
from version import __version__

ROOT = Path(__file__).resolve().parent.parent


def _keypair():
    private_key = Ed25519PrivateKey.generate()
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return private_key, base64.b64encode(public_bytes).decode("ascii")


def _signed(private_key, payload: dict) -> dict:
    signature = base64.b64encode(private_key.sign(canonical_manifest_payload(payload))).decode("ascii")
    return {"payload": payload, "signature": signature}


class TestUpdateManifest(unittest.TestCase):
    def test_is_newer_version(self):
        self.assertTrue(is_newer_version("1.0.1", "1.0.0"))
        self.assertTrue(is_newer_version("1.1.0", "1.0.9"))
        self.assertTrue(is_newer_version("2.0.0", "1.99.99"))
        self.assertTrue(is_newer_version("1.0.0.1", "1.0.0"))
        self.assertFalse(is_newer_version("1.0.0", "1.0.0"))
        self.assertFalse(is_newer_version("0.9.9", "1.0.0"))

    def test_canonical_manifest_payload(self):
        self.assertEqual(canonical_manifest_payload({"b": 2, "a": 1}), b'{"a":1,"b":2}')

    def test_verify_release_manifest_success(self):
        private_key, public_b64 = _keypair()
        future = (datetime.now(timezone.utc) + timedelta(days=30)).replace(microsecond=0)
        payload = {
            "version": "1.1.0",
            "artifact_url": "https://github.com/twbeatles/used-market-notifier/releases/download/v1.1.0/UsedMarketNotifier-v1.1.0.exe",
            "sha256": "a" * 64,
            "size": 1024 * 1024 * 10,
            "expires_at": future.isoformat().replace("+00:00", "Z"),
        }
        manifest = verify_release_manifest(
            _signed(private_key, payload),
            public_key=public_b64,
            current_version="1.0.0",
        )
        self.assertIsInstance(manifest, ReleaseManifest)
        self.assertEqual(manifest.version, "1.1.0")
        self.assertEqual(manifest.artifact_sha256, "a" * 64)
        self.assertEqual(manifest.artifact_size, 1024 * 1024 * 10)

    def test_verify_release_manifest_invalid_signature(self):
        _private_key, public_b64 = _keypair()
        other_key = Ed25519PrivateKey.generate()
        future = (datetime.now(timezone.utc) + timedelta(days=30)).replace(microsecond=0)
        payload = {
            "version": "1.1.0",
            "artifact_url": "https://github.com/twbeatles/used-market-notifier/releases/download/v1.1.0/app.exe",
            "sha256": "a" * 64,
            "size": 1000,
            "expires_at": future.isoformat().replace("+00:00", "Z"),
        }
        with self.assertRaisesRegex(ValueError, "signature verification failed"):
            verify_release_manifest(
                _signed(other_key, payload),
                public_key=public_b64,
                current_version="1.0.0",
            )

    def test_verify_release_manifest_not_newer_version(self):
        private_key, public_b64 = _keypair()
        future = (datetime.now(timezone.utc) + timedelta(days=30)).replace(microsecond=0)
        payload = {
            "version": "1.0.0",
            "artifact_url": "https://github.com/twbeatles/used-market-notifier/releases/download/v1.0.0/app.exe",
            "sha256": "a" * 64,
            "size": 1000,
            "expires_at": future.isoformat().replace("+00:00", "Z"),
        }
        with self.assertRaises(NoUpdateAvailableError):
            verify_release_manifest(
                _signed(private_key, payload),
                public_key=public_b64,
                current_version="1.0.0",
            )

    def test_verify_release_manifest_expired(self):
        private_key, public_b64 = _keypair()
        past = (datetime.now(timezone.utc) - timedelta(days=1)).replace(microsecond=0)
        payload = {
            "version": "1.1.0",
            "artifact_url": "https://github.com/twbeatles/used-market-notifier/releases/download/v1.1.0/app.exe",
            "sha256": "a" * 64,
            "size": 1000,
            "expires_at": past.isoformat().replace("+00:00", "Z"),
        }
        with self.assertRaisesRegex(ValueError, "expired"):
            verify_release_manifest(
                _signed(private_key, payload),
                public_key=public_b64,
                current_version="1.0.0",
            )

    def test_verify_release_manifest_non_https_rejected(self):
        private_key, public_b64 = _keypair()
        future = (datetime.now(timezone.utc) + timedelta(days=30)).replace(microsecond=0)
        payload = {
            "version": "1.1.0",
            "artifact_url": "http://insecure.example.com/app.exe",
            "sha256": "a" * 64,
            "size": 1000,
            "expires_at": future.isoformat().replace("+00:00", "Z"),
        }
        with self.assertRaisesRegex(ValueError, "must be HTTPS"):
            verify_release_manifest(
                _signed(private_key, payload),
                public_key=public_b64,
                current_version="1.0.0",
            )

    def test_download_release_manifest_cache_busting(self):
        captured = []

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def geturl(self):
                return "https://example.com/latest.json"

            def read(self, limit):
                return b'{"payload": {}}'

        def fake_urlopen(request, timeout):
            captured.append(request)
            return FakeResponse()

        with patch("updater.manifest.urlopen", side_effect=fake_urlopen):
            result = download_release_manifest("https://example.com/latest.json")
        self.assertEqual(result, b'{"payload": {}}')
        self.assertEqual(len(captured), 1)
        request = captured[0]
        self.assertIn("_t=", request.full_url)
        cache_control = request.headers.get("Cache-control") or request.headers.get("Cache-Control")
        self.assertEqual(cache_control, "no-cache")
        self.assertEqual(request.headers.get("Pragma"), "no-cache")

    def test_download_release_manifest_rejects_non_https(self):
        with self.assertRaisesRegex(ValueError, "must be HTTPS"):
            download_release_manifest("http://example.com/latest.json")

    def test_committed_manifest_matches_embedded_key(self):
        document = (ROOT / "updates" / "latest.json").read_text(encoding="utf-8")
        json.loads(document)
        with self.assertRaises(NoUpdateAvailableError):
            verify_release_manifest(
                document,
                public_key=UPDATE_PUBLIC_KEY_B64_DEFAULT,
                current_version=__version__,
            )


if __name__ == "__main__":
    unittest.main()
