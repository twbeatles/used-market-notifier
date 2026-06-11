"""Protocols shared by the monitoring engine."""

from __future__ import annotations

from typing import Protocol

from models import AppSettings, Item


class SettingsProvider(Protocol):
    settings: AppSettings


class ScraperProtocol(Protocol):
    def safe_search(self, keyword: str, location: str | None = None) -> list[Item]:
        ...

    def enrich_item(self, item: Item) -> Item:
        ...

    def close(self) -> object:
        ...


class NotifierProtocol(Protocol):
    async def send_message(self, text: str) -> bool:
        ...

    async def send_item(self, item: Item, with_image: bool = True) -> bool:
        ...

    async def send_price_change(self, item: Item, old_price: str, new_price: str) -> bool:
        ...

    def get_last_delivery_result(self) -> dict:
        ...
