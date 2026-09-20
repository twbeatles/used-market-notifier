"""Favorite and seller-filter models."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FavoriteItem:
    """Represents a favorited item"""
    listing_id: int
    added_at: str  # ISO format string
    notes: str = ""
    target_price: Optional[int] = None


@dataclass
class SellerFilter:
    """Filter for specific sellers"""
    seller_name: str
    platform: str
    is_blocked: bool = True
    notes: str = ""


__all__ = ["FavoriteItem", "SellerFilter"]
