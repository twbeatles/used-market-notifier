"""Build a render context dict from a listing row."""

from typing import Mapping


def create_context_from_listing(
    listing: Mapping[str, object],
    target_price: int | None = None,
) -> dict[str, str]:
    """
    Create a context dict from a listing dict.

    Args:
        listing: Listing data dict
        target_price: Optional target price to include

    Returns:
        Context dict for template rendering
    """
    platform_names = {
        'danggeun': '당근마켓',
        'bunjang': '번개장터',
        'joonggonara': '중고나라'
    }

    platform_key_raw = listing.get('platform', '')
    platform_key = platform_key_raw if isinstance(platform_key_raw, str) else str(platform_key_raw or "")

    def _as_text(value: object, default: str = "") -> str:
        if isinstance(value, str):
            return value
        if value is None:
            return default
        return str(value)

    return {
        'title': _as_text(listing.get('title', '')),
        'price': _as_text(listing.get('price', '')),
        'seller': _as_text(listing.get('seller', '')),
        'location': _as_text(listing.get('location', '')),
        'platform': platform_names.get(platform_key, platform_key),
        'target_price': f"{target_price:,}원" if target_price is not None else '',
    }


__all__ = ["create_context_from_listing"]
