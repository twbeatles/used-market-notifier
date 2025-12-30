from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import logging


@dataclass
class Item:
    """Represents a listing item from any platform"""
    platform: str
    article_id: str
    title: str
    price: str
    link: str
    keyword: str
    thumbnail: Optional[str] = None
    seller: Optional[str] = None
    location: Optional[str] = None
    price_numeric: Optional[int] = None

    def parse_price(self) -> int:
        """Extract numeric price from price string"""
        if self.price_numeric is not None:
            return self.price_numeric
        try:
            cleaned = ''.join(c for c in self.price if c.isdigit())
            self.price_numeric = int(cleaned) if cleaned else 0
        except:
            self.price_numeric = 0
        return self.price_numeric


class BaseScraper(ABC):
    """Abstract base class for marketplace scrapers"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def search(self, keyword: str, location: str = None) -> list[Item]:
        """
        Search for the keyword on the platform and return a list of Items.
        
        Args:
            keyword: Search term
            location: Optional location filter (platform-specific)
        
        Returns:
            List of Item objects
        """
        pass

    def close(self):
        """Clean up resources (drivers, etc.)"""
        pass
    
    def filter_by_price(self, items: list[Item], min_price: int = None, max_price: int = None) -> list[Item]:
        """Filter items by price range"""
        result = []
        for item in items:
            price = item.parse_price()
            if price == 0:
                result.append(item)
                continue
            if min_price and price < min_price:
                continue
            if max_price and price > max_price:
                continue
            result.append(item)
        return result
    
    def filter_by_keywords(self, items: list[Item], exclude_keywords: list[str] = None) -> list[Item]:
        """Filter out items containing excluded keywords"""
        if not exclude_keywords:
            return items
        result = []
        for item in items:
            title_lower = item.title.lower()
            if not any(ex.lower() in title_lower for ex in exclude_keywords):
                result.append(item)
        return result
