# auto_tagger.py
"""Automatic tagging system for listings based on title keywords"""

from dataclasses import dataclass
from typing import Any


@dataclass
class TagResult:
    """Result of auto-tagging analysis"""
    tag_name: str
    icon: str
    color: str
    matched_keyword: str


class AutoTagger:
    """Analyzes listing titles and generates automatic tags"""
    
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
    
    def __init__(self, custom_rules: list[dict[str, Any]] | None = None):
        """
        Initialize AutoTagger with optional custom rules.
        
        Args:
            custom_rules: List of rule dicts to use instead of defaults
        """
        self.rules = custom_rules if custom_rules else self.DEFAULT_RULES
    
    def analyze(self, title: str) -> list[str]:
        """
        Analyze title and return list of matching tag names.
        
        Args:
            title: The listing title to analyze
            
        Returns:
            List of tag names that matched
        """
        if not title:
            return []
        
        title_lower = title.lower()
        matched_tags = []
        
        for rule in self.rules:
            if not rule.get('enabled', True):
                continue
                
            for keyword in rule.get('keywords', []):
                if keyword.lower() in title_lower:
                    matched_tags.append(rule['tag_name'])
                    break  # Only add each tag once
        
        return matched_tags
    
    def analyze_detailed(self, title: str) -> list[TagResult]:
        """
        Analyze title and return detailed tag results.
        
        Args:
            title: The listing title to analyze
            
        Returns:
            List of TagResult objects with full tag info
        """
        if not title:
            return []
        
        title_lower = title.lower()
        results = []
        
        for rule in self.rules:
            if not rule.get('enabled', True):
                continue
                
            for keyword in rule.get('keywords', []):
                if keyword.lower() in title_lower:
                    results.append(TagResult(
                        tag_name=rule['tag_name'],
                        icon=rule.get('icon', '🏷️'),
                        color=rule.get('color', '#89b4fa'),
                        matched_keyword=keyword
                    ))
                    break  # Only add each tag once
        
        return results
    
    def get_tag_display(self, tag_name: str) -> tuple:
        """
        Get display info for a tag.
        
        Returns:
            Tuple of (icon, color) for the tag
        """
        for rule in self.rules:
            if rule['tag_name'] == tag_name:
                return (rule.get('icon', '🏷️'), rule.get('color', '#89b4fa'))
        return ('🏷️', '#89b4fa')
    
    def format_tags_html(self, tags: list[str]) -> str:
        """
        Format tags as HTML badges for display.
        
        Args:
            tags: List of tag names
            
        Returns:
            HTML string with styled tag badges
        """
        if not tags:
            return ""
        
        badges = []
        for tag in tags:
            icon, color = self.get_tag_display(tag)
            badge = f'<span style="background-color: {color}; color: #1e1e2e; ' \
                    f'padding: 2px 6px; border-radius: 4px; margin-right: 4px; ' \
                    f'font-size: 10pt;">{icon} {tag}</span>'
            badges.append(badge)
        
        return ''.join(badges)
    
    def update_rules(self, new_rules: list[dict[str, Any]]) -> None:
        """Update the tagging rules"""
        self.rules = new_rules
    
    def add_rule(self, tag_name: str, keywords: list[str], 
                 color: str = "#89b4fa", icon: str = "🏷️"):
        """Add a new tagging rule"""
        self.rules.append({
            "tag_name": tag_name,
            "keywords": keywords,
            "color": color,
            "icon": icon,
            "enabled": True
        })
    
    def remove_rule(self, tag_name: str):
        """Remove a tagging rule by name"""
        self.rules = [r for r in self.rules if r['tag_name'] != tag_name]


# Convenience function for quick tagging
def auto_tag(title: str) -> list[str]:
    """Quick function to get tags for a title"""
    tagger = AutoTagger()
    return tagger.analyze(title)


if __name__ == "__main__":
    # Test auto tagger
    tagger = AutoTagger()
    
    test_titles = [
        "맥북 프로 M2 A급 풀박스 정품",
        "아이폰 15 급처 네고가능",
        "갤럭시 S24 택포 직거래",
        "맥북 에어 중고",
        "에어팟 프로 미개봉 새제품"
    ]
    
    for title in test_titles:
        tags = tagger.analyze(title)
        detailed = tagger.analyze_detailed(title)
        print(f"\n'{title}'")
        print(f"  Tags: {tags}")
        for t in detailed:
            print(f"    - {t.icon} {t.tag_name} (matched: '{t.matched_keyword}')")
