from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import logging
import sys
import os

# Add parent directory to path for models import
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import Item from models - single source of truth
from models import Item


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

    def safe_search(self, keyword: str, location: str = None) -> list[Item]:
        """
        Safe wrapper around search that handles exceptions gracefully.
        Returns empty list on error instead of raising.
        """
        try:
            return self.search(keyword, location)
        except Exception as e:
            self.logger.error(f"Search failed for '{keyword}': {e}")
            return []

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
