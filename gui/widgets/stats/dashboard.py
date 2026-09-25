"""Enhanced statistics dashboard."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFileDialog,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
)

from export_manager import ExportManager
from models import Item

from ...charts import DailyChart, PlatformChart
from ...components import StatCard
from ...link_utils import open_external_url

from .mixins import (
    StatsCoreMixin,
    StatsUiMixin,
    StatsRefreshMixin,
    StatsActionsMixin,
)

class StatsWidget(
    StatsCoreMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    StatsUiMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    StatsRefreshMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    StatsActionsMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    QWidget,
):
    """Statistics dashboard with recent listings, price changes, and status history."""
