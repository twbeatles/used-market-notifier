from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import logging

# Import Item from models - single source of truth
from models import Item


class BaseScraper(ABC):
    """Abstract base class for marketplace scrapers"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def normalize_price(price_str: str) -> str:
        """가격 문자열 정규화: '10,000원' 형식으로 통일"""
        import re
        if not price_str:
            return "가격문의"
        clean = re.sub(r'[^\d]', '', str(price_str))
        if clean and clean != '0':
            return f"{int(clean):,}원"
        return "가격문의"
    
    @staticmethod
    def sanitize_keyword(keyword: str) -> str:
        """키워드 전처리: 특수문자 제거, 공백 정리"""
        import re
        keyword = re.sub(r'[^\w\s가-힣]', ' ', keyword)
        return ' '.join(keyword.split())

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
