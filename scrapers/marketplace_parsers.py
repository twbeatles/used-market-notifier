"""Pure parsing helpers shared across marketplace scrapers and tests."""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, Iterable
from urllib.parse import parse_qs, urlsplit, urlunsplit

from models import Item
from price_utils import format_price_kr, parse_price_kr

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


def parse_html_snapshot(html: str) -> HtmlDocumentSnapshot:
    parser = _SnapshotHTMLParser()
    parser.feed(str(html or ""))
    parser.close()
    return HtmlDocumentSnapshot(anchors=parser.anchors, ld_json_scripts=parser.ld_json_scripts)


def normalize_whitespace(value: str | None) -> str:
    return " ".join(str(value or "").split())


def normalize_multiline_text(value: str | None) -> str:
    lines = [normalize_whitespace(line) for line in str(value or "").splitlines()]
    return "\n".join(line for line in lines if line)


def normalize_price_text(value: Any, *, unknown: str = "가격문의") -> str:
    digits = re.sub(r"[^\d]", "", str(value or ""))
    if not digits:
        return unknown
    return f"{int(digits):,}원"


def looks_like_time_line(value: Any) -> bool:
    text = normalize_whitespace(str(value or ""))
    if not text:
        return False
    return TIME_TEXT_RE.fullmatch(text) is not None or any(marker in text for marker in TIME_MARKERS)


def is_strict_price_line(value: Any) -> bool:
    text = normalize_whitespace(str(value or ""))
    if not text:
        return False
    compact = text.replace(" ", "")
    if PRICE_CANDIDATE_RE.fullmatch(compact):
        return True
    return STRICT_PRICE_LINE_RE.fullmatch(compact) is not None


def is_count_or_metric_line(value: Any) -> bool:
    text = normalize_whitespace(str(value or ""))
    if not text:
        return True
    return re.fullmatch(r"\d{1,3}\+?", text) is not None


def is_malformed_listing_title(value: Any) -> bool:
    text = normalize_whitespace(str(value or ""))
    if len(text) < 2:
        return True
    upper = text.upper()
    if upper in BUNJANG_AD_TEXTS:
        return True
    lowered = text.lower()
    if any(
        marker in lowered
        for marker in ("광고", "no title", "제목 없음", "판매완료", "예약중", "거래완료", "배송비포함", "검수가능")
    ):
        return True
    if text in UNKNOWN_LOCATION_TEXTS or text.replace(" ", "") == "지역정보없음":
        return True
    if is_strict_price_line(text):
        return True
    if looks_like_time_line(text) or is_count_or_metric_line(text):
        return True
    return False


def normalize_location_value(value: Any) -> str | None:
    text = normalize_whitespace(str(value or ""))
    if not text:
        return None
    text = re.split(r"\s*[·|]\s*(?:방금|초 전|분 전|시간 전|일 전|주 전|달 전|끌올)", text, maxsplit=1)[0]
    text = re.sub(r"\s*(?:방금|초 전|분 전|시간 전|일 전|주 전|달 전|끌올).*$", "", text).strip()
    text = text.strip(" \t\r\n·,/|")
    if not text:
        return None
    compact = text.replace(" ", "")
    if compact in {"지역정보없음"} or text in UNKNOWN_LOCATION_TEXTS:
        return None
    if looks_like_time_line(text) or is_count_or_metric_line(text) or is_strict_price_line(text):
        return None
    return text


def extract_label_value(text: str, labels: Iterable[str], *, max_chars: int = 80) -> str | None:
    text_value = str(text or "")
    for label in labels:
        pattern = rf"{re.escape(label)}\s*[:：]?\s*([^\n]{{1,{max_chars}}})"
        match = re.search(pattern, text_value)
        if match:
            candidate = normalize_whitespace(match.group(1))
            if candidate:
                return candidate
    return None


def extract_location_from_text(text: str) -> str | None:
    labeled = extract_label_value(text, ("거래 희망지역", "거래희망지역", "거래 지역", "거래지역", "지역 정보", "지역정보", "지역"))
    if labeled:
        normalized = normalize_location_value(labeled)
        if normalized:
            return normalized
    match = LOCATION_RE.search(str(text or ""))
    if not match:
        return None
    return normalize_location_value(match.group(0))


def extract_profile_name_from_aria_label(value: str | None) -> str | None:
    text = normalize_whitespace(value)
    if not text:
        return None
    match = PROFILE_ARIA_RE.search(text)
    if not match:
        return None
    candidate = normalize_whitespace(match.group(1))
    return candidate or None


def pick_seller_candidate(candidates: Iterable[dict[str, Any]], *, platform: str) -> str | None:
    normalized_platform = str(platform or "").strip().lower()
    for candidate in candidates:
        text = normalize_whitespace(candidate.get("text"))
        href = normalize_whitespace(candidate.get("href"))
        aria_label = candidate.get("aria_label")

        if normalized_platform == "danggeun" and not text:
            text = extract_profile_name_from_aria_label(str(aria_label or ""))

        if not text:
            continue

        text = SELLER_SUFFIX_COUNT_RE.sub("", text).strip()
        if not text:
            continue

        if href and "/shop//" in href:
            continue
        if text in GENERIC_SELLER_TEXTS:
            continue
        if any(fragment in text for fragment in GENERIC_SELLER_FRAGMENTS):
            continue
        if re.fullmatch(r"\d+", text):
            continue
        if len(text) > 30:
            continue
        return text
    return None


def merge_item_metadata(
    item: Item,
    *,
    title: Any = None,
    seller: Any = None,
    location: Any = None,
    price: Any = None,
    sale_status: Any = None,
    price_numeric: Any = None,
) -> Item:
    resolved_price_numeric = item.price_numeric
    if price_numeric is not None:
        try:
            resolved_price_numeric = int(price_numeric)
        except Exception:
            resolved_price_numeric = item.price_numeric

    resolved_price = item.price
    if price is not None and str(price).strip():
        resolved_price = str(price).strip()

    resolved_title = normalize_whitespace(str(title or "")) or item.title
    resolved_seller = normalize_whitespace(str(seller or "")) or item.seller
    resolved_location = normalize_location_value(location) or item.location
    resolved_sale_status = normalize_whitespace(str(sale_status or "")) or item.sale_status

    return Item(
        platform=item.platform,
        article_id=item.article_id,
        title=resolved_title,
        price=resolved_price,
        link=item.link,
        keyword=item.keyword,
        thumbnail=item.thumbnail,
        seller=resolved_seller,
        location=resolved_location,
        sale_status=resolved_sale_status,
        price_numeric=resolved_price_numeric,
    )


def _lookup_path(payload: Any, path: tuple[Any, ...]) -> Any:
    current = payload
    for key in path:
        if isinstance(current, dict):
            current = current.get(key)
            continue
        if isinstance(current, list) and isinstance(key, int):
            if key >= len(current):
                return None
            current = current[key]
            continue
        return None
    return current


def _first_non_empty(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, (list, tuple)):
            for nested in value:
                if nested is None:
                    continue
                if isinstance(nested, str) and not nested.strip():
                    continue
                return nested
            continue
        return value
    return None


def normalize_sale_status(value: Any) -> str | None:
    raw = normalize_whitespace(str(value or ""))
    if not raw:
        return None

    normalized = re.sub(r"[^a-z0-9가-힣]+", "", raw.lower())
    if normalized in {"onsale", "sale", "selling", "forsale", "판매중", "판매", "available", "진행중"}:
        return "for_sale"
    if normalized in {"reservation", "reserved", "reserve", "예약", "예약중", "hold"}:
        return "reserved"
    if normalized in {"sold", "soldout", "soldoutcompleted", "판매완료", "거래완료", "완료", "품절"}:
        return "sold"
    if normalized in {"unknown", "미확인", "알수없음"}:
        return "unknown"
    return "unknown"


def parse_bunjang_detail_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    root = payload or {}
    if isinstance(root.get("data"), dict):
        root = root["data"]

    product = root.get("product")
    if not isinstance(product, dict):
        product = {}
    shop = root.get("shop")
    if not isinstance(shop, dict):
        shop = {}

    seller = normalize_whitespace(
        _first_non_empty(
            shop.get("name"),
            shop.get("shopName"),
            shop.get("userName"),
            product.get("sellerName"),
            product.get("userName"),
            _lookup_path(shop, ("seller", "name")),
        )
        or ""
    ) or None

    location = normalize_location_value(
        _first_non_empty(
            product.get("location"),
            product.get("locationName"),
            product.get("region"),
            product.get("regionName"),
            product.get("regionFullName"),
            product.get("geoLabel"),
            _lookup_path(product, ("locationInfo", "name")),
            _lookup_path(product, ("locationInfo", "fullName")),
            _lookup_path(product, ("userArea", "name")),
            _lookup_path(product, ("userArea", "fullName")),
            _lookup_path(product, ("regions", 0, "name")),
            _lookup_path(product, ("regions", 0, "fullName")),
            _lookup_path(shop, ("location", "name")),
            _lookup_path(root, ("location", "name")),
        )
    )

    raw_price = _first_non_empty(
        product.get("price"),
        product.get("priceNumeric"),
        _lookup_path(product, ("priceInfo", "price")),
        _lookup_path(product, ("priceInfo", "amount")),
    )
    price_numeric = 0
    if raw_price is not None:
        try:
            price_numeric = int(float(str(raw_price).replace(",", "").strip()))
        except Exception:
            price_numeric = 0
    price = normalize_price_text(price_numeric) if price_numeric > 0 else None

    sale_status = normalize_sale_status(
        _first_non_empty(
            product.get("saleStatus"),
            product.get("status"),
            root.get("saleStatus"),
        )
    )

    title = normalize_whitespace(
        _first_non_empty(
            product.get("name"),
            product.get("title"),
            root.get("name"),
        )
        or ""
    ) or None

    return {
        "seller": seller,
        "location": location,
        "price": price,
        "price_numeric": price_numeric or None,
        "sale_status": sale_status,
        "title": title,
    }


def normalize_url_for_match(url: str) -> str:
    raw = str(url or "").strip()
    if not raw:
        return ""
    try:
        parts = urlsplit(raw)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))
    except Exception:
        return raw


def _host_from_url(url: str) -> str:
    try:
        return urlsplit(str(url or "")).netloc.lower()
    except Exception:
        return ""


def validate_platform_url(platform: str, url: str) -> bool:
    normalized_platform = str(platform or "").strip().lower()
    host = _host_from_url(url)
    if not normalized_platform or not host:
        return False
    allowed = PLATFORM_ALLOWED_HOSTS.get(normalized_platform)
    if not allowed:
        return True
    return host in allowed


def extract_bunjang_product_id(link: str) -> str | None:
    if not link:
        return None
    match = BUNJANG_PRODUCT_PATH_RE.search(str(link))
    return match.group(1) if match else None


def parse_bunjang_card_text(text: str) -> BunjangCardParseResult:
    raw_lines = [normalize_whitespace(line) for line in str(text or "").splitlines()]
    lines = [line for line in raw_lines if line and line != "·" and line not in BUNJANG_BADGE_LINES]

    is_ad = any(line.upper() in BUNJANG_AD_TEXTS for line in lines[:2])
    lines = [line for line in lines if line.upper() not in BUNJANG_AD_TEXTS]
    if not lines:
        return BunjangCardParseResult("", "N/A", None, is_ad=is_ad, malformed_reason="empty")

    price = "N/A"
    price_idx = -1
    for idx, line in enumerate(lines):
        if is_strict_price_line(line):
            price = normalize_price_text(line, unknown="N/A")
            price_idx = idx
            break

    def looks_like_location_only(value: str) -> bool:
        normalized = normalize_location_value(value)
        if not normalized:
            return False
        return LOCATION_RE.fullmatch(normalized) is not None

    def valid_title_candidate(value: str) -> bool:
        if is_malformed_listing_title(value):
            return False
        if value in BUNJANG_BADGE_LINES:
            return False
        if looks_like_location_only(value):
            return False
        return True

    title = ""
    if price_idx >= 0:
        for line in lines[price_idx + 1:]:
            if valid_title_candidate(line):
                title = line
                break
        if not title:
            for line in reversed(lines[:price_idx]):
                if valid_title_candidate(line):
                    title = line
                    break
    else:
        for line in lines:
            if valid_title_candidate(line):
                title = line
                break

    location: str | None = None
    if title:
        title_index = lines.index(title) if title in lines else -1
        search_lines = lines[title_index + 1:] if title_index >= 0 else lines
        for line in reversed(search_lines):
            if line == title or is_strict_price_line(line) or looks_like_time_line(line) or is_count_or_metric_line(line):
                continue
            normalized = normalize_location_value(line)
            if normalized and LOCATION_RE.search(normalized):
                location = normalized
                break

    malformed_reason = None
    if not title:
        malformed_reason = "missing_title"
    elif is_malformed_listing_title(title):
        malformed_reason = "malformed_title"

    return BunjangCardParseResult(title, price, location, is_ad=is_ad, malformed_reason=malformed_reason)


def parse_bunjang_search_items(
    snapshot: HtmlDocumentSnapshot,
    keyword: str,
    *,
    max_results: int = 120,
) -> tuple[list[Item], dict[str, object]]:
    metrics: dict[str, object] = {
        "dom_card_count": 0,
        "dom_product_link_count": 0,
        "items_after_data_pid": 0,
        "items_after_dom_fallback": 0,
        "drop_reason_count": {},
    }
    drop_reasons: dict[str, int] = {}

    def drop(reason: str) -> None:
        drop_reasons[reason] = drop_reasons.get(reason, 0) + 1

    items: list[Item] = []
    seen_pids: set[str] = set()

    product_links = [
        anchor
        for anchor in snapshot.anchors
        if "/products/" in str(anchor.attrs.get("href") or "")
    ]
    metrics["dom_product_link_count"] = len(product_links)

    data_pid_cards = [anchor for anchor in snapshot.anchors if anchor.attrs.get("data-pid")]
    metrics["dom_card_count"] = len(data_pid_cards)

    def append_anchor(anchor: HtmlAnchorSnapshot, *, from_data_pid: bool) -> None:
        if len(items) >= max_results:
            return
        href = str(anchor.attrs.get("href") or "").strip()
        pid = str(anchor.attrs.get("data-pid") or "").strip() if from_data_pid else ""
        if href.startswith("/"):
            href = f"https://m.bunjang.co.kr{href}"
        if not pid:
            pid = extract_bunjang_product_id(href) or ""
        if not pid:
            drop("missing_id")
            return
        if pid in seen_pids:
            drop("duplicate_id")
            return
        if href and not validate_platform_url("bunjang", href):
            drop("host_mismatch")
            return

        parsed = parse_bunjang_card_text(anchor.text)
        if parsed.is_ad:
            drop("ad")
            return
        if parsed.malformed_reason:
            drop(parsed.malformed_reason)
            return

        link = href or f"https://m.bunjang.co.kr/products/{pid}"
        items.append(
            Item(
                platform="bunjang",
                article_id=pid,
                title=parsed.title,
                price=parsed.price,
                link=link,
                keyword=keyword,
                thumbnail=anchor.image,
                seller=None,
                location=parsed.location,
            )
        )
        seen_pids.add(pid)

    for anchor in product_links[:max_results]:
        append_anchor(anchor, from_data_pid=False)

    metrics["items_after_dom_fallback"] = len(items)

    for anchor in data_pid_cards:
        if len(items) >= max_results:
            break
        append_anchor(anchor, from_data_pid=True)

    metrics["items_after_data_pid"] = max(0, len(items) - int(metrics["items_after_dom_fallback"]))
    metrics["drop_reason_count"] = drop_reasons
    return items, metrics


def extract_numeric_article_id(link: str) -> str | None:
    if not link:
        return None
    try:
        parts = urlsplit(link)
        host = parts.netloc.lower()
        path = parts.path or ""
        if host not in JOONGGONARA_ALLOWED_HOSTS:
            return None

        match = JOONGGONARA_PATH_RE.search(path)
        if match:
            return match.group(1)
        match = JOONGGONARA_MOBILE_PATH_RE.search(path)
        if match:
            return match.group(1)

        qs = parse_qs(parts.query or "")
        article_ids = qs.get("articleid") or qs.get("articleId") or qs.get("articleID")
        if article_ids and article_ids[0]:
            club_ids = qs.get("clubid") or qs.get("clubId") or qs.get("clubID")
            if club_ids and str(club_ids[0]) != "10050146":
                return None
            match = re.search(r"(\d+)", str(article_ids[0]))
            if match:
                return match.group(1)
    except Exception:
        return None
    return None


def is_valid_joonggonara_title(title: str) -> bool:
    cleaned = normalize_whitespace(title)
    if len(cleaned) < 2 or len(cleaned) > 120:
        return False
    lowered = cleaned.lower()
    if lowered in {"중고나라", "joonggonara", "중고 나라"}:
        return False
    if TIME_TEXT_RE.fullmatch(cleaned):
        return False
    if URL_ONLY_RE.fullmatch(cleaned):
        return False
    if QUESTION_ONLY_RE.fullmatch(cleaned):
        return False
    if re.fullmatch(r"[0-9,]+", cleaned):
        return False
    if "cafe.naver.com/joonggonara" in lowered:
        return False
    if any(marker in lowered for marker in ("판매완료", "예약중", "거래완료", "no title", "광고", "배송비포함")):
        return False
    if not re.search(r"[0-9a-z가-힣]", lowered):
        return False
    return True


def classify_joonggonara_candidate(link: str, text: str) -> dict[str, str] | None:
    normalized_link = normalize_url_for_match(link)
    if not normalized_link or not validate_platform_url("joonggonara", normalized_link):
        return None
    article_id = extract_numeric_article_id(normalized_link)
    if not article_id:
        return None

    first_line = next((line.strip() for line in str(text or "").splitlines() if line.strip()), "")
    title = normalize_whitespace(first_line)
    if not is_valid_joonggonara_title(title):
        return None

    return {"article_id": article_id, "title": title, "link": normalized_link}


def evaluate_scrape_quality(platform: str, items: list[Item]) -> dict[str, object]:
    total = len(items or [])
    malformed_reasons: dict[str, int] = {}
    if total == 0:
        return {"malformed": False, "total": 0, "malformed_count": 0, "valid_count": 0, "reasons": {}}

    valid_count = 0
    for item in items:
        reason = ""
        if not getattr(item, "article_id", None):
            reason = "missing_id"
        elif is_malformed_listing_title(getattr(item, "title", "")):
            reason = "malformed_title"
        elif (
            getattr(item, "link", None)
            and _host_from_url(item.link) not in {"example.com", "e"}
            and not validate_platform_url(platform, item.link)
        ):
            reason = "host_mismatch"

        if reason:
            malformed_reasons[reason] = malformed_reasons.get(reason, 0) + 1
        else:
            valid_count += 1

    malformed_count = total - valid_count
    malformed_ratio = malformed_count / total if total else 0.0
    valid_ratio = valid_count / total if total else 1.0
    malformed = (
        total >= 3
        and (
            malformed_ratio >= 0.35
            or valid_ratio < 0.6
            or malformed_reasons.get("host_mismatch", 0) > 0
        )
    )
    return {
        "malformed": malformed,
        "total": total,
        "malformed_count": malformed_count,
        "valid_count": valid_count,
        "malformed_ratio": malformed_ratio,
        "valid_ratio": valid_ratio,
        "reasons": malformed_reasons,
    }


def parse_joonggonara_search_items(html: str, keyword: str, *, max_results: int = 120) -> list[Item]:
    snapshot = parse_html_snapshot(html)
    items: list[Item] = []
    seen_ids: set[str] = set()

    for anchor in snapshot.anchors:
        candidate = classify_joonggonara_candidate(anchor.attrs.get("href", ""), anchor.text)
        if not candidate:
            continue
        article_id = candidate["article_id"]
        if article_id in seen_ids:
            continue
        seen_ids.add(article_id)
        items.append(
            Item(
                platform="joonggonara",
                article_id=article_id,
                title=candidate["title"],
                price="가격문의",
                link=candidate["link"],
                keyword=keyword,
                thumbnail=None,
            )
        )
        if len(items) >= max_results:
            break

    return items


def parse_joonggonara_detail_text(text: str) -> dict[str, str | None]:
    body = str(text or "")
    lines = [normalize_whitespace(line) for line in body.splitlines() if normalize_whitespace(line)]

    def _is_meta_line(value: str) -> bool:
        cleaned = normalize_whitespace(value)
        if not cleaned:
            return True
        if cleaned.startswith("[") or cleaned.startswith("＃") or cleaned.startswith("#"):
            return True
        if cleaned in JOONGGONARA_META_EXACT:
            return True
        if any(fragment in cleaned for fragment in JOONGGONARA_META_FRAGMENTS):
            return True
        return False

    def _extract_inline_transaction_location(value: str) -> str | None:
        line = normalize_whitespace(value)
        if not line or "직거래" not in line:
            return None
        match = re.search(r"직거래(?:지역)?\s*[:：]?\s*([^\n]{1,40})", line)
        if not match:
            return None
        candidate = normalize_whitespace(match.group(1))
        candidate = re.sub(r"(에서|가능|가능하며|가능합니다|합니다|이며).*$", "", candidate).strip(" ,/")
        if not candidate:
            return None
        tokens = MICRO_LOCATION_TOKEN_RE.findall(candidate)
        if tokens:
            unique_tokens: list[str] = []
            for token in tokens:
                if token not in unique_tokens:
                    unique_tokens.append(token)
            return ",".join(unique_tokens[:2])
        return candidate

    def _extract_price_from_lines(values: list[str]) -> str | None:
        for line in values:
            if any(token in line for token in ("가격", "판매가", "희망가격", "금액")):
                amount = parse_price_kr(line)
                if amount > 0:
                    return format_price_kr(amount)
        for line in values:
            if not PRICE_CANDIDATE_RE.search(line):
                continue
            amount = parse_price_kr(line)
            if amount > 0:
                return format_price_kr(amount)
        return None

    title = None
    title_index = -1
    for index, line in enumerate(lines):
        if _is_meta_line(line):
            continue
        if is_valid_joonggonara_title(line):
            title = line
            title_index = index
            break

    price = _extract_price_from_lines(lines)

    labeled_location = extract_label_value(
        body,
        (
            "거래 희망지역",
            "거래희망지역",
            "거래 지역",
            "거래지역",
            "직거래지역",
            "직거래 지역",
            "거래 가능 지역",
            "거래가능지역",
            "지역 정보",
            "지역정보",
            "지역",
        ),
    )
    location = normalize_location_value(labeled_location) if labeled_location else None
    if not location:
        for line in lines:
            location = _extract_inline_transaction_location(line)
            if location:
                break
    if not location:
        for index, line in enumerate(lines):
            if "거래방식" not in line:
                continue
            for candidate_line in lines[index + 1 : index + 4]:
                location = _extract_inline_transaction_location(candidate_line)
                if location:
                    break
            if location:
                break

    seller = extract_label_value(body, ("판매자 정보", "판매자", "작성자", "닉네임"))
    if seller and ("협의" in seller or seller.startswith("와 ")):
        seller = None
    if not seller and title_index >= 0:
        for candidate in lines[title_index + 1 : title_index + 6]:
            if _is_meta_line(candidate) or candidate in JOONGGONARA_SELLER_NOISE:
                continue
            if PRICE_RE.search(candidate) or LOCATION_RE.search(candidate):
                continue
            if PRICE_CANDIDATE_RE.search(candidate):
                continue
            if 2 <= len(candidate) <= 20:
                seller = candidate
                break
    if seller:
        seller = normalize_whitespace(seller)

    return {
        "title": title,
        "price": price,
        "location": location,
        "seller": seller or None,
    }
