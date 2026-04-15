import json
import re
import unittest
from pathlib import Path

from scrapers.marketplace_parsers import (
    parse_bunjang_detail_payload,
    parse_html_snapshot,
    parse_joonggonara_detail_text,
    parse_joonggonara_search_items,
)
from scrapers.playwright_bunjang import PlaywrightBunjangScraper
from scrapers.playwright_danggeun import PlaywrightDanggeunScraper


FIXTURES = Path(__file__).parent / "fixtures"


def _read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _html_to_text(html: str) -> str:
    return re.sub(r"<[^>]+>", "\n", html)


class TestDanggeunFixtureParser(unittest.TestCase):
    def test_snapshot_parser_uses_json_ld_and_tracks_drop_reasons(self):
        scraper = object.__new__(PlaywrightDanggeunScraper)
        snapshot = parse_html_snapshot(_read_fixture("danggeun_search_snapshot.html"))

        items, metrics = scraper._parse_snapshot_items(snapshot, "아이폰")

        self.assertEqual(len(items), 1)
        self.assertEqual(metrics["json_ld_script_count"], 1)
        self.assertEqual(metrics["json_ld_item_count"], 3)
        self.assertEqual(metrics["items_after_json_ld"], 1)
        self.assertEqual(metrics["items_after_dom_fallback"], 0)
        self.assertEqual(metrics["drop_reason_count"]["invalid_title"], 1)
        self.assertEqual(metrics["drop_reason_count"]["missing_id"], 1)
        self.assertEqual(items[0].article_id, "12345")
        self.assertEqual(items[0].price, "750,000원")
        self.assertEqual(items[0].location, "서울 강남구 역삼동")


class TestBunjangFixtureParser(unittest.TestCase):
    def test_snapshot_parser_reads_data_pid_cards_and_drop_reasons(self):
        scraper = object.__new__(PlaywrightBunjangScraper)
        snapshot = parse_html_snapshot(_read_fixture("bunjang_search_snapshot.html"))

        items, metrics = scraper._parse_snapshot_items(snapshot, "아이폰")

        self.assertEqual(len(items), 1)
        self.assertEqual(metrics["dom_card_count"], 2)
        self.assertEqual(metrics["items_after_data_pid"], 1)
        self.assertEqual(metrics["drop_reason_count"]["invalid_title"], 1)
        self.assertEqual(items[0].article_id, "738030")
        self.assertEqual(items[0].price, "160,000원")
        self.assertEqual(items[0].location, "서울특별시 서초구 반포3동")

    def test_detail_api_payload_maps_status_and_metadata(self):
        payload = json.loads(_read_fixture("bunjang_detail_api.json"))
        parsed = parse_bunjang_detail_payload(payload)

        self.assertEqual(parsed["seller"], "삼삼상점")
        self.assertEqual(parsed["location"], "서울특별시 강남구 역삼동")
        self.assertEqual(parsed["price"], "760,000원")
        self.assertEqual(parsed["price_numeric"], 760000)
        self.assertEqual(parsed["sale_status"], "reserved")


class TestJoonggonaraFixtureParser(unittest.TestCase):
    def test_search_parser_rejects_noise_links(self):
        items = parse_joonggonara_search_items(_read_fixture("joonggonara_search_results.html"), "아이폰")

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].article_id, "12345678")
        self.assertEqual(items[0].title, "아이폰4s 16GB")

    def test_detail_parser_extracts_iframe_body_fields(self):
        parsed = parse_joonggonara_detail_text(_html_to_text(_read_fixture("joonggonara_article_iframe.html")))

        self.assertEqual(parsed["title"], "아이폰4s 16GB")
        self.assertEqual(parsed["price"], "60,000원")
        self.assertEqual(parsed["location"], "개봉제3동")
        self.assertEqual(parsed["seller"], "전자기기만지는사람")


if __name__ == "__main__":
    unittest.main()
