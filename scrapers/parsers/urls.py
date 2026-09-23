"""Marketplace URL helpers."""

from urllib.parse import quote

from .common import *


def build_danggeun_search_url(keyword: str, region_slug: str | None = None) -> str:
    """당근 중고거래 검색 URL.

    2026-09 기준 매물이 있는 경로는 `/kr/search/buy-sell/?q=` 이다.
    `region_slug` 가 있으면 `in=역삼동-6035` 처럼 검색 중심 지역을 붙입니다.
    """
    encoded = quote(str(keyword or "").strip())
    url = f"https://www.daangn.com/kr/search/buy-sell/?q={encoded}"
    slug = str(region_slug or "").strip()
    if slug:
        url += f"&in={quote(slug)}"
    return url

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
