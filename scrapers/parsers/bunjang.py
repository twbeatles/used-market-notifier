"""Bunjang parser helpers."""

from .common import *
from .html_snapshot import parse_html_snapshot
from .metadata import _first_non_empty, _lookup_path, normalize_sale_status
from .metadata import merge_item_metadata
from .normalization import is_count_or_metric_line, is_malformed_listing_title, is_strict_price_line, looks_like_time_line, normalize_location_value, normalize_price_text, normalize_whitespace
from .urls import extract_bunjang_product_id, normalize_url_for_match, validate_platform_url

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
