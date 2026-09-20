# auto_tagger.py
"""Automatic tagging system for listings based on title keywords.

Canonical implementations live in this package, split by responsibility:
result value object, default rules data, title analysis, display
formatting, rule-store management, and the composed ``AutoTagger``.
This ``__init__`` re-exports the previous ``auto_tagger.py`` public
surface.
"""

from .analyzer import AnalyzerMixin
from .default_rules import DEFAULT_RULES
from .display import DisplayMixin
from .store import StoreMixin
from .tag_result import TagResult
from .tagger import AutoTagger, auto_tag

__all__ = [
    "AnalyzerMixin",
    "AutoTagger",
    "DEFAULT_RULES",
    "DisplayMixin",
    "StoreMixin",
    "TagResult",
    "auto_tag",
]
