import unittest

from scrapers.marketplace_parsers import merge_item_metadata, pick_seller_candidate
from scrapers.playwright_bunjang import PlaywrightBunjangScraper
from models import Item


class TestPlaywrightBunjangParser(unittest.TestCase):
    def test_normalize_location_unknown_to_none(self):
        self.assertIsNone(PlaywrightBunjangScraper._normalize_location("지역정보 없음"))
        self.assertIsNone(PlaywrightBunjangScraper._normalize_location("지역 정보 없음"))

    def test_normalize_location_keeps_valid_text(self):
        value = "서울특별시 서초구 반포3동"
        self.assertEqual(PlaywrightBunjangScraper._normalize_location(value), value)

    def test_parse_card_text_fallback_removes_badges_and_parses(self):
        text = "\n".join(
            [
                "배송비포함",
                "검수가능",
                "[738030] 아이폰7 제트블랙 128기가 배터리 100% 공기계",
                "160,000",
                "5초 전",
                "지역정보 없음",
            ]
        )
        title, price, location = PlaywrightBunjangScraper._parse_card_text_fallback(text)
        self.assertEqual(title, "[738030] 아이폰7 제트블랙 128기가 배터리 100% 공기계")
        self.assertEqual(price, "160,000원")
        self.assertIsNone(location)

    def test_parse_card_text_fallback_with_real_location(self):
        text = "\n".join(
            [
                "검수가능",
                "아이폰8 로즈골드 256기가",
                "170,000",
                "1분 전",
                "경기도 광주시 쌍령동",
            ]
        )
        title, price, location = PlaywrightBunjangScraper._parse_card_text_fallback(text)
        self.assertEqual(title, "아이폰8 로즈골드 256기가")
        self.assertEqual(price, "170,000원")
        self.assertEqual(location, "경기도 광주시 쌍령동")

    def test_pick_seller_candidate_skips_generic_shop_entries(self):
        value = pick_seller_candidate(
            [
                {"text": "내상점", "href": "/shop//products", "aria_label": None},
                {"text": "스마트온1상품30", "href": None, "aria_label": None},
                {"text": "스마트온1", "href": "/shop/3756791/products", "aria_label": None},
            ],
            platform="bunjang",
        )
        self.assertEqual(value, "스마트온1")

    def test_merge_item_metadata_keeps_api_price_and_status_while_filling_dom_location(self):
        item = Item(
            platform="bunjang",
            article_id="401916857",
            title="아이폰 6S 64기가 로즈 골드 A급 팝니다.",
            price="100,000원",
            link="https://m.bunjang.co.kr/products/401916857",
            keyword="아이폰",
            seller="스마트온1",
            location=None,
            sale_status="for_sale",
            price_numeric=100000,
        )
        merged = merge_item_metadata(item, location="서울특별시 성동구 사근동")

        self.assertEqual(merged.seller, "스마트온1")
        self.assertEqual(merged.location, "서울특별시 성동구 사근동")
        self.assertEqual(merged.price, "100,000원")
        self.assertEqual(merged.sale_status, "for_sale")


if __name__ == "__main__":
    unittest.main()
