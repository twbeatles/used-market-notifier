# notifiers/slack_notifier.py
"""Slack webhook notification handler"""

import aiohttp
from typing import Optional
import sys
sys.path.insert(0, '..')
from models import Item
from .base import BaseNotifier


class SlackNotifier(BaseNotifier):
    """Slack Incoming Webhook notifier with Block Kit"""
    
    def __init__(self, webhook_url: str):
        super().__init__()
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)
    
    async def _send_webhook(self, payload: dict) -> bool:
        """Send webhook request to Slack"""
        if not self.enabled:
            return False
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as resp:
                    return resp.status == 200
        except Exception as e:
            self.logger.error(f"Slack webhook error: {e}")
            return False
    
    async def send_message(self, text: str) -> bool:
        """Send simple text message"""
        return await self._send_webhook({"text": text})
    
    async def send_item(self, item: Item, with_image: bool = True) -> bool:
        """Send Block Kit message for new item"""
        platform_emoji = {
            'danggeun': ':carrot:',
            'bunjang': ':zap:',
            'joonggonara': ':shopping_trolley:'
        }
        emoji = platform_emoji.get(item.platform, ':package:')
        
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{emoji} 새 상품 알림!", "emoji": True}
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{item.link}|{item.title}>*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*💰 가격:*\n{item.price}"},
                    {"type": "mrkdwn", "text": f"*🔍 키워드:*\n{item.keyword}"},
                    {"type": "mrkdwn", "text": f"*📦 플랫폼:*\n{item.platform.upper()}"},
                ]
            }
        ]
        
        # Add location and seller if available
        extra_fields = []
        if item.location:
            extra_fields.append({"type": "mrkdwn", "text": f"*📍 지역:*\n{item.location}"})
        if item.seller:
            extra_fields.append({"type": "mrkdwn", "text": f"*👤 판매자:*\n{item.seller}"})
        
        if extra_fields:
            blocks.append({
                "type": "section",
                "fields": extra_fields
            })
        
        # Add thumbnail if available
        if with_image and item.thumbnail:
            blocks[1]["accessory"] = {
                "type": "image",
                "image_url": item.thumbnail,
                "alt_text": item.title
            }
        
        blocks.append({"type": "divider"})
        
        return await self._send_webhook({"blocks": blocks})
    
    async def send_price_change(self, item: Item, old_price: str, new_price: str) -> bool:
        """Send price change notification"""
        try:
            old_num = int(''.join(c for c in old_price if c.isdigit()) or '0')
            new_num = int(''.join(c for c in new_price if c.isdigit()) or '0')
            emoji = ":chart_with_downwards_trend:" if new_num < old_num else ":chart_with_upwards_trend:"
            direction = "인하" if new_num < old_num else "인상"
        except:
            emoji = ":money_with_wings:"
            direction = "변동"
        
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{emoji} 가격 {direction}!", "emoji": True}
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{item.link}|{item.title}>*\n`{old_price}` → `{new_price}`"
                }
            },
            {"type": "divider"}
        ]
        
        if item.thumbnail:
            blocks[1]["accessory"] = {
                "type": "image",
                "image_url": item.thumbnail,
                "alt_text": item.title
            }
        
        return await self._send_webhook({"blocks": blocks})
