# notifiers/base.py
"""Base notifier abstract class"""

from abc import ABC, abstractmethod
from typing import Optional
import logging
from models import Item


class BaseNotifier(ABC):
    """Abstract base class for all notifiers"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.enabled = False
    
    @abstractmethod
    async def send_message(self, text: str) -> bool:
        """Send a text message"""
        pass
    
    @abstractmethod
    async def send_item(self, item: Item, with_image: bool = True) -> bool:
        """Send a notification for a new item"""
        pass
    
    @abstractmethod
    async def send_price_change(self, item: Item, old_price: str, new_price: str) -> bool:
        """Send a notification for a price change"""
        pass
    
    def format_item_message(self, item: Item) -> str:
        """Format item as message text"""
        platform_emoji = {
            'danggeun': '🥕',
            'bunjang': '⚡',
            'joonggonara': '🛒'
        }
        emoji = platform_emoji.get(item.platform, '📦')
        
        lines = [
            f"{emoji} [{item.platform.upper()}] 새 상품!",
            f"",
            f"🔍 키워드: {item.keyword}",
            f"📦 제목: {item.title}",
            f"💰 가격: {item.price}",
        ]
        
        if item.location:
            lines.append(f"📍 지역: {item.location}")
        
        if item.seller:
            lines.append(f"👤 판매자: {item.seller}")
        
        lines.append(f"")
        lines.append(f"🔗 {item.link}")
        
        return "\n".join(lines)
    
    def format_price_change_message(self, item: Item, old_price: str, new_price: str) -> str:
        """Format price change notification"""
        # Determine if price went up or down
        try:
            old_num = int(''.join(c for c in old_price if c.isdigit()) or '0')
            new_num = int(''.join(c for c in new_price if c.isdigit()) or '0')
            if new_num < old_num:
                emoji = "📉"
                direction = "인하"
            else:
                emoji = "📈"
                direction = "인상"
        except Exception:
            emoji = "💱"
            direction = "변동"
        
        return (
            f"{emoji} 가격 {direction}!\n"
            f"\n"
            f"📦 {item.title}\n"
            f"💰 {old_price} → {new_price}\n"
            f"\n"
            f"🔗 {item.link}"
        )
