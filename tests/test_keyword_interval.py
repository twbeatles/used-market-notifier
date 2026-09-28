"""Regression: custom keyword interval uses UTC-correct DB times and per-config keys."""

import os
import tempfile
import unittest

from db import DatabaseManager
from models import AppSettings, SearchKeyword
from monitor_engine import MonitorEngine


class _Settings:
    def __init__(self):
        self.settings = AppSettings(notifications_enabled=False)


class KeywordIntervalTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = DatabaseManager(os.path.join(self.tmp.name, "t.db"))
        self.engine = MonitorEngine(_Settings(), db=self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_recent_db_search_is_not_treated_as_elapsed(self):
        # checked_at is SQLite CURRENT_TIMESTAMP (UTC); a local-time comparison
        # used to add the UTC offset (+540 min in KST) to the elapsed time.
        self.db.record_search_stats("아이폰", "bunjang", 3, 0)
        kw = SearchKeyword(keyword="아이폰", platforms=["bunjang"], custom_interval=30)
        elapsed = self.engine._minutes_since_keyword_run(kw, self.engine._keyword_interval_key(kw))
        self.assertIsNotNone(elapsed)
        self.assertLess(elapsed, 1.0)

    def test_db_lookup_is_limited_to_keyword_platforms(self):
        self.db.record_search_stats("아이폰", "danggeun", 3, 0)
        kw = SearchKeyword(keyword="아이폰", platforms=["bunjang"], custom_interval=30)
        self.assertIsNone(self.engine._minutes_since_keyword_run(kw, self.engine._keyword_interval_key(kw)))

    def test_interval_keys_differ_by_location_and_platforms(self):
        a = SearchKeyword(keyword="아이폰", platforms=["danggeun"], location="강남")
        b = SearchKeyword(keyword="아이폰", platforms=["danggeun"], location="역삼동")
        c = SearchKeyword(keyword="아이폰", platforms=["bunjang"], location="강남")
        keys = {self.engine._keyword_interval_key(k) for k in (a, b, c)}
        self.assertEqual(len(keys), 3)


if __name__ == "__main__":
    unittest.main()
