import unittest

from price_utils import parse_price_kr
from models import Item


class TestPriceParseKR(unittest.TestCase):
    def test_free_keywords(self):
        self.assertEqual(parse_price_kr("무료나눔"), 0)
        self.assertEqual(parse_price_kr("무료"), 0)
        self.assertEqual(parse_price_kr("나눔"), 0)

    def test_plain_won(self):
        self.assertEqual(parse_price_kr("10,000원"), 10000)
        self.assertEqual(parse_price_kr("10000"), 10000)

    def test_man_unit(self):
        self.assertEqual(parse_price_kr("10만"), 100000)
        self.assertEqual(parse_price_kr("10만원"), 100000)
        self.assertEqual(parse_price_kr("1.2만"), 12000)

    def test_man_plus_thousand(self):
        self.assertEqual(parse_price_kr("2만5천"), 25000)
        self.assertEqual(parse_price_kr("2만 5천원"), 25000)

    def test_item_parse_price_uses_parser(self):
        it = Item(
            platform="danggeun",
            article_id="x",
            title="t",
            price="10만원",
            link="https://example.com",
            keyword="k",
        )
        self.assertEqual(it.parse_price(), 100000)


if __name__ == "__main__":
    unittest.main()

