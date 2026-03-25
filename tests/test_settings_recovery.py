import json
import os
import tempfile
import unittest
import zipfile

from settings_manager import SettingsManager


class TestSettingsRecovery(unittest.TestCase):
    def test_recovers_from_latest_valid_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = os.path.join(tmp, "settings.json")
            backup_dir = os.path.join(tmp, "backup")
            os.makedirs(backup_dir, exist_ok=True)

            with open(settings_path, "w", encoding="utf-8") as f:
                f.write("{invalid json")

            valid_settings = {
                "headless_mode": False,
                "metadata_enrichment_enabled": True,
                "notifiers": [],
                "keywords": [],
            }
            backup_path = os.path.join(backup_dir, "backup_20260325_120000.zip")
            with zipfile.ZipFile(backup_path, "w") as zf:
                zf.writestr("settings.json", json.dumps(valid_settings))

            manager = SettingsManager(settings_path=settings_path)

            self.assertFalse(manager.settings.headless_mode)
            self.assertTrue(manager.settings.metadata_enrichment_enabled)
            self.assertTrue(manager.load_recovery_state["recovered_from_backup"])
            self.assertFalse(manager.load_recovery_state["used_default"])
            self.assertEqual(manager.load_recovery_state["recovered_backup_path"], backup_path)
            broken_candidates = [name for name in os.listdir(tmp) if name.startswith("settings.broken-")]
            self.assertEqual(len(broken_candidates), 1)

    def test_uses_defaults_when_no_valid_backup_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = os.path.join(tmp, "settings.json")
            with open(settings_path, "w", encoding="utf-8") as f:
                f.write("{invalid json")

            manager = SettingsManager(settings_path=settings_path)

            self.assertTrue(manager.load_recovery_state["used_default"])
            self.assertFalse(manager.load_recovery_state["recovered_from_backup"])
            broken_candidates = [name for name in os.listdir(tmp) if name.startswith("settings.broken-")]
            self.assertEqual(len(broken_candidates), 1)


if __name__ == "__main__":
    unittest.main()
