"""Pure parsing helpers shared across marketplace scrapers and tests."""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, Iterable
from urllib.parse import parse_qs, urlsplit

from models import Item

UNKNOWN_LOCATION_TEXTS = {"지역정보 없음", "지역 정보 없음"}
TIME_TEXT_RE = re.compile(r"^(?:\d+:)?\d{1,2}:\d{2}$")
URL_ONLY_RE = re.compile(r"^(?:https?://|www\.)\S+$", re.IGNORECASE)
QUESTION_ONLY_RE = re.compile(r"^[\s\?？!~·]+$")
PRICE_RE = re.compile(r"(\d{1,3}(?:,\d{3})+|\d{2,9})\s*원")
LOCATION_RE = re.compile(
    r"(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)[^\n|,/]{0,24}"
)


@dataclass
class HtmlAnchorSnapshot:
    attrs: dict[str, str]
    text: str
    image: str | None = None


@dataclass
class HtmlDocumentSnapshot:
    anchors: list[HtmlAnchorSnapshot]
    ld_json_scripts: list[str]


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


def normalize_location_value(value: Any) -> str | None:
    text = normalize_whitespace(str(value or ""))
    if not text:
        return None
    compact = text.replace(" ", "")
    if compact in {"지역정보없음"} or text in UNKNOWN_LOCATION_TEXTS:
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


def extract_numeric_article_id(link: str) -> str | None:
    if not link:
        return None
    try:
        parts = urlsplit(link)
        qs = parse_qs(parts.query or "")
        article_ids = qs.get("articleid") or qs.get("articleId") or qs.get("articleID")
        if article_ids and article_ids[0]:
            match = re.search(r"(\d+)", str(article_ids[0]))
            if match:
                return match.group(1)
    except Exception:
        pass

    match = re.search(r"/joonggonara/(\d+)(?:[/?#]|$)", link)
    if match:
        return match.group(1)
    match = re.search(r"/(\d+)(?:[/?#]|$)", link)
    if match and "cafe.naver.com" in link:
        return match.group(1)
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
    if "cafe.naver.com/joonggonara" in lowered:
        return False
    if any(marker in lowered for marker in ("판매완료", "예약중", "거래완료", "no title", "광고", "배송비포함")):
        return False
    if not re.search(r"[0-9a-z가-힣]", lowered):
        return False
    return True


def classify_joonggonara_candidate(link: str, text: str) -> dict[str, str] | None:
    normalized_link = str(link or "").strip()
    if not normalized_link or "cafe.naver.com" not in normalized_link or "joonggonara" not in normalized_link:
        return None
    article_id = extract_numeric_article_id(normalized_link)
    if not article_id:
        return None

    first_line = next((line.strip() for line in str(text or "").splitlines() if line.strip()), "")
    title = normalize_whitespace(first_line)
    if not is_valid_joonggonara_title(title):
        return None

    return {"article_id": article_id, "title": title, "link": normalized_link}


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
    ignored_fragments = (
        "게시판 목록",
        "목록",
        "본문 바로가기",
        "카페홈",
        "이전글",
        "다음글",
        "구매문의",
        "URL 복사",
        "조회",
        "댓글",
        "중고나라 회원",
        "판매 완료",
        "거래 시 꼭 알아주세요",
        "디지털/가전",
    )

    title = None
    title_index = -1
    for index, line in enumerate(lines):
        if any(fragment in line for fragment in ignored_fragments):
            continue
        if line.startswith("["):
            continue
        if is_valid_joonggonara_title(line):
            title = line
            title_index = index
            break

    labeled_price = extract_label_value(body, ("가격", "판매가", "희망가격", "금액"))
    raw_price = labeled_price
    if raw_price and not re.search(r"\d", raw_price):
        raw_price = None
    if not raw_price:
        match = PRICE_RE.search(body)
        raw_price = match.group(0) if match else None
    price = normalize_price_text(raw_price) if raw_price else None

    labeled_location = extract_label_value(body, ("거래 희망지역", "거래희망지역", "거래 지역", "거래지역", "지역 정보", "지역정보", "지역"))
    location = normalize_location_value(labeled_location) if labeled_location else None
    seller = extract_label_value(body, ("판매자 정보", "판매자", "작성자", "닉네임"))
    if seller and ("협의" in seller or seller.startswith("와 ")):
        seller = None
    if not seller and title_index >= 0:
        for candidate in lines[title_index + 1 : title_index + 6]:
            if any(fragment in candidate for fragment in ignored_fragments):
                continue
            if PRICE_RE.search(candidate) or LOCATION_RE.search(candidate):
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
