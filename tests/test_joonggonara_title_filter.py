import unittest

from scrapers.joonggonara import JoonggonaraScraper


class TestJoonggonaraTitleFilter(unittest.TestCase):
    def test_partial_completion_keywords_are_filtered(self):
        scraper = object.__new__(JoonggonaraScraper)

        self.assertFalse(scraper._is_valid_title("판매완료 아이폰 15"))
        self.assertFalse(scraper._is_valid_title("예약중 맥북"))
        self.assertFalse(scraper._is_valid_title("거래완료 닌텐도"))
        self.assertTrue(scraper._is_valid_title("아이폰 15 상태좋음"))


if __name__ == "__main__":
    unittest.main()
