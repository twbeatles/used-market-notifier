# message_templates.py
"""Message template system for quick seller communication.

Canonical implementations live in this package, split by responsibility:
template value object, built-in defaults, clipboard I/O, listing-context
mapping, and the manager (store + orchestration). This ``__init__``
re-exports the previous ``message_templates.py`` public surface.
"""

from .clipboard import copy_text_to_clipboard
from .context import create_context_from_listing
from .defaults import DEFAULT_TEMPLATES
from .manager import MessageTemplateManager
from .template import MessageTemplate

__all__ = [
    "DEFAULT_TEMPLATES",
    "MessageTemplate",
    "MessageTemplateManager",
    "copy_text_to_clipboard",
    "create_context_from_listing",
]
