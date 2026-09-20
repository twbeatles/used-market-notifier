# pyright: reportAttributeAccessIssue=false
"""Rule-store management: replace, add, and remove tag rules."""

from typing import Any


class StoreMixin:
    """Rule-store behavior for AutoTagger (needs ``self.rules``)."""

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


__all__ = ["StoreMixin"]
