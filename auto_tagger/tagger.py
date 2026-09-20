"""AutoTagger composed from focused behavior mixins."""

from typing import Any

from .analyzer import AnalyzerMixin
from .default_rules import DEFAULT_RULES
from .display import DisplayMixin
from .store import StoreMixin


class AutoTagger(AnalyzerMixin, DisplayMixin, StoreMixin):
    """Analyzes listing titles and generates automatic tags"""

    DEFAULT_RULES: list[dict[str, Any]] = DEFAULT_RULES

    def __init__(self, custom_rules: list[dict[str, Any]] | None = None):
        """
        Initialize AutoTagger with optional custom rules.

        Args:
            custom_rules: List of rule dicts to use instead of defaults
        """
        self.rules = custom_rules if custom_rules else self.DEFAULT_RULES


# Convenience function for quick tagging
def auto_tag(title: str) -> list[str]:
    """Quick function to get tags for a title"""
    tagger = AutoTagger()
    return tagger.analyze(title)


__all__ = ["AutoTagger", "auto_tag"]
