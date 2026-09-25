from typing import TYPE_CHECKING
# pyright: reportAttributeAccessIssue=false
"""Tag display helpers: icon/color lookup and HTML badge rendering."""


if TYPE_CHECKING:
    from auto_tagger.tagger import AutoTagger
    _HostBase_DisplayMixin = AutoTagger
else:
    _HostBase_DisplayMixin = object

class DisplayMixin(_HostBase_DisplayMixin):
    """Display behavior for AutoTagger (needs ``self.rules``)."""

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


__all__ = ["DisplayMixin"]
