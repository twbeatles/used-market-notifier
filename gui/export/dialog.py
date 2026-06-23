# gui/export_dialog.py
"""Enhanced export dialog with filtering options"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QCheckBox, QComboBox, QDateEdit, QRadioButton,
    QButtonGroup, QFileDialog, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from typing import Mapping

from .mixins import (
    ExportUiMixin,
    ExportActionsMixin,
    ExportStylesMixin,
)

class ExportDialog(
    ExportUiMixin,
    ExportActionsMixin,
    ExportStylesMixin,
    QDialog,
):
    """ExportDialog dialog."""

    def __init__(self, db, current_filters: Mapping[str, object] | None = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_filters = current_filters or {}
        self.setup_ui()
    
