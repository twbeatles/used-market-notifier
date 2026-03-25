"""Slack webhook notification handler."""

from __future__ import annotations

import asyncio
from importlib import import_module

from models import Item

from .base import BaseNotifier


def _load_aiohttp():
    try:
        return import_module("aiohttp")
    except Exception:
        return None


aiohttp = _load_aiohttp()
_AIOHTTP_CLIENT_ERROR = getattr(aiohttp, "ClientError", Exception) if aiohttp else Exception


class SlackNotifier(BaseNotifier):
    """Slack Incoming Webhook notifier with Block Kit."""

    def __init__(self, webhook_url: str):
        super().__init__()
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)

    async def _send_webhook(self, payload: dict, max_retries: int = 3) -> bool:
        if not self.enabled:
            self._set_delivery_result(False, "slack notifier disabled")
            return False
        if aiohttp is None:
            self.logger.error("aiohttp is not installed; Slack notifier is unavailable")
            self._set_delivery_result(False, "aiohttp is not installed")
            return False

        last_error = "request failed"
        rate_limited = False

        for attempt in range(max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(self.webhook_url, json=payload) as response:
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
                            retry_after = None
                            try:
                                header_value = response.headers.get("Retry-After")
                                if header_value:
                                    retry_after = float(header_value)
                            except Exception:
                                retry_after = None
                            last_error = f"HTTP 429 {body[:300]}".strip()
                            if retry_after is not None and attempt < max_retries - 1:
                                self.logger.warning(f"Slack rate limited. Retrying after {retry_after:.1f}s.")
                                await asyncio.sleep(retry_after)
                                continue
                        elif response.status >= 500 and attempt < max_retries - 1:
                            last_error = f"HTTP {response.status} {body[:300]}".strip()
                            await asyncio.sleep(float(attempt + 1))
                            continue
                        else:
                            last_error = f"HTTP {response.status} {body[:300]}".strip()

                        self.logger.warning(f"Slack webhook failed: {last_error}")
                        self._set_delivery_result(False, last_error, rate_limited=rate_limited)
                        return False
            except asyncio.TimeoutError:
                last_error = f"timeout on attempt {attempt + 1}/{max_retries}"
                self.logger.warning(f"Slack request {last_error}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(float(attempt + 1))
                    continue
            except _AIOHTTP_CLIENT_ERROR as e:
                last_error = f"connection error: {e}"
                self.logger.warning(f"Slack {last_error}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(float(attempt + 1))
                    continue
            except Exception as e:
                last_error = str(e)
                self.logger.error(f"Slack webhook error: {e}")
                self._set_delivery_result(False, last_error, rate_limited=rate_limited)
                return False

        self._set_delivery_result(False, last_error, rate_limited=rate_limited)
        return False

    async def send_message(self, text: str) -> bool:
        return await self._send_webhook({"text": text})

    async def send_item(self, item: Item, with_image: bool = True) -> bool:
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "New item alert", "emoji": True},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*<{item.link}|{item.title}>*"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Price*\n{item.price}"},
                    {"type": "mrkdwn", "text": f"*Keyword*\n{item.keyword}"},
                    {"type": "mrkdwn", "text": f"*Platform*\n{item.platform.upper()}"},
                ],
            },
        ]

        extra_fields = []
        if item.location:
            extra_fields.append({"type": "mrkdwn", "text": f"*Location*\n{item.location}"})
        if item.seller:
            extra_fields.append({"type": "mrkdwn", "text": f"*Seller*\n{item.seller}"})
        if extra_fields:
            blocks.append({"type": "section", "fields": extra_fields})

        if with_image and item.thumbnail:
            blocks[1]["accessory"] = {
                "type": "image",
                "image_url": item.thumbnail,
                "alt_text": item.title,
            }

        blocks.append({"type": "divider"})
        return await self._send_webhook({"blocks": blocks})

    async def send_price_change(self, item: Item, old_price: str, new_price: str) -> bool:
        try:
            old_num = int("".join(ch for ch in old_price if ch.isdigit()) or "0")
            new_num = int("".join(ch for ch in new_price if ch.isdigit()) or "0")
            direction = "Price down" if new_num < old_num else "Price up"
        except Exception:
            direction = "Price changed"

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": direction, "emoji": True},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{item.link}|{item.title}>*\n`{old_price}` -> `{new_price}`",
                },
            },
            {"type": "divider"},
        ]

        if item.thumbnail:
            blocks[1]["accessory"] = {
                "type": "image",
                "image_url": item.thumbnail,
                "alt_text": item.title,
            }

        return await self._send_webhook({"blocks": blocks})
