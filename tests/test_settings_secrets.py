"""Regression: notifier secrets protected at rest, atomic settings save."""

import json
import os
import sys
import tempfile
import unittest
from unittest import mock

from app_settings import secrets
from models import NotificationType, NotifierConfig
from settings_manager import SettingsManager

TOKEN = "123456:ABC-secret-bot-token"
WEBHOOK = "https://discord.com/api/webhooks/1/secret"


class SettingsSecretsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "settings.json")

    def tearDown(self):
        self.tmp.cleanup()

    def _read(self) -> str:
        with open(self.path, encoding="utf-8") as f:
            return f.read()

    def _save_with_secrets(self) -> SettingsManager:
        manager = SettingsManager(settings_path=self.path)
        manager.settings.notifiers = [
            NotifierConfig(type=NotificationType.TELEGRAM, enabled=True, token=TOKEN, chat_id="42"),
            NotifierConfig(type=NotificationType.DISCORD, enabled=True, webhook_url=WEBHOOK),
        ]
        self.assertTrue(manager.save())
        return manager

    @unittest.skipUnless(sys.platform == "win32", "DPAPI is Windows-only")
    def test_secrets_are_encrypted_on_disk_and_round_trip(self):
        self._save_with_secrets()
        raw = self._read()
        self.assertNotIn(TOKEN, raw)
        self.assertNotIn(WEBHOOK, raw)
        self.assertIn(secrets.PREFIX, raw)
        self.assertIn('"chat_id": "42"', raw)  # not a secret

        reloaded = SettingsManager(settings_path=self.path)
        by_type = {n.type: n for n in reloaded.settings.notifiers}
        self.assertEqual(by_type[NotificationType.TELEGRAM].token, TOKEN)
        self.assertEqual(by_type[NotificationType.DISCORD].webhook_url, WEBHOOK)
        self.assertEqual(reloaded.load_recovery_state["secret_decrypt_failed"], [])

    def test_legacy_plaintext_settings_still_load(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"notifiers": [{"type": "telegram", "enabled": True, "token": TOKEN, "chat_id": "42"}]}, f)
        manager = SettingsManager(settings_path=self.path)
        self.assertEqual(manager.settings.notifiers[0].token, TOKEN)
        self.assertEqual(manager.load_recovery_state["secret_decrypt_failed"], [])

    def test_undecryptable_secret_is_cleared_and_reported(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "notifiers": [
                        {"type": "telegram", "enabled": True, "token": secrets.PREFIX + "bm90LXZhbGlk", "chat_id": "42"}
                    ]
                },
                f,
            )
        manager = SettingsManager(settings_path=self.path)
        self.assertEqual(manager.settings.notifiers[0].token, "")
        failures = manager.load_recovery_state["secret_decrypt_failed"]
        self.assertIsInstance(failures, list)
        self.assertEqual(len(failures), 1)  # pyright: ignore[reportArgumentType]
        self.assertFalse(manager.load_recovery_state["used_default"])  # rest of settings kept

    def test_encryption_failure_keeps_plaintext(self):
        with mock.patch.object(secrets, "dpapi_available", return_value=True), \
                mock.patch.object(secrets, "_dpapi", side_effect=OSError("no dpapi")):
            self.assertEqual(secrets.protect_secret(TOKEN), TOKEN)

    def test_save_is_atomic_when_serialization_fails(self):
        manager = self._save_with_secrets()
        before = self._read()
        with mock.patch("app_settings.json_io.json.dump", side_effect=RuntimeError("disk full")):
            self.assertFalse(manager.save())
        self.assertEqual(self._read(), before)
        leftovers = [n for n in os.listdir(self.tmp.name) if n.endswith(".tmp")]
        self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
