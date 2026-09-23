import unittest

from scrapers.marketplace_parsers import normalize_location_value, pick_seller_candidate
from scrapers.playwright_danggeun import PlaywrightDanggeunScraper


class TestPlaywrightDanggeunParser(unittest.TestCase):
    def test_extract_article_id_numeric_url(self):
        url = "https://www.daangn.com/kr/buy-sell/sample-title-12345/"
        self.assertEqual(PlaywrightDanggeunScraper._extract_article_id(url), "12345")

    def test_extract_article_id_slug_url(self):
        url = "https://www.daangn.com/kr/buy-sell/sample-title-sfp71383orri/"
        self.assertEqual(PlaywrightDanggeunScraper._extract_article_id(url), "sfp71383orri")

    def test_extract_article_id_hash_fallback_is_deterministic(self):
        url = "https://example.com/no/article/id/here?foo=bar"
        id1 = PlaywrightDanggeunScraper._extract_article_id(url)
        id2 = PlaywrightDanggeunScraper._extract_article_id(url)
        self.assertIsNotNone(id1)
        self.assertIsNotNone(id2)
        assert id1 is not None and id2 is not None
        self.assertEqual(id1, id2)
        self.assertTrue(id1.startswith("hash_"))
        self.assertEqual(len(id1), len("hash_") + 12)

    def test_parse_card_text_extracts_title_price_location(self):
        text = "\n".join(
            [
                "아이폰15프로 256기가 네츄럴티타늄 판매",
                "750,000원",
                "여의도동",
                "·",
                "2시간 전",
            ]
        )
        title, price, location = PlaywrightDanggeunScraper._parse_card_text(text)
        self.assertEqual(title, "아이폰15프로 256기가 네츄럴티타늄 판매")
        self.assertEqual(price, "750,000원")
        self.assertEqual(location, "여의도동")

    def test_parse_card_text_skips_buy_now_badge(self):
        text = "\n".join(
            [
                "애플 아이폰 12 미니 128GB 그린",
                "160,000원",
                "목동동",
                "·",
                "16분 전",
                "바로구매",
            ]
        )
        title, price, location = PlaywrightDanggeunScraper._parse_card_text(text)
        self.assertEqual(title, "애플 아이폰 12 미니 128GB 그린")
        self.assertEqual(price, "160,000원")
        self.assertEqual(location, "목동동")

    def test_parse_card_text_trims_trailing_separator_on_location_line(self):
        text = "\n".join(["아이폰6+ 판매합니다", "60,000원", "농소2동 ·"])
        _title, _price, location = PlaywrightDanggeunScraper._parse_card_text(text)
        self.assertEqual(location, "농소2동")

    def test_location_normalization_trims_separator_and_time(self):
        self.assertEqual(normalize_location_value("행당동·"), "행당동")
        self.assertEqual(normalize_location_value("서울 강남구 역삼동 · 끌올 1일 전"), "서울 강남구 역삼동")
        self.assertEqual(normalize_location_value("잠원동 · 7분 전"), "잠원동")
        self.assertEqual(normalize_location_value("만수3동 · 끌올 41분 전"), "만수3동")

    def test_pick_seller_candidate_uses_danggeun_profile_aria_fallback(self):
        value = pick_seller_candidate(
            [
                {
                    "text": "",
                    "href": "/kr/users/sample-user/",
                    "aria_label": "주말만바라봄님의 프로필 페이지",
                },
                {"text": "주말만바라봄의 판매 물품", "href": "/kr/users/sample-user/", "aria_label": None},
            ],
            platform="danggeun",
        )
        self.assertEqual(value, "주말만바라봄")


if __name__ == "__main__":
    unittest.main()
