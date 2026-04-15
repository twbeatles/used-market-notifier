import importlib.util
import unittest

import monitor_engine
import scrapers
from scrapers.playwright_bunjang import PlaywrightBunjangScraper
from scrapers.playwright_danggeun import PlaywrightDanggeunScraper
from scrapers.playwright_joonggonara import PlaywrightJoonggonaraScraper


class TestImportSafety(unittest.TestCase):
    def test_monitor_engine_imports_even_without_selenium(self):
        self.assertTrue(hasattr(monitor_engine, "MonitorEngine"))
        self.assertIsNotNone(PlaywrightDanggeunScraper)
        self.assertIsNotNone(PlaywrightBunjangScraper)
        self.assertIsNotNone(PlaywrightJoonggonaraScraper)

    def test_selenium_exports_are_optional(self):
        selenium_missing = importlib.util.find_spec("selenium") is None
        if selenium_missing:
            self.assertIsNone(scrapers.DanggeunScraper)
            self.assertIsNone(scrapers.BunjangScraper)
            self.assertIsNone(scrapers.JoonggonaraScraper)
            self.assertIsNone(scrapers.SeleniumScraper)
        else:
            self.assertIsNotNone(scrapers.DanggeunScraper)
            self.assertIsNotNone(scrapers.BunjangScraper)
            self.assertIsNotNone(scrapers.JoonggonaraScraper)
            self.assertIsNotNone(scrapers.SeleniumScraper)


if __name__ == "__main__":
    unittest.main()
