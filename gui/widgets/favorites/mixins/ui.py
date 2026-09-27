from typing import TYPE_CHECKING
"""Mixin module: ui."""

# gui/favorites_widget.py
"""Favorites management widget"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QMessageBox, QMenu, QDialog,
    QFormLayout, QLineEdit, QSpinBox, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont
from qfluentwidgets import FluentIcon as FIF, PushButton, SubtitleLabel
from db import DatabaseManager
from ....link_utils import open_external_url


if TYPE_CHECKING:
    from gui.widgets.favorites.widget import FavoritesWidget
    _HostBase_FavoritesUiMixin = FavoritesWidget
else:
    _HostBase_FavoritesUiMixin = object

class FavoritesUiMixin(_HostBase_FavoritesUiMixin):
    """Ui behavior."""

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(SubtitleLabel("즐겨찾기", self))

        header_layout.addStretch()

        refresh_btn = PushButton("새로고침", self)
        refresh_btn.clicked.connect(self.refresh_list)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["플랫폼", "제목", "가격", "목표가", "메모", "등록일"])
        h_header = self.table.horizontalHeader()
        if h_header is not None:
            h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # Table style
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        v_header = self.table.verticalHeader()
        if v_header is not None:
            v_header.setVisible(False)
            v_header.setDefaultSectionSize(40)
        self.table.setSortingEnabled(True)  # Enable column sorting

        layout.addWidget(self.table)

        # Empty state placeholder
        from gui.loading_spinner import EmptyStateWidget
        self.empty_state = EmptyStateWidget(
            icon=FIF.HEART,
            title="즐겨찾기가 비어있습니다",
            message="관심있는 매물을 즐겨찾기에 추가해보세요.\n매물 목록에서 우클릭 → '즐겨찾기 추가'",
            parent=self
        )
        self.empty_state.hide()
        layout.addWidget(self.empty_state)

        # Context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.cellDoubleClicked.connect(self.on_double_click)

        self.refresh_list()
