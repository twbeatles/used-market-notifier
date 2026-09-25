# gui/listings_widget.py
"""All listings browser widget - Shows all scraped items"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QLineEdit, QMessageBox, QMenu, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence
from typing import Optional

from ...link_utils import open_external_url

from .mixins import (
    ListingsCoreMixin,
    ListingsShortcutsMixin,
    ListingsUiMixin,
    ListingsFiltersMixin,
    ListingsTableMixin,
    ListingsActionsMixin,
)

class ListingsWidget(
    ListingsCoreMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    ListingsShortcutsMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    ListingsUiMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    ListingsFiltersMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    ListingsTableMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    ListingsActionsMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    QWidget,
):
    """Widget to browse all scraped listings."""

    def __init__(self, engine=None, parent=None):
        super().__init__(engine, parent)
