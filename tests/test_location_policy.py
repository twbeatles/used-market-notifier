import unittest

from models import Item, SearchKeyword


def _item(platform: str, location: str | None) -> Item:
    return Item(
        platform=platform,
        article_id=f"{platform}-id",
        title="테스트",
        price="10,000원",
        link="https://example.com",
        keyword="테스트",
        location=location,
    )


class TestLocationPolicy(unittest.TestCase):
    def test_danggeun_location_is_strict_when_filter_is_set(self):
        kw = SearchKeyword(keyword="맥북", location="강남")

        self.assertFalse(kw.matches_location(_item("danggeun", None)))
        self.assertTrue(kw.matches_location(_item("danggeun", "서울 강남구")))
        self.assertFalse(kw.matches_location(_item("danggeun", "서울 마포구")))

    def test_non_danggeun_keeps_best_effort_behavior(self):
        kw = SearchKeyword(keyword="맥북", location="강남")

        # Unknown location still passes for non-danggeun platforms.
        self.assertTrue(kw.matches_location(_item("bunjang", None)))
        self.assertTrue(kw.matches_location(_item("joonggonara", "서울 강남구")))


if __name__ == "__main__":
    unittest.main()
