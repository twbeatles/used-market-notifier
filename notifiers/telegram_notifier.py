# notifiers/telegram_notifier.py
"""Telegram notification handler"""

import asyncio
import aiohttp
from typing import Optional
from models import Item
from .base import BaseNotifier


class TelegramNotifier(BaseNotifier):
    """Telegram Bot API notifier with image support"""
    
    API_BASE = "https://api.telegram.org/bot"
    
    def __init__(self, token: str, chat_id: str):
        super().__init__()
        self.token = token
        self.chat_id = chat_id
        self.enabled = bool(token and chat_id)
    
    async def _request(self, method: str, data: dict = None, files: dict = None, max_retries: int = 3) -> bool:
        """Make API request to Telegram with retry logic"""
        url = f"{self.API_BASE}{self.token}/{method}"
        
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
                        async with session.post(url, data=form) as resp:
                            if resp.status == 200:
                                return True
                            elif resp.status >= 500:  # Server error, retry
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(1.0 * (attempt + 1))
                                    continue
                            return False
                    else:
                        async with session.post(url, json=data) as resp:
                            if resp.status == 200:
                                return True
                            elif resp.status >= 500:  # Server error, retry
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(1.0 * (attempt + 1))
                                    continue
                            return False
            except asyncio.TimeoutError:
                self.logger.warning(f"Telegram request timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                return False
            except aiohttp.ClientError as e:
                self.logger.warning(f"Telegram connection error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                return False
            except Exception as e:
                self.logger.error(f"Telegram API error: {e}")
                return False
        
        return False
    
    async def send_message(self, text: str) -> bool:
        """Send text message"""
        if not self.enabled:
            return False
        return await self._request("sendMessage", {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        })
    
    async def send_photo(self, photo_url: str, caption: str) -> bool:
        """Send photo with caption"""
        if not self.enabled:
            return False
        return await self._request("sendPhoto", {
            "chat_id": self.chat_id,
            "photo": photo_url,
            "caption": caption,
            "parse_mode": "HTML"
        })
    
    async def send_item(self, item: Item, with_image: bool = True) -> bool:
        """Send item notification, optionally with thumbnail"""
        if not self.enabled:
            return False
        
        message = self.format_item_message(item)
        
        if with_image and item.thumbnail:
            try:
                success = await self.send_photo(item.thumbnail, message)
                if success:
                    return True
            except Exception as e:
                self.logger.warning(f"Failed to send image, falling back to text: {e}")
        
        return await self.send_message(message)
    
    async def send_price_change(self, item: Item, old_price: str, new_price: str) -> bool:
        """Send price change notification"""
        if not self.enabled:
            return False
        message = self.format_price_change_message(item, old_price, new_price)
        return await self.send_message(message)
