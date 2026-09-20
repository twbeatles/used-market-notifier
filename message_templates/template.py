"""Seller message template with variable substitution."""

from dataclasses import dataclass
from typing import Mapping
import re


@dataclass
class MessageTemplate:
    """Template for seller messages with variable substitution"""
    name: str
    content: str
    platform: str = "all"  # "all", "danggeun", "bunjang", "joonggonara"

    def render(self, context: Mapping[str, object]) -> str:
        """
        Render template with context variables.

        Available variables:
            {title} - Listing title
            {price} - Listed price
            {seller} - Seller name
            {location} - Location
            {target_price} - User's target price (if set)
            {platform} - Platform name
        """
        result = self.content
        for key, value in context.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, str(value) if value else "")

        # Clean up any remaining placeholders
        result = re.sub(r'\{[^}]+\}', '', result)
        return result.strip()


__all__ = ["MessageTemplate"]
