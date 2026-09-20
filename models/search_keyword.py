"""Search keyword model with per-keyword filters."""

from dataclasses import dataclass, field
from typing import Optional

from .item import Item


@dataclass
class SearchKeyword:
    """Represents a search keyword with filters"""
    keyword: str
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    location: Optional[str] = None
    exclude_keywords: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=lambda: ["danggeun", "bunjang", "joonggonara"])
    enabled: bool = True
    group_name: Optional[str] = None
    custom_interval: Optional[int] = None
    target_price: Optional[int] = None
    notify_enabled: bool = True  # Per-keyword notification toggle

    def matches_price(self, item: Item) -> bool:
        """Check if item price is within range"""
        price = item.parse_price()
        if price == 0:
            return True  # Allow items with unknown price
        if self.min_price and price < self.min_price:
            return False
        if self.max_price and price > self.max_price:
            return False
        return True

    def matches_location(self, item: Item) -> bool:
        """Check if item location matches filter"""
        if not self.location:
            return True

        item_platform = (item.platform or "").lower()
        # Danggeun location filtering is strict: unknown location should not pass.
        if item_platform == "danggeun":
            if not item.location:
                return False
            return self.location.lower() in item.location.lower()

        # Other platforms keep best-effort behavior.
        if not item.location:
            return True
        return self.location.lower() in item.location.lower()

    def has_excluded_words(self, item: Item) -> bool:
        """Check if item contains excluded keywords"""
        if not self.exclude_keywords:
            return False
        title_lower = item.title.lower()
        return any(ex.lower() in title_lower for ex in self.exclude_keywords)

    def matches(self, item: Item) -> bool:
        """Check if item passes all filters"""
        return (
            self.matches_price(item) and
            self.matches_location(item) and
            not self.has_excluded_words(item)
        )


__all__ = ["SearchKeyword"]
