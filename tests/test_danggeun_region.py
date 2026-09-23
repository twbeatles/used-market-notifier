"""당근 지역 이름 선택과 검색 URL."""

import unittest

from scrapers.marketplace_parsers import (
    DanggeunRegion,
    build_danggeun_search_url,
    choose_danggeun_region,
    clear_danggeun_region_cache,
    parse_region_locations,
    resolve_danggeun_region,
)


YEOKSAM = {
    "locations": [
        {
            "id": 6035,
            "name1": "서울특별시",
            "name2": "강남구",
            "name3": "역삼동",
            "name": "역삼동",
            "depth": 3,
        },
        {
            "id": 1673,
            "name1": "경기도",
            "name2": "용인시 처인구",
            "name3": "역삼동",
            "name": "역삼동",
            "depth": 3,
        },
    ]
}

NONHYEON = {
    "locations": [
        {
            "id": 6031,
            "name1": "서울특별시",
            "name2": "강남구",
            "name3": "논현동",
            "name": "논현동",
            "depth": 3,
        },
        {
            "id": 6498,
            "name1": "인천광역시",
            "name2": "남동구",
            "name3": "논현동",
            "name": "논현동",
            "depth": 3,
        },
    ]
}


class TestDanggeunRegion(unittest.TestCase):
    def setUp(self):
        clear_danggeun_region_cache()

    def test_duplicate_dong_prefers_seoul(self):
        regions = parse_region_locations(YEOKSAM)
        chosen = choose_danggeun_region("역삼동", regions)
        assert chosen is not None
        self.assertEqual(chosen.region_id, 6035)
        self.assertEqual(chosen.slug, "역삼동-6035")
        self.assertEqual(chosen.label, "서울특별시 강남구 역삼동")

    def test_full_address_selects_non_seoul_match(self):
        regions = parse_region_locations(NONHYEON)
        chosen = choose_danggeun_region("인천광역시 남동구 논현동", regions)
        assert chosen is not None
        self.assertEqual(chosen.region_id, 6498)
        self.assertEqual(chosen.slug, "논현동-6498")

    def test_bare_duplicate_name_still_prefers_seoul(self):
        chosen = choose_danggeun_region("논현동", parse_region_locations(NONHYEON))
        assert chosen is not None
        self.assertEqual(chosen.region_id, 6031)

    def test_resolve_uses_fetcher_and_cache(self):
        calls = []

        def fetcher(keyword: str):
            calls.append(keyword)
            return YEOKSAM

        first = resolve_danggeun_region("역삼동", fetcher=fetcher)
        second = resolve_danggeun_region("역삼동", fetcher=fetcher)
        assert first is not None and second is not None
        self.assertEqual(first.slug, "역삼동-6035")
        self.assertIs(first, second)
        self.assertEqual(calls, ["역삼동"])

    def test_explicit_slug_skips_fetcher(self):
        def fetcher(_keyword: str):
            raise AssertionError("fetcher should not run")

        region = resolve_danggeun_region("서초4동-366", fetcher=fetcher)
        assert isinstance(region, DanggeunRegion)
        self.assertEqual(region.slug, "서초4동-366")

    def test_search_url_includes_region_slug(self):
        url = build_danggeun_search_url("아이폰", "역삼동-6035")
        self.assertEqual(
            url,
            "https://www.daangn.com/kr/search/buy-sell/?q=%EC%95%84%EC%9D%B4%ED%8F%B0&in=%EC%97%AD%EC%82%BC%EB%8F%99-6035",
        )

    def test_unknown_query_returns_none(self):
        self.assertIsNone(choose_danggeun_region("없는동네", []))
        self.assertIsNone(resolve_danggeun_region("없는동네", fetcher=lambda _query: {"locations": []}))


if __name__ == "__main__":
    unittest.main()
