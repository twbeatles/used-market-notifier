"""Telegram notification handler."""

from __future__ import annotations

import asyncio
from importlib import import_module
from typing import Any, Mapping, Optional

from models import Item

from .base import BaseNotifier


def _load_aiohttp():
    try:
        return import_module("aiohttp")
    except Exception:
        return None


aiohttp = _load_aiohttp()
_AIOHTTP_CLIENT_ERROR = getattr(aiohttp, "ClientError", Exception) if aiohttp else Exception


class TelegramNotifier(BaseNotifier):
    """Telegram Bot API notifier with image support."""

    API_BASE = "https://api.telegram.org/bot"
    MAX_MESSAGE_LEN = 4096
    MAX_CAPTION_LEN = 1024

    def __init__(self, token: str, chat_id: str):
        super().__init__()
        self.token = token
        self.chat_id = chat_id
        self.enabled = bool(token and chat_id)

    @staticmethod
    def _truncate(text: str, limit: int) -> str:
        value = str(text or "")
        if len(value) <= limit:
            return value
        if limit <= 3:
            return value[:limit]
        return value[: limit - 3] + "..."

    async def _read_telegram_retry_after(self, response: Any) -> Optional[int]:
        try:
            data = await response.json(content_type=None)
            params = data.get("parameters") or {}
            retry_after = params.get("retry_after")
            if isinstance(retry_after, int) and retry_after > 0:
                return retry_after
        except Exception:
            return None
        return None

    async def _request(
        self,
        method: str,
        data: Mapping[str, Any] | None = None,
        files: Mapping[str, Any] | None = None,
        max_retries: int = 3,
    ) -> bool:
        """Make an API request to Telegram with retry logic."""
        if not self.enabled:
            self._set_delivery_result(False, "telegram notifier disabled")
            return False
        if aiohttp is None:
            self.logger.error("aiohttp is not installed; Telegram notifier is unavailable")
            self._set_delivery_result(False, "aiohttp is not installed")
            return False

        url = f"{self.API_BASE}{self.token}/{method}"
        last_error = "request failed"
        rate_limited = False

        for attempt in range(max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    if files:
                        form = aiohttp.FormData()
                        for key, value in (data or {}).items():
                            form.add_field(key, str(value))
                        for key, value in files.items():
                            form.add_field(key, value)
                        request_ctx = session.post(url, data=form)
                    else:
                        request_ctx = session.post(url, json=data)

                    async with request_ctx as response:
                        if response.status == 200:
                            self._set_delivery_result(True)
                            return True

                        body = ""
                        try:
                            body = await response.text()
                        except Exception:
                            body = ""

                        if response.status == 429:
                            rate_limited = True
                            retry_after = await self._read_telegram_retry_after(response)
                            last_error = f"HTTP 429 {body[:300]}".strip()
                            if retry_after and attempt < max_retries - 1:
                                self.logger.warning(f"Telegram rate limited. Retrying after {retry_after}s.")
                                await asyncio.sleep(retry_after)
                                continue
                        elif response.status >= 500 and attempt < max_retries - 1:
                            last_error = f"HTTP {response.status} {body[:300]}".strip()
                            await asyncio.sleep(float(attempt + 1))
                            continue
                        else:
                            last_error = f"HTTP {response.status} {body[:300]}".strip()

                        self.logger.warning(f"Telegram API failed: {last_error}")
                        self._set_delivery_result(False, last_error, rate_limited=rate_limited)
                        return False
            except asyncio.TimeoutError:
                last_error = f"timeout on attempt {attempt + 1}/{max_retries}"
                self.logger.warning(f"Telegram request {last_error}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(float(attempt + 1))
                    continue
            except _AIOHTTP_CLIENT_ERROR as e:
                last_error = f"connection error: {e}"
                self.logger.warning(f"Telegram {last_error}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(float(attempt + 1))
                    continue
            except Exception as e:
                last_error = str(e)
                self.logger.error(f"Telegram API error: {e}")
                self._set_delivery_result(False, last_error, rate_limited=rate_limited)
                return False

        self._set_delivery_result(False, last_error, rate_limited=rate_limited)
        return False

    async def send_message(self, text: str) -> bool:
        """Send a text message."""
        message = self._truncate(text, self.MAX_MESSAGE_LEN)
        return await self._request(
            "sendMessage",
            {
                "chat_id": self.chat_id,
                "text": message,
                "disable_web_page_preview": False,
            },
        )

    async def send_photo(self, photo_url: str, caption: str) -> bool:
        """Send a photo with caption."""
        return await self._request(
            "sendPhoto",
            {
                "chat_id": self.chat_id,
                "photo": photo_url,
                "caption": self._truncate(caption, self.MAX_CAPTION_LEN),
            },
        )

    async def send_item(self, item: Item, with_image: bool = True) -> bool:
        """Send item notification, optionally with a thumbnail."""
        if not self.enabled:
            self._set_delivery_result(False, "telegram notifier disabled")
            return False

        message = self.format_item_message(item)
        if with_image and item.thumbnail:
            try:
                success = await self.send_photo(item.thumbnail, message)
                if success:
                    return True
            except Exception as e:
                self.logger.warning(f"Failed to send Telegram photo, falling back to text: {e}")

        return await self.send_message(message)

    async def send_price_change(self, item: Item, old_price: str, new_price: str) -> bool:
        """Send price change notification."""
        if not self.enabled:
            self._set_delivery_result(False, "telegram notifier disabled")
            return False
        return await self.send_message(self.format_price_change_message(item, old_price, new_price))
