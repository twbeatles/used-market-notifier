"""Scrape quality helpers."""

from .common import *
from .urls import _host_from_url
from .normalization import is_malformed_listing_title
from .urls import validate_platform_url

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
