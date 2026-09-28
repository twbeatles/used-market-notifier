"""Listing item model."""

from dataclasses import dataclass, field
from typing import Optional

from price_utils import parse_price_kr


@dataclass
class Item:
    """Represents a listing item from any platform"""
    platform: str
    article_id: str
    title: str
    price: str
    link: str
    keyword: str
    thumbnail: Optional[str] = None
    seller: Optional[str] = None
    location: Optional[str] = None
    sale_status: Optional[str] = None
    price_numeric: Optional[int] = None  # Parsed price for filtering
    # 엔진이 알림을 억제한 신규 매물(기준선 수집 등). UI 트레이 알림 판단용이며 저장되지 않음.
    notification_suppressed: bool = field(default=False, compare=False, repr=False)

    def parse_price(self) -> int:
        """Extract numeric price from price string"""
        if self.price_numeric is not None:
            return self.price_numeric
        self.price_numeric = parse_price_kr(self.price)
        return self.price_numeric


__all__ = ["Item"]
