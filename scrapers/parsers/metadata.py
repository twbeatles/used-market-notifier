"""Listing metadata helpers."""

from .common import *
from .normalization import normalize_location_value, normalize_price_text

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
