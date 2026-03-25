"""Base notifier abstraction."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from models import Item


class BaseNotifier(ABC):
    """Abstract base class for all notifiers."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.enabled = False
        self._last_delivery_result = {
            "success": False,
            "error_message": None,
            "rate_limited": False,
        }

    @abstractmethod
    async def send_message(self, text: str) -> bool:
        """Send a text message."""

    @abstractmethod
    async def send_item(self, item: Item, with_image: bool = True) -> bool:
        """Send a notification for a new item."""

    @abstractmethod
    async def send_price_change(self, item: Item, old_price: str, new_price: str) -> bool:
        """Send a notification for a price change."""

    def format_item_message(self, item: Item) -> str:
        """Format an item notification message."""
        lines = [
            f"[{item.platform.upper()}] New item",
            "",
            f"Keyword: {item.keyword}",
            f"Title: {item.title}",
            f"Price: {item.price}",
        ]

        if item.location:
            lines.append(f"Location: {item.location}")
        if item.seller:
            lines.append(f"Seller: {item.seller}")

        lines.extend(["", f"Link: {item.link}"])
        return "\n".join(lines)

    def format_price_change_message(self, item: Item, old_price: str, new_price: str) -> str:
        """Format a price-change notification message."""
        try:
            old_num = int("".join(c for c in old_price if c.isdigit()) or "0")
            new_num = int("".join(c for c in new_price if c.isdigit()) or "0")
            label = "Price down" if new_num < old_num else "Price up"
        except Exception:
            label = "Price changed"

        return (
            f"{label}\n\n"
            f"Title: {item.title}\n"
            f"Price: {old_price} -> {new_price}\n\n"
            f"Link: {item.link}"
        )

    def _set_delivery_result(
        self,
        success: bool,
        error_message: str | None = None,
        rate_limited: bool = False,
    ) -> None:
        self._last_delivery_result = {
            "success": bool(success),
            "error_message": error_message,
            "rate_limited": bool(rate_limited),
        }

    def get_last_delivery_result(self) -> dict:
        """Return the most recent delivery outcome."""
        return dict(self._last_delivery_result)
