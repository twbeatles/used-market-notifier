"""당근 검색 지역 이름을 공개 지역 API의 동 코드로 바꿉니다."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib.parse import quote
from urllib.request import Request, urlopen

from .normalization import normalize_whitespace

REGION_KEYWORD_URL = "https://www.daangn.com/kr/api/v1/regions/keyword"
_REGION_SLUG_RE = re.compile(r"^(.+)-(\d+)$")
_cache: dict[str, "DanggeunRegion"] = {}


@dataclass(frozen=True, slots=True)
class DanggeunRegion:
    """확인된 당근 지역."""

    region_id: int
    name: str
    name1: str = ""
    name2: str = ""
    name3: str = ""
    depth: int = 0

    @property
    def label(self) -> str:
        parts = [self.name1, self.name2, self.name3 or self.name]
        label = " ".join(part for part in parts if part)
        return label or self.name

    @property
    def slug(self) -> str:
        short_name = self.name3 or self.name
        return f"{short_name}-{self.region_id}"


def parse_region_slug(value: str) -> DanggeunRegion | None:
    """이미 `역삼동-6035` 형태면 API 없이 사용합니다."""
    match = _REGION_SLUG_RE.fullmatch(normalize_whitespace(value))
    if not match:
        return None
    name = match.group(1).strip()
    if not name:
        return None
    return DanggeunRegion(
        region_id=int(match.group(2)),
        name=name,
        name3=name,
        depth=3,
    )


def parse_region_locations(payload: Mapping[str, Any] | None) -> list[DanggeunRegion]:
    raw_locations = (payload or {}).get("locations", [])
    if not isinstance(raw_locations, list):
        return []
    regions: list[DanggeunRegion] = []
    for raw in raw_locations:
        if not isinstance(raw, dict):
            continue
        raw_id = raw.get("id")
        if raw_id is None:
            continue
        try:
            region_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        name = normalize_whitespace(raw.get("name"))
        name3 = normalize_whitespace(raw.get("name3")) or name
        if not name and not name3:
            continue
        try:
            depth = int(raw.get("depth") or 0)
        except (TypeError, ValueError):
            depth = 0
        regions.append(
            DanggeunRegion(
                region_id=region_id,
                name=name or name3,
                name1=normalize_whitespace(raw.get("name1")),
                name2=normalize_whitespace(raw.get("name2")),
                name3=name3,
                depth=depth,
            )
        )
    return regions


def _matches_query(region: DanggeunRegion, query: str) -> bool:
    compact_query = query.replace(" ", "")
    fields = [region.name, region.name1, region.name2, region.name3, region.label]
    return any(query == field or compact_query == field.replace(" ", "") for field in fields if field)


def choose_danggeun_region(query: str, regions: list[DanggeunRegion]) -> DanggeunRegion | None:
    """같은 지명이 여러 곳이면 입력과 맞는 후보 중 서울 동을 먼저 고릅니다."""
    text = normalize_whitespace(query)
    if not text or not regions:
        return None
    exact = [region for region in regions if _matches_query(region, text)]
    pool = exact or regions
    seoul_dongs = [
        region for region in pool if region.name1 == "서울특별시" and region.depth == 3
    ]
    if seoul_dongs:
        return seoul_dongs[0]
    return pool[0]


def fetch_danggeun_regions(keyword: str) -> dict[str, Any]:
    """당근 지역 검색 API. 실패하면 예외를 그대로 올립니다."""
    url = f"{REGION_KEYWORD_URL}?keyword={quote(normalize_whitespace(keyword))}"
    request = Request(
        url,
        headers={"User-Agent": "UsedMarketNotifier", "Accept": "application/json"},
    )
    with urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Daangn region response is not an object")
    return payload


def resolve_danggeun_region(
    query: str,
    *,
    fetcher: Callable[[str], Mapping[str, Any]] | None = None,
) -> DanggeunRegion | None:
    """지역 이름 또는 `동-id` 코드를 검색에 넣을 지역으로 바꿉니다."""
    text = normalize_whitespace(query)
    if not text:
        return None
    direct = parse_region_slug(text)
    if direct is not None:
        return direct
    cached = _cache.get(text)
    if cached is not None:
        return cached
    payload = (fetcher or fetch_danggeun_regions)(text)
    chosen = choose_danggeun_region(text, parse_region_locations(payload))
    if chosen is not None:
        _cache[text] = chosen
    return chosen


def clear_danggeun_region_cache() -> None:
    _cache.clear()
