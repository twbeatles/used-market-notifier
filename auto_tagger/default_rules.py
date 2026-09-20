"""Built-in default auto-tagging rules."""

from typing import Any


# Default tag rules - can be customized via settings
DEFAULT_RULES: list[dict[str, Any]] = [
    {
        "tag_name": "A급",
        "keywords": ["A급", "에이급", "상태좋음", "매우깨끗", "최상", "S급"],
        "color": "#a6e3a1",  # Green
        "icon": "✨"
    },
    {
        "tag_name": "풀박스",
        "keywords": ["풀박스", "풀박", "미개봉", "새제품", "미사용"],
        "color": "#89b4fa",  # Blue
        "icon": "📦"
    },
    {
        "tag_name": "급처",
        "keywords": ["급처", "급매", "급급", "빨리", "오늘만"],
        "color": "#f38ba8",  # Red
        "icon": "🔥"
    },
    {
        "tag_name": "네고가능",
        "keywords": ["네고가능", "네고", "협의가능", "가격협의", "흥정"],
        "color": "#f9e2af",  # Yellow
        "icon": "💬"
    },
    {
        "tag_name": "택포",
        "keywords": ["택포", "택배포함", "배송비포함", "무배"],
        "color": "#94e2d5",  # Teal
        "icon": "📮"
    },
    {
        "tag_name": "직거래",
        "keywords": ["직거래", "직거래만", "직거래전용", "직거래희망"],
        "color": "#cba6f7",  # Purple
        "icon": "🤝"
    },
    {
        "tag_name": "정품",
        "keywords": ["정품", "정품확인", "구매영수증", "보증서"],
        "color": "#fab387",  # Peach
        "icon": "✅"
    },
    {
        "tag_name": "구성품포함",
        "keywords": ["구성품", "풀구성", "박스포함", "악세사리포함"],
        "color": "#74c7ec",  # Sapphire
        "icon": "🎁"
    }
]


__all__ = ["DEFAULT_RULES"]
