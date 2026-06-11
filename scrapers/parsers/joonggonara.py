"""Joonggonara parser helpers."""

from .common import *
from .html_snapshot import parse_html_snapshot
from .metadata import extract_label_value, extract_location_from_text
from .normalization import normalize_location_value, normalize_multiline_text, normalize_price_text, normalize_whitespace
from .urls import extract_numeric_article_id, normalize_url_for_match, validate_platform_url

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
