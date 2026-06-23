# gui/compare_dialog.py
"""Enhanced dialog for comparing multiple listings side by side"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QTextEdit, QMessageBox, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ..link_utils import open_external_url

from .mixins import (
    CompareUiMixin,
    CompareActionsMixin,
)

class CompareDialog(
    CompareUiMixin,
    CompareActionsMixin,
    QDialog,
):
    """CompareDialog dialog."""

    def __init__(self, listings: list, parent=None):
        super().__init__(parent)
        self.listings = listings
        self.notes = {}  # Row notes for comparison
        self.setup_ui()

