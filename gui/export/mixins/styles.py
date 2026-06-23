"""Mixin module: styles."""

"""Enhanced export dialog with filtering options."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QCheckBox, QComboBox, QDateEdit, QRadioButton,
    QButtonGroup, QFileDialog, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from typing import Mapping

class ExportStylesMixin:
    """Styles behavior."""

    def _group_style(self):
        return """
            QGroupBox {
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
        """
    

    def _combo_style(self):
        return """
            QComboBox {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px 10px;
                color: #cdd6f4;
                min-width: 100px;
            }
        """
    

    def _date_style(self):
        return """
            QDateEdit {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px 10px;
                color: #cdd6f4;
            }
        """
