# gui/keyword_manager.py
"""Enhanced keyword management widget with modern card-based design"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QDialog, QFormLayout, QLineEdit, QSpinBox, QComboBox,
    QCheckBox, QLabel, QGroupBox, QMessageBox, QTextEdit, QFrame,
    QScrollArea, QGridLayout, QSizePolicy, QGraphicsDropShadowEffect,
    QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QFont, QColor
from models import SearchKeyword, KeywordPreset
