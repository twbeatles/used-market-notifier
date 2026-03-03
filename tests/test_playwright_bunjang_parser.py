import unittest

from scrapers.playwright_bunjang import PlaywrightBunjangScraper


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


if __name__ == "__main__":
    unittest.main()
