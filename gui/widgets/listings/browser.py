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
    ListingsCoreMixin,
    ListingsShortcutsMixin,
    ListingsUiMixin,
    ListingsFiltersMixin,
    ListingsTableMixin,
    ListingsActionsMixin,
    QWidget,
):
    """Widget to browse all scraped listings."""
