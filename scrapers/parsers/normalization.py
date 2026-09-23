"""Normalization helpers."""

from .common import *

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
    # 카드 문구는 "잠원동 · 7분 전"처럼 숫자와 단위가 붙어 있다.
    relative_time = r"(?:방금|끌올|\d+\s*(?:초|분|시간|일|주|달)\s*전)"
    text = re.split(rf"\s*[·|]\s*{relative_time}", text, maxsplit=1)[0]
    text = re.sub(rf"\s*{relative_time}.*$", "", text).strip()
    text = text.strip(" \t\r\n·,/|")
    if not text:
        return None
    compact = text.replace(" ", "")
    if compact in {"지역정보없음"} or text in UNKNOWN_LOCATION_TEXTS:
        return None
    if looks_like_time_line(text) or is_count_or_metric_line(text) or is_strict_price_line(text):
        return None
    return text
