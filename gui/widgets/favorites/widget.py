# gui/favorites_widget.py
"""Favorites management widget"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QMessageBox, QMenu, QDialog,
    QFormLayout, QLineEdit, QSpinBox, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QFont
from db import DatabaseManager
from ...link_utils import open_external_url

from .mixins import (
    FavoritesCoreMixin,
    FavoritesUiMixin,
    FavoritesActionsMixin,
)

class FavoritesWidget(
    FavoritesCoreMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    FavoritesUiMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    FavoritesActionsMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    QWidget,
):
    """Favorites management widget."""
