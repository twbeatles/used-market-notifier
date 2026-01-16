# notifiers/discord_notifier.py
"""Discord webhook notification handler"""

import aiohttp
from typing import Optional
from models import Item
from .base import BaseNotifier


class DiscordNotifier(BaseNotifier):
    """Discord Webhook notifier with rich embeds"""
    
    def __init__(self, webhook_url: str):
        super().__init__()
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)
    
    async def _send_webhook(self, payload: dict, max_retries: int = 3) -> bool:
        """Send webhook request to Discord with retry logic"""
        if not self.enabled:
            return False
        
        import asyncio
        
        for attempt in range(max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(self.webhook_url, json=payload) as resp:
                        if resp.status in (200, 204):
                            return True
                        elif resp.status >= 500:  # Server error, retry
                            if attempt < max_retries - 1:
                                await asyncio.sleep(1.0 * (attempt + 1))
                                continue
                        return False
            except asyncio.TimeoutError:
                self.logger.warning(f"Discord request timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                return False
            except aiohttp.ClientError as e:
                self.logger.warning(f"Discord connection error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                return False
            except Exception as e:
                self.logger.error(f"Discord webhook error: {e}")
                return False
        
        return False
    
    async def send_message(self, text: str) -> bool:
        """Send simple text message"""
        return await self._send_webhook({"content": text})
    
    async def send_item(self, item: Item, with_image: bool = True) -> bool:
        """Send rich embed for new item"""
        platform_colors = {
            'danggeun': 0xFF6F00,  # Orange
            'bunjang': 0x7B68EE,   # Purple
            'joonggonara': 0x00C853  # Green
        }
        
        embed = {
            "title": f"🆕 {item.title}",
            "url": item.link,
            "color": platform_colors.get(item.platform, 0x5865F2),
            "fields": [
                {"name": "💰 가격", "value": item.price, "inline": True},
                {"name": "🔍 키워드", "value": item.keyword, "inline": True},
                {"name": "📦 플랫폼", "value": item.platform.upper(), "inline": True},
            ],
            "footer": {"text": "중고거래 알리미"}
        }
        
        if item.location:
            embed["fields"].append({"name": "📍 지역", "value": item.location, "inline": True})
        
        if item.seller:
            embed["fields"].append({"name": "👤 판매자", "value": item.seller, "inline": True})
        
        if with_image and item.thumbnail:
            embed["thumbnail"] = {"url": item.thumbnail}
        
        return await self._send_webhook({"embeds": [embed]})
    
    async def send_price_change(self, item: Item, old_price: str, new_price: str) -> bool:
        """Send price change notification"""
        # Determine direction
        try:
            old_num = int(''.join(c for c in old_price if c.isdigit()) or '0')
            new_num = int(''.join(c for c in new_price if c.isdigit()) or '0')
            color = 0x00C853 if new_num < old_num else 0xFF5252  # Green if down, red if up
            emoji = "📉" if new_num < old_num else "📈"
        except (ValueError, TypeError):
            color = 0xFFC107
            emoji = "💱"
        
        embed = {
            "title": f"{emoji} 가격 변동: {item.title}",
            "url": item.link,
            "color": color,
            "fields": [
                {"name": "이전 가격", "value": old_price, "inline": True},
                {"name": "→", "value": "→", "inline": True},
                {"name": "현재 가격", "value": new_price, "inline": True},
            ],
            "footer": {"text": "중고거래 알리미"}
        }
        
        if item.thumbnail:
            embed["thumbnail"] = {"url": item.thumbnail}
        
        return await self._send_webhook({"embeds": [embed]})
