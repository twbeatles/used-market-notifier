import json
import os
import tempfile
import unittest
import zipfile
from typing import cast

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

    def test_partially_invalid_settings_are_normalized_without_quarantine(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = os.path.join(tmp, "settings.json")
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "theme_mode": "neon",
                        "check_interval_seconds": -5,
                        "max_fallback_per_cycle": "bad",
                        "notification_schedule": {"days": ["x"], "start_hour": 99},
                        "keywords": [{"keyword": "아이폰", "platforms": ["bad-platform"]}],
                    },
                    f,
                )

            manager = SettingsManager(settings_path=settings_path)

            self.assertFalse(manager.load_recovery_state["used_default"])
            self.assertFalse(manager.load_recovery_state["recovered_from_backup"])
            self.assertIsNone(manager.load_recovery_state["broken_settings_path"])
            self.assertEqual(manager.settings.theme_mode.value, "dark")
            self.assertEqual(manager.settings.check_interval_seconds, 300)
            self.assertEqual(manager.settings.max_fallback_per_cycle, 3)
            self.assertEqual(manager.settings.notification_schedule.days, [0, 1, 2, 3, 4, 5, 6])
            self.assertEqual(manager.settings.keywords[0].platforms, ["danggeun", "bunjang", "joonggonara"])
            normalized = cast(list[str], manager.load_recovery_state["normalized_fields"])
            self.assertIn("theme_mode", normalized)
            self.assertIn("check_interval_seconds", normalized)


if __name__ == "__main__":
    unittest.main()
