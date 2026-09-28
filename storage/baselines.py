from typing import TYPE_CHECKING
# pyright: reportAttributeAccessIssue=false
"""Search baseline / listing last-seen persistence for DatabaseManager."""

from .common import *


if TYPE_CHECKING:
    from storage.database import DatabaseManager
    _HostBase_BaselineMixin = DatabaseManager
else:
    _HostBase_BaselineMixin = object


def _norm(value: Any) -> str:
    return " ".join(str(value or "").split()).lower()


def keyword_search_signature(keyword_config: Any) -> str:
    """키워드 검색 조건 서명 (검색어·지역·가격 범위·제외어).

    조건이 바뀌면 서명이 달라져 새 기준선이 필요해집니다.
    """
    exclude = getattr(keyword_config, "exclude_keywords", None) or []
    parts = [
        _norm(getattr(keyword_config, "keyword", "")),
        _norm(getattr(keyword_config, "location", "")),
        str(int(getattr(keyword_config, "min_price", 0) or 0)),
        str(int(getattr(keyword_config, "max_price", 0) or 0)),
        ",".join(sorted(_norm(x) for x in exclude if _norm(x))),
    ]
    return "|".join(parts)


class SearchBaselineMixin(_HostBase_BaselineMixin):
    """(검색 조건 서명, 플랫폼) 단위 알림 기준선."""

    def has_search_baseline(self, signature: str, platform: str) -> bool:
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT 1 FROM search_baselines WHERE signature = ? AND platform = ?",
                (signature, platform),
            )
            return cursor.fetchone() is not None

    def establish_search_baseline(self, signature: str, platform: str) -> None:
        with self.lock:
            self.conn.execute(
                "INSERT OR IGNORE INTO search_baselines (signature, platform) VALUES (?, ?)",
                (signature, platform),
            )
            self.conn.commit()


class ListingSeenMixin(_HostBase_BaselineMixin):
    """매물을 마지막으로 검색 결과에서 본 시각 (정리 기준)."""

    def touch_listings_seen(self, listing_ids: list[int]) -> None:
        ids = sorted({int(i) for i in listing_ids if i is not None})
        if not ids:
            return
        with self.lock:
            self.conn.executemany(
                """
                INSERT INTO listing_last_seen (listing_id, last_seen_at)
                VALUES (?, CURRENT_TIMESTAMP)
                ON CONFLICT(listing_id) DO UPDATE SET last_seen_at = CURRENT_TIMESTAMP
                """,
                [(i,) for i in ids],
            )
            self.conn.commit()


__all__ = ["SearchBaselineMixin", "ListingSeenMixin", "keyword_search_signature"]
