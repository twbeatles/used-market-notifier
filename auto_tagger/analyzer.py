from typing import TYPE_CHECKING
# pyright: reportAttributeAccessIssue=false
"""Title analysis: match tag rules against listing titles."""

from .tag_result import TagResult


if TYPE_CHECKING:
    from auto_tagger.tagger import AutoTagger
    _HostBase_AnalyzerMixin = AutoTagger
else:
    _HostBase_AnalyzerMixin = object

class AnalyzerMixin(_HostBase_AnalyzerMixin):  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    """Title-matching behavior for AutoTagger (needs ``self.rules``)."""

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


__all__ = ["AnalyzerMixin"]
