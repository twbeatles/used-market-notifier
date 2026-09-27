# gui/keyword_manager.py
"""Enhanced keyword management widget with modern card-based design"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QDialog, QFormLayout, QLineEdit, QSpinBox, QComboBox,
    QCheckBox, QLabel, QGroupBox, QMessageBox, QTextEdit, QFrame,
    QScrollArea, QGridLayout, QSizePolicy, QGraphicsDropShadowEffect,
    QInputDialog
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QFont, QColor
from qfluentwidgets import (
    CaptionLabel,
    CheckBox,
    ComboBox,
    FluentIcon as FIF,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    SpinBox,
    SubtitleLabel,
    TextEdit,
)
from gui.loading_spinner import EmptyStateWidget
from models import SearchKeyword, KeywordPreset
