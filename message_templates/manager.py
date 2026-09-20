"""Template store: CRUD, lookup, and rendering orchestration."""

from typing import Mapping, Sequence

from .clipboard import copy_text_to_clipboard
from .context import create_context_from_listing
from .defaults import DEFAULT_TEMPLATES
from .template import MessageTemplate


class MessageTemplateManager:
    """Manages message templates for seller communication"""

    DEFAULT_TEMPLATES = DEFAULT_TEMPLATES

    def __init__(self, custom_templates: Sequence[object] | None = None):
        """
        Initialize with optional custom templates.

        Args:
            custom_templates: List of custom templates (overrides defaults if provided)
        """
        self.templates = (
            self._normalize_templates(custom_templates)
            if custom_templates
            else self.DEFAULT_TEMPLATES.copy()
        )

    def _normalize_templates(self, templates: Sequence[object] | None) -> list[MessageTemplate]:
        """
        Normalize templates coming from settings (e.g. models.MessageTemplate) or dicts
        into this module's MessageTemplate (which has render()).
        """
        normalized: list[MessageTemplate] = []
        if not templates:
            return normalized

        for t in templates:
            if isinstance(t, MessageTemplate):
                normalized.append(t)
                continue

            # dict-like template
            if isinstance(t, dict):
                name = str(t.get("name", "") or "")
                content = str(t.get("content", "") or "")
                platform = str(t.get("platform", "all") or "all")
                if name and content:
                    normalized.append(MessageTemplate(name=name, content=content, platform=platform))
                continue

            # models.MessageTemplate or other objects with attributes
            name = str(getattr(t, "name", "") or "")
            content = str(getattr(t, "content", "") or "")
            platform = str(getattr(t, "platform", "all") or "all")
            if name and content:
                normalized.append(MessageTemplate(name=name, content=content, platform=platform))

        return normalized

    def get_templates(self, platform: str | None = None) -> list[MessageTemplate]:
        """
        Get templates, optionally filtered by platform.

        Args:
            platform: Filter by platform ("danggeun", "bunjang", "joonggonara", or None for all)

        Returns:
            List of applicable templates
        """
        if not platform:
            return self.templates

        return [
            t for t in self.templates
            if t.platform == "all" or t.platform == platform
        ]

    def render_template(self, template_name: str, context: Mapping[str, object]) -> str | None:
        """
        Render a template by name with the given context.

        Args:
            template_name: Name of the template to use
            context: Variable substitution context

        Returns:
            Rendered message string or None if template not found
        """
        for template in self.templates:
            if template.name == template_name:
                return template.render(context)
        return None

    def add_template(self, name: str, content: str, platform: str = "all"):
        """Add a new template"""
        self.templates.append(MessageTemplate(
            name=name,
            content=content,
            platform=platform
        ))

    def update_template(
        self,
        name: str,
        content: str | None = None,
        platform: str | None = None,
    ) -> None:
        """Update an existing template"""
        for template in self.templates:
            if template.name == name:
                if content is not None:
                    template.content = content
                if platform is not None:
                    template.platform = platform
                break

    def remove_template(self, name: str):
        """Remove a template by name"""
        self.templates = [t for t in self.templates if t.name != name]

    def get_available_variables(self) -> list[str]:
        """Get list of available template variables"""
        return [
            "{title} - 상품 제목",
            "{price} - 판매 가격",
            "{seller} - 판매자 이름",
            "{location} - 지역",
            "{target_price} - 목표 가격",
            "{platform} - 플랫폼 이름"
        ]

    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        """Copy text to system clipboard (Qt preferred, pyperclip fallback)."""
        return copy_text_to_clipboard(text)

    def create_context_from_listing(
        self,
        listing: Mapping[str, object],
        target_price: int | None = None,
    ) -> dict[str, str]:
        """Create a context dict from a listing dict (see context module)."""
        return create_context_from_listing(listing, target_price)


__all__ = ["MessageTemplateManager"]
