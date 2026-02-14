import os
import tempfile
import unittest

from models import TagRule
from settings_manager import SettingsManager


class TestTagRulesRoundtrip(unittest.TestCase):
    def test_tag_rules_save_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = os.path.join(tmp, "settings.json")
            sm = SettingsManager(settings_path=settings_path)

            sm.settings.tag_rules = [
                TagRule(tag_name="급처", keywords=["급처", "급매"], color="#f38ba8", icon="🔥", enabled=True),
                TagRule(tag_name="택포", keywords=["택포"], color="#94e2d5", icon="📮", enabled=False),
            ]

            self.assertTrue(sm.save())

            sm2 = SettingsManager(settings_path=settings_path)
            self.assertEqual(len(sm2.settings.tag_rules), 2)
            self.assertEqual(sm2.settings.tag_rules[0].tag_name, "급처")
            self.assertEqual(sm2.settings.tag_rules[1].enabled, False)


if __name__ == "__main__":
    unittest.main()

