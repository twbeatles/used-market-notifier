"""Tag analysis result value object."""

from dataclasses import dataclass


@dataclass
class TagResult:
    """Result of auto-tagging analysis"""
    tag_name: str
    icon: str
    color: str
    matched_keyword: str


__all__ = ["TagResult"]
