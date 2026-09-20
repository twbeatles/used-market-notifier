"""Dark theme stylesheet (assembled from dark_sections)."""

from .dark_sections import (
    BASE_QSS,
    TABS_QSS,
    BUTTONS_QSS,
    INPUTS_QSS,
    LISTS_QSS,
    CHROME_QSS,
    OVERLAYS_QSS,
    CARDS_QSS,
)

DARK_STYLE = (
    BASE_QSS +
    TABS_QSS +
    BUTTONS_QSS +
    INPUTS_QSS +
    LISTS_QSS +
    CHROME_QSS +
    OVERLAYS_QSS +
    CARDS_QSS
)

__all__ = ["DARK_STYLE"]
