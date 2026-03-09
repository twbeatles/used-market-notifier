import unittest

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


if __name__ == "__main__":
    unittest.main()
