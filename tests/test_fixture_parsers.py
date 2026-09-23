import json
import re
import unittest
from pathlib import Path
from typing import Any, Mapping, cast

from scrapers.marketplace_parsers import (
    build_danggeun_search_url,
    classify_joonggonara_candidate,
    merge_item_metadata,
    parse_bunjang_detail_payload,
    parse_html_snapshot,
    parse_joonggonara_detail_text,
    parse_joonggonara_search_items,
)
from scrapers.playwright_bunjang import PlaywrightBunjangScraper
from scrapers.playwright_danggeun import PlaywrightDanggeunScraper
from models import Item


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
        drop_reasons = cast(Mapping[str, Any], metrics["drop_reason_count"])

        self.assertEqual(len(items), 1)
        self.assertEqual(metrics["json_ld_script_count"], 1)
        self.assertEqual(metrics["json_ld_item_count"], 3)
        self.assertEqual(metrics["items_after_json_ld"], 1)
        self.assertEqual(metrics["items_after_dom_fallback"], 0)
        self.assertEqual(drop_reasons["invalid_title"], 1)
        self.assertEqual(drop_reasons["missing_id"], 1)
        self.assertEqual(items[0].article_id, "12345")
        self.assertEqual(items[0].price, "750,000원")
        self.assertEqual(items[0].location, "서울 강남구 역삼동")

    def test_current_search_snapshot_reads_slug_json_ld_and_ignores_ads(self):
        scraper = object.__new__(PlaywrightDanggeunScraper)
        snapshot = parse_html_snapshot(_read_fixture("danggeun_search_snapshot_current.html"))

        items, metrics = scraper._parse_snapshot_items(snapshot, "아이폰")

        self.assertEqual(build_danggeun_search_url("아이폰 15"), "https://www.daangn.com/kr/search/buy-sell/?q=%EC%95%84%EC%9D%B4%ED%8F%B0%2015")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].article_id, "heatdwx3zwuy")
        self.assertEqual(items[0].title, "아이폰 12 미니 128GB 화이트")
        self.assertEqual(items[0].price, "150,000원")
        self.assertEqual(items[0].location, "만수3동")
        self.assertTrue(items[0].link.startswith("https://www.daangn.com/kr/buy-sell/"))
        self.assertGreaterEqual(metrics["dom_card_count"], 2)

    def test_cards_without_data_gtm_fall_back_when_json_ld_is_absent(self):
        scraper = object.__new__(PlaywrightDanggeunScraper)
        snapshot = parse_html_snapshot(_read_fixture("danggeun_search_cards_only.html"))

        items, metrics = scraper._parse_snapshot_items(snapshot, "아이폰")
        by_id = {item.article_id: item for item in items}

        self.assertEqual(metrics["json_ld_item_count"], 0)
        self.assertEqual(metrics["items_after_dom_fallback"], 2)
        self.assertEqual(set(by_id), {"heatdwx3zwuy", "v8k3tpo7o6v6"})
        self.assertEqual(by_id["v8k3tpo7o6v6"].location, "목동동")
        self.assertEqual(by_id["v8k3tpo7o6v6"].price, "160,000원")
        self.assertNotIn("ader.naver.com", " ".join(item.link for item in items))


class TestBunjangFixtureParser(unittest.TestCase):
    def test_snapshot_parser_reads_data_pid_cards_and_drop_reasons(self):
        scraper = object.__new__(PlaywrightBunjangScraper)
        snapshot = parse_html_snapshot(_read_fixture("bunjang_search_snapshot.html"))

        items, metrics = scraper._parse_snapshot_items(snapshot, "아이폰")
        drop_reasons = cast(Mapping[str, Any], metrics["drop_reason_count"])

        self.assertEqual(len(items), 1)
        self.assertEqual(metrics["dom_card_count"], 2)
        self.assertEqual(metrics["dom_product_link_count"], 2)
        self.assertEqual(metrics["items_after_dom_fallback"], 1)
        self.assertGreaterEqual(drop_reasons["missing_title"], 1)
        self.assertEqual(items[0].article_id, "738030")
        self.assertEqual(items[0].price, "160,000원")
        self.assertEqual(items[0].location, "서울특별시 서초구 반포3동")

    def test_tracked_absolute_product_urls_keep_price_first_cards(self):
        scraper = object.__new__(PlaywrightBunjangScraper)
        snapshot = parse_html_snapshot(_read_fixture("bunjang_search_snapshot_tracked.html"))

        items, metrics = scraper._parse_snapshot_items(snapshot, "아이폰")
        by_id = {item.article_id: item for item in items}

        self.assertEqual(set(by_id), {"433667944", "433826511"})
        self.assertEqual(by_id["433667944"].title, "배터리100 아이폰13미니 128기가 판매해요")
        self.assertEqual(by_id["433667944"].price, "345,000원")
        self.assertEqual(by_id["433826511"].title, "아이폰 13 프로맥스 128기가")
        self.assertEqual(by_id["433826511"].price, "455,000원")
        self.assertIn("imp_id=track", by_id["433667944"].link)
        self.assertGreaterEqual(metrics["dom_product_link_count"], 3)

    def test_detail_api_payload_maps_status_and_metadata(self):
        payload = json.loads(_read_fixture("bunjang_detail_api.json"))
        parsed = parse_bunjang_detail_payload(payload)

        self.assertEqual(parsed["seller"], "삼삼상점")
        self.assertEqual(parsed["location"], "서울특별시 강남구 역삼동")
        self.assertEqual(parsed["price"], "760,000원")
        self.assertEqual(parsed["price_numeric"], 760000)
        self.assertEqual(parsed["sale_status"], "reserved")

    def test_partial_detail_api_payload_can_be_merged_with_dom_location(self):
        payload = json.loads(_read_fixture("bunjang_detail_api_partial.json"))
        parsed = parse_bunjang_detail_payload(payload)

        self.assertEqual(parsed["seller"], "스마트온1")
        self.assertIsNone(parsed["location"])
        self.assertEqual(parsed["price"], "100,000원")
        self.assertEqual(parsed["sale_status"], "for_sale")

        base = Item(
            platform="bunjang",
            article_id="401916857",
            title="아이폰 6S 64기가 로즈 골드 A급 팝니다.",
            price="100,000원",
            link="https://m.bunjang.co.kr/products/401916857",
            keyword="아이폰",
        )
        api_item = PlaywrightBunjangScraper._apply_detail_payload(base, parsed)
        merged = merge_item_metadata(api_item, location="서울특별시 성동구 사근동")

        self.assertEqual(merged.seller, "스마트온1")
        self.assertEqual(merged.location, "서울특별시 성동구 사근동")
        self.assertEqual(merged.price, "100,000원")
        self.assertEqual(merged.sale_status, "for_sale")


class TestJoonggonaraFixtureParser(unittest.TestCase):
    def test_search_parser_rejects_noise_links(self):
        items = parse_joonggonara_search_items(_read_fixture("joonggonara_search_results.html"), "아이폰")

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].article_id, "12345678")
        self.assertEqual(items[0].title, "아이폰4s 16GB")

    def test_search_parser_rejects_smartstore_query_containing_cafe_site(self):
        smartstore_link = (
            "https://smartstore.naver.com/main/products/12460691050"
            "?nl-query=%EC%95%84%EC%9D%B4%ED%8F%B0%20site%3Acafe.naver.com%2Fjoonggonara"
        )
        self.assertIsNone(classify_joonggonara_candidate(smartstore_link, "아이폰15 중고 리퍼 자급제폰"))

    def test_search_parser_accepts_cafe_article_url(self):
        cafe_link = "https://cafe.naver.com/joonggonara/1129393870?q=%ec%95%84%ec%9d%b4%ed%8f%b0"
        candidate = classify_joonggonara_candidate(cafe_link, "아이폰12미니 128GB")
        self.assertIsNotNone(candidate)
        assert candidate is not None
        self.assertEqual(candidate["article_id"], "1129393870")

    def test_search_parser_keeps_cafe_articles_with_tracking_query(self):
        items = parse_joonggonara_search_items(
            _read_fixture("joonggonara_search_results_query.html"),
            "아이폰",
        )
        by_id = {item.article_id: item for item in items}

        self.assertEqual(set(by_id), {"1132321933", "1135514176"})
        self.assertEqual(by_id["1132321933"].title, "아이폰5 A1429 32G 공기계 iphone")
        self.assertIn("art=sample-token", by_id["1132321933"].link)
        self.assertTrue(by_id["1135514176"].link.startswith("https://m.cafe.naver.com/joonggonara/1135514176"))

    def test_detail_parser_extracts_iframe_body_fields(self):
        parsed = parse_joonggonara_detail_text(_html_to_text(_read_fixture("joonggonara_article_iframe.html")))

        self.assertEqual(parsed["title"], "아이폰4s 16GB")
        self.assertEqual(parsed["price"], "60,000원")
        self.assertEqual(parsed["location"], "개봉제3동")
        self.assertEqual(parsed["seller"], "전자기기만지는사람")

    def test_detail_parser_handles_realistic_meta_noise_and_manwon_price(self):
        parsed = parse_joonggonara_detail_text(
            _html_to_text(_read_fixture("joonggonara_article_iframe_complex.html"))
        )

        self.assertEqual(parsed["title"], "아이폰12프로 골드 액정 깨끗한 공기계 배터리효율 86%")
        self.assertEqual(parsed["price"], "350,000원")
        self.assertEqual(parsed["location"], "왕십리역,행당동")
        self.assertEqual(parsed["seller"], "왕십리역")


if __name__ == "__main__":
    unittest.main()
