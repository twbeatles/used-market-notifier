# pyright: reportUnsupportedDunderAll=false
"""Pure parsing helpers shared across marketplace scrapers and tests."""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, Iterable
from urllib.parse import parse_qs, urlsplit, urlunsplit

from models import Item
from price_utils import format_price_kr, parse_price_kr


def normalize_whitespace(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_multiline_text(value: str | None) -> str:
    lines = [normalize_whitespace(line) for line in str(value or "").splitlines()]
    return "\n".join(line for line in lines if line)

UNKNOWN_LOCATION_TEXTS = {"지역정보 없음", "지역 정보 없음"}
TIME_TEXT_RE = re.compile(r"^(?:\d+:)?\d{1,2}:\d{2}$")
URL_ONLY_RE = re.compile(r"^(?:https?://|www\.)\S+$", re.IGNORECASE)
QUESTION_ONLY_RE = re.compile(r"^[\s\?？!~·]+$")
PRICE_RE = re.compile(r"(\d{1,3}(?:,\d{3})+|\d{2,9})\s*원")
STRICT_PRICE_LINE_RE = re.compile(r"^(?:\d{1,3}(?:,\d{3})+|\d{4,9})(?:원)?$")
LOCATION_RE = re.compile(
    r"(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)[^\n|,/]{0,24}"
)
PRICE_CANDIDATE_RE = re.compile(r"\d[\d,\.]*\s*(?:만원|만|천원|천|원)")
PROFILE_ARIA_RE = re.compile(r"(.+?)님의 프로필 페이지")
SELLER_SUFFIX_COUNT_RE = re.compile(r"상품\d+$")
MICRO_LOCATION_TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9]+(?:역|동|읍|면|리|구)")
BUNJANG_PRODUCT_PATH_RE = re.compile(r"/products/(\d+)(?:[/?#]|$)")
JOONGGONARA_PATH_RE = re.compile(r"^/joonggonara/(\d+)(?:[/?#]|$)")
JOONGGONARA_MOBILE_PATH_RE = re.compile(r"^/ca-fe/(?:web/)?cafes/10050146/articles/(\d+)(?:[/?#]|$)")
TIME_MARKERS = ("방금", "초 전", "분 전", "시간 전", "일 전", "주 전", "달 전", "끌올")
BUNJANG_BADGE_LINES = {"배송비포함", "검수가능"}
BUNJANG_AD_TEXTS = {"AD", "광고", "SPONSORED"}
JOONGGONARA_ALLOWED_HOSTS = {"cafe.naver.com", "m.cafe.naver.com"}
PLATFORM_ALLOWED_HOSTS = {
    "danggeun": {"www.daangn.com", "daangn.com"},
    "bunjang": {"m.bunjang.co.kr", "bunjang.co.kr", "www.bunjang.co.kr"},
    "joonggonara": JOONGGONARA_ALLOWED_HOSTS,
}

GENERIC_SELLER_TEXTS = {
    "내상점",
    "판매하기",
    "상점정보",
    "상점후기",
    "좋아요",
    "공유",
    "프로필",
    "번개톡",
    "바로구매",
}
GENERIC_SELLER_FRAGMENTS = (
    "상점후기",
    "상품 더보기",
    "팔로우",
    "번개톡",
    "바로구매",
    "판매 물품",
)
JOONGGONARA_META_EXACT = {
    "스마트폰",
    "휴대폰",
    "태블릿",
    "디지털기기",
    "디지털/가전",
    "인기멤버",
    "1:1 채팅",
    "URL 복사",
    "카페홈",
    "목록",
}
JOONGGONARA_META_FRAGMENTS = (
    "게시판 목록",
    "본문 바로가기",
    "이전글",
    "다음글",
    "구매문의",
    "조회",
    "댓글",
    "중고나라 회원",
    "거래 시 꼭 알아주세요",
    "셀러회원",
    "좋아요",
)
JOONGGONARA_SELLER_NOISE = {
    "인기멤버",
    "1:1 채팅",
    "URL 복사",
    "좋아요",
}


@dataclass
class HtmlAnchorSnapshot:
    attrs: dict[str, str]
    text: str
    image: str | None = None


@dataclass
class HtmlDocumentSnapshot:
    anchors: list[HtmlAnchorSnapshot]
    ld_json_scripts: list[str]


@dataclass
class BunjangCardParseResult:
    title: str
    price: str
    location: str | None = None
    is_ad: bool = False
    malformed_reason: str | None = None


class _SnapshotHTMLParser(HTMLParser):
    BLOCK_BREAK_TAGS = {"br", "div", "p", "li", "section", "article", "time"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchors: list[HtmlAnchorSnapshot] = []
        self.ld_json_scripts: list[str] = []
        self._anchor_stack: list[dict[str, Any]] = []
        self._script_chunks: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {str(k): str(v or "") for k, v in attrs}
        if tag == "a":
            self._anchor_stack.append({"attrs": attr_map, "chunks": [], "images": []})
            return

        if tag == "script" and attr_map.get("type") == "application/ld+json":
            self._script_chunks = []
            return

        if tag == "img" and self._anchor_stack:
            src = attr_map.get("src") or attr_map.get("data-src")
            if src:
                self._anchor_stack[-1]["images"].append(src)
            return

        if tag in self.BLOCK_BREAK_TAGS and self._anchor_stack:
            self._anchor_stack[-1]["chunks"].append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._script_chunks is not None:
            script_text = "".join(self._script_chunks).strip()
            if script_text:
                self.ld_json_scripts.append(script_text)
            self._script_chunks = None
            return

        if tag == "a" and self._anchor_stack:
            raw_anchor = self._anchor_stack.pop()
            text = normalize_multiline_text("".join(raw_anchor["chunks"]))
            image = raw_anchor["images"][0] if raw_anchor["images"] else None
            self.anchors.append(
                HtmlAnchorSnapshot(
                    attrs=raw_anchor["attrs"],
                    text=text,
                    image=image,
                )
            )

        if tag in self.BLOCK_BREAK_TAGS and self._anchor_stack:
            self._anchor_stack[-1]["chunks"].append("\n")

    def handle_data(self, data: str) -> None:
        if self._anchor_stack:
            self._anchor_stack[-1]["chunks"].append(data)
        if self._script_chunks is not None:
            self._script_chunks.append(data)


__all__ = [name for name in globals() if not name.startswith("__")]
