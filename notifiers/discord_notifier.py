"""Discord webhook notification handler."""

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


class DiscordNotifier(BaseNotifier):
    """Discord webhook notifier with embeds."""

    def __init__(self, webhook_url: str):
        super().__init__()
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)

    async def _send_webhook(self, payload: dict, max_retries: int = 3) -> bool:
        if not self.enabled:
            self._set_delivery_result(False, "discord notifier disabled")
            return False
        if aiohttp is None:
            self.logger.error("aiohttp is not installed; Discord notifier is unavailable")
            self._set_delivery_result(False, "aiohttp is not installed")
            return False

        last_error = "request failed"
        rate_limited = False

        for attempt in range(max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(self.webhook_url, json=payload) as response:
                        if response.status in (200, 204):
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
                            if retry_after is None:
                                try:
                                    data = await response.json(content_type=None)
                                    delay = data.get("retry_after")
                                    if isinstance(delay, (int, float)):
                                        retry_after = float(delay)
                                except Exception:
                                    retry_after = None
                            last_error = f"HTTP 429 {body[:300]}".strip()
                            if retry_after is not None and attempt < max_retries - 1:
                                self.logger.warning(f"Discord rate limited. Retrying after {retry_after:.1f}s.")
                                await asyncio.sleep(retry_after)
                                continue
                        elif response.status >= 500 and attempt < max_retries - 1:
                            last_error = f"HTTP {response.status} {body[:300]}".strip()
                            await asyncio.sleep(float(attempt + 1))
                            continue
                        else:
                            last_error = f"HTTP {response.status} {body[:300]}".strip()

                        self.logger.warning(f"Discord webhook failed: {last_error}")
                        self._set_delivery_result(False, last_error, rate_limited=rate_limited)
                        return False
            except asyncio.TimeoutError:
                last_error = f"timeout on attempt {attempt + 1}/{max_retries}"
                self.logger.warning(f"Discord request {last_error}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(float(attempt + 1))
                    continue
            except _AIOHTTP_CLIENT_ERROR as e:
                last_error = f"connection error: {e}"
                self.logger.warning(f"Discord {last_error}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(float(attempt + 1))
                    continue
            except Exception as e:
                last_error = str(e)
                self.logger.error(f"Discord webhook error: {e}")
                self._set_delivery_result(False, last_error, rate_limited=rate_limited)
                return False

        self._set_delivery_result(False, last_error, rate_limited=rate_limited)
        return False

    async def send_message(self, text: str) -> bool:
        return await self._send_webhook({"content": text})

    async def send_item(self, item: Item, with_image: bool = True) -> bool:
        platform_colors = {
            "danggeun": 0xFF6F00,
            "bunjang": 0x7B68EE,
            "joonggonara": 0x00C853,
        }
        embed = {
            "title": f"New item: {item.title}",
            "url": item.link,
            "color": platform_colors.get(item.platform, 0x5865F2),
            "fields": [
                {"name": "Price", "value": item.price, "inline": True},
                {"name": "Keyword", "value": item.keyword, "inline": True},
                {"name": "Platform", "value": item.platform.upper(), "inline": True},
            ],
            "footer": {"text": "Used Market Notifier"},
        }

        if item.location:
            embed["fields"].append({"name": "Location", "value": item.location, "inline": True})
        if item.seller:
            embed["fields"].append({"name": "Seller", "value": item.seller, "inline": True})
        if with_image and item.thumbnail:
            embed["thumbnail"] = {"url": item.thumbnail}

        return await self._send_webhook({"embeds": [embed]})

    async def send_price_change(self, item: Item, old_price: str, new_price: str) -> bool:
        try:
            old_num = int("".join(ch for ch in old_price if ch.isdigit()) or "0")
            new_num = int("".join(ch for ch in new_price if ch.isdigit()) or "0")
            color = 0x00C853 if new_num < old_num else 0xFF5252
            label = "Price down" if new_num < old_num else "Price up"
        except Exception:
            color = 0xFFC107
            label = "Price changed"

        embed = {
            "title": f"{label}: {item.title}",
            "url": item.link,
            "color": color,
            "fields": [
                {"name": "Old price", "value": old_price, "inline": True},
                {"name": "Current price", "value": new_price, "inline": True},
            ],
            "footer": {"text": "Used Market Notifier"},
        }
        if item.thumbnail:
            embed["thumbnail"] = {"url": item.thumbnail}
        return await self._send_webhook({"embeds": [embed]})
