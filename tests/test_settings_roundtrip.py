import os
import tempfile
import unittest

from models import MessageTemplate
from settings_manager import SettingsManager


class TestSettingsRoundtrip(unittest.TestCase):
    def test_message_templates_save_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = os.path.join(tmp, "settings.json")
            sm = SettingsManager(settings_path=settings_path)

            sm.settings.message_templates = [
                MessageTemplate(name="기본", content="안녕하세요! {title} 문의드립니다.", platform="all"),
                MessageTemplate(name="당근전용", content="이웃입니다. {location}에서 직거래 가능할까요?", platform="danggeun"),
            ]
            sm.settings.conditional_metadata_enrichment_enabled = False

            self.assertTrue(sm.save())

            sm2 = SettingsManager(settings_path=settings_path)
            self.assertEqual(len(sm2.settings.message_templates), 2)
            self.assertEqual(sm2.settings.message_templates[1].platform, "danggeun")
            self.assertFalse(sm2.settings.conditional_metadata_enrichment_enabled)


if __name__ == "__main__":
    unittest.main()

