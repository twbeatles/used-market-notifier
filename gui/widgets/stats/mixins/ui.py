"""Mixin module: ui."""

from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QLabel,
    QFileDialog,
    QHeaderView,
    QMenu,
    QMessageBox,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
)
from qfluentwidgets import CaptionLabel, PushButton, ScrollArea, SubtitleLabel

from export_manager import ExportManager
from models import Item

from ....charts import DailyChart, PlatformChart
from ....link_utils import open_external_url


if TYPE_CHECKING:
    from gui.widgets.stats.dashboard import StatsWidget
    _HostBase_StatsUiMixin = StatsWidget
else:
    _HostBase_StatsUiMixin = object

class _SummaryCard(QWidget):
    """Fluent summary card: identity dot + title + value (QSS-free)."""

    def __init__(self, title: str, value: str, unit: str, accent: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        head = QHBoxLayout()
        head.setSpacing(8)
        dot = QPixmap(12, 12)
        dot.fill(QColor(accent))
        dot_label = QLabel()
        dot_label.setPixmap(dot)
        dot_label.setFixedSize(12, 12)
        head.addWidget(dot_label)
        head.addWidget(CaptionLabel(title, self), 1)
        layout.addLayout(head)

        value_row = QHBoxLayout()
        value_row.setSpacing(4)
        self.value_label = SubtitleLabel(value, self)
        value_row.addWidget(self.value_label)
        value_row.addWidget(CaptionLabel(unit, self), 1)
        layout.addLayout(value_row)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class StatsUiMixin(_HostBase_StatsUiMixin):
    """Ui behavior."""

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = ScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()
        header_layout.addWidget(SubtitleLabel("통계 대시보드", self))
        header_layout.addStretch()

        export_btn = PushButton("내보내기", self)
        export_btn.clicked.connect(self.show_export_menu)
        header_layout.addWidget(export_btn)

        refresh_btn = PushButton("새로고침", self)
        refresh_btn.clicked.connect(lambda: self.refresh_stats(force=True))
        header_layout.addWidget(refresh_btn)
        layout.addLayout(header_layout)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        self.total_card = _SummaryCard("전체 상품", "0", "건", "#7aa2f7")
        self.danggeun_card = _SummaryCard("당근마켓", "0", "건", "#ff9e64")
        self.bunjang_card = _SummaryCard("번개장터", "0", "건", "#bb9af7")
        self.joonggonara_card = _SummaryCard("중고나라", "0", "건", "#9ece6a")
        cards_layout.addWidget(self.total_card)
        cards_layout.addWidget(self.danggeun_card)
        cards_layout.addWidget(self.bunjang_card)
        cards_layout.addWidget(self.joonggonara_card)
        layout.addLayout(cards_layout)

        charts_tabs = QTabWidget()
        charts_tabs.setMinimumHeight(220)
        charts_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        platform_widget = QWidget()
        platform_layout = QVBoxLayout(platform_widget)
        platform_layout.setContentsMargins(12, 12, 12, 12)
        self.platform_chart = PlatformChart()
        self.platform_chart.setMinimumHeight(180)
        platform_layout.addWidget(self.platform_chart)
        charts_tabs.addTab(platform_widget, "플랫폼 분포")

        daily_widget = QWidget()
        daily_layout = QVBoxLayout(daily_widget)
        daily_layout.setContentsMargins(12, 12, 12, 12)
        self.daily_chart = DailyChart()
        self.daily_chart.setMinimumHeight(180)
        daily_layout.addWidget(self.daily_chart)
        charts_tabs.addTab(daily_widget, "최근 7일 추이")
        layout.addWidget(charts_tabs)

        tables_tabs = QTabWidget()
        tables_tabs.setMinimumHeight(300)
        tables_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.recent_table = self._create_table(["플랫폼", "제목", "가격", "키워드", "시간"], stretch_col=1)
        self.recent_table.setColumnWidth(0, 90)
        self.recent_table.setColumnWidth(2, 120)
        self.recent_table.setColumnWidth(3, 140)
        self.recent_table.setColumnWidth(4, 80)
        self.recent_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.recent_table.customContextMenuRequested.connect(self.show_context_menu)
        self.recent_table.cellDoubleClicked.connect(self.on_table_double_click)
        tables_tabs.addTab(self._table_tab(self.recent_table), "최근 발견 상품")

        self.price_table = self._create_table(["상품", "이전 가격", "현재 가격", "시간"], stretch_col=0)
        self.price_table.setColumnWidth(1, 120)
        self.price_table.setColumnWidth(2, 120)
        self.price_table.setColumnWidth(3, 120)
        self.price_table.cellDoubleClicked.connect(self.on_table_double_click)
        tables_tabs.addTab(self._table_tab(self.price_table), "가격 변동")

        self.analysis_table = self._create_table(["키워드", "매물 수", "최저가", "평균가", "최고가"], stretch_col=0)
        self.analysis_table.setColumnWidth(1, 80)
        self.analysis_table.setColumnWidth(2, 120)
        self.analysis_table.setColumnWidth(3, 120)
        self.analysis_table.setColumnWidth(4, 120)
        tables_tabs.addTab(self._table_tab(self.analysis_table), "키워드 시세")

        self.status_history_table = self._create_table(
            ["플랫폼", "제목", "이전 상태", "현재 상태", "시간"],
            stretch_col=1,
        )
        self.status_history_table.setColumnWidth(0, 90)
        self.status_history_table.setColumnWidth(2, 110)
        self.status_history_table.setColumnWidth(3, 110)
        self.status_history_table.setColumnWidth(4, 150)
        self.status_history_table.cellDoubleClicked.connect(self.on_table_double_click)
        tables_tabs.addTab(self._table_tab(self.status_history_table), "판매 상태 변경")

        layout.addWidget(tables_tabs, 1)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)


    def _create_table(self, headers: list[str], stretch_col: int) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        h_header = table.horizontalHeader()
        if h_header is not None:
            h_header.setSectionResizeMode(stretch_col, QHeaderView.ResizeMode.Stretch)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        v_header = table.verticalHeader()
        if v_header is not None:
            v_header.setVisible(False)
            v_header.setDefaultSectionSize(40)
        return table


    def _table_tab(self, table: QTableWidget) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.addWidget(table)
        return widget
