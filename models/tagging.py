"""Auto-tagging rule and seller message-template models."""

from dataclasses import dataclass, field


@dataclass
class TagRule:
    """Rule for auto-tagging listings based on title keywords"""
    tag_name: str           # 태그 이름 (예: "A급")
    keywords: list[str] = field(default_factory=list)  # 트리거 키워드들
    color: str = "#89b4fa"  # 태그 색상
    icon: str = "🏷️"        # 태그 아이콘
    enabled: bool = True


@dataclass
class MessageTemplate:
    """Template for quick messages to sellers"""
    name: str               # 템플릿 이름
    content: str            # 템플릿 내용 (변수: {title}, {price}, {seller}, {location}, {target_price})
    platform: str = "all"   # "all", "danggeun", "bunjang", "joonggonara"


__all__ = ["TagRule", "MessageTemplate"]
