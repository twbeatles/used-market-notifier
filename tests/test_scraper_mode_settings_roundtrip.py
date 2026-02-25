import os
import tempfile
import unittest

from settings_manager import SettingsManager


class TestScraperModeSettingsRoundtrip(unittest.TestCase):
    def test_dual_engine_settings_save_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = os.path.join(tmp, "settings.json")
            sm = SettingsManager(settings_path=settings_path)

            sm.settings.scraper_mode = "selenium_primary"
            sm.settings.fallback_on_empty_results = False
            sm.settings.max_fallback_per_cycle = 7
            self.assertTrue(sm.save())

            sm2 = SettingsManager(settings_path=settings_path)
            self.assertEqual(sm2.settings.scraper_mode, "selenium_primary")
            self.assertFalse(sm2.settings.fallback_on_empty_results)
            self.assertEqual(sm2.settings.max_fallback_per_cycle, 7)

    def test_invalid_scraper_mode_falls_back_to_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = os.path.join(tmp, "settings.json")
            sm = SettingsManager(settings_path=settings_path)

            sm.settings.scraper_mode = "invalid_mode"
            self.assertTrue(sm.save())

            sm2 = SettingsManager(settings_path=settings_path)
            self.assertEqual(sm2.settings.scraper_mode, "playwright_primary")


if __name__ == "__main__":
    unittest.main()
