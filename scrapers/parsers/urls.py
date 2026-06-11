"""Marketplace URL helpers."""

from .common import *

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
