"""Mixin module: ui."""

# gui/listings_widget.py
"""All listings browser widget - Shows all scraped items"""

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QHeaderView, QTableWidget, QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    ComboBox,
    PushButton,
    SearchLineEdit,
    SubtitleLabel,
)

if TYPE_CHECKING:
    from gui.widgets.listings.browser import ListingsWidget
    _HostBase_ListingsUiMixin = ListingsWidget
else:
    _HostBase_ListingsUiMixin = object

class ListingsUiMixin(_HostBase_ListingsUiMixin):
    """Ui behavior."""

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()

        header_layout.addWidget(SubtitleLabel("전체 매물 목록", self))

        header_layout.addStretch()

        # Search box
        self.search_input = SearchLineEdit(self)
        self.search_input.setPlaceholderText("제목 검색...")
        self.search_input.setMinimumWidth(200)
        self.search_input.textChanged.connect(self.on_search_changed)
        header_layout.addWidget(self.search_input)

        # Platform filter
        self.platform_combo = ComboBox(self)
        self.platform_combo.addItems(["전체", "당근마켓", "번개장터", "중고나라"])
        self.platform_combo.setMinimumWidth(100)
        self.platform_combo.currentTextChanged.connect(self.on_platform_changed)
        header_layout.addWidget(self.platform_combo)

        # Status filter dropdown (replaces exclude_sold checkbox)
        header_layout.addWidget(BodyLabel("상태:", self))

        self.status_combo = ComboBox(self)
        self.status_combo.addItems(["전체", "판매중", "예약중", "판매완료"])
        self.status_combo.setMinimumWidth(80)
        self.status_combo.currentTextChanged.connect(self.on_status_changed)
        header_layout.addWidget(self.status_combo)

        # Refresh button
        refresh_btn = PushButton("새로고침", self)
        refresh_btn.clicked.connect(lambda: self.refresh_listings(force=True))
        header_layout.addWidget(refresh_btn)

        # Compare button
        compare_btn = PushButton("비교", self)
        compare_btn.setToolTip("선택한 매물들을 비교합니다 (2-5개 선택)")
        compare_btn.clicked.connect(self._compare_selected)
        header_layout.addWidget(compare_btn)

        # Export button (Feature #16)
        export_btn = PushButton("내보내기", self)
        export_btn.setToolTip("현재 필터가 적용된 매물을 CSV/Excel로 내보내기")
        export_btn.clicked.connect(self._show_export_dialog)
        header_layout.addWidget(export_btn)

        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["플랫폼", "제목", "가격", "키워드", "등록일", "링크"])
        h_header = self.table.horizontalHeader()
        if h_header is not None:
            h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 60)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)  # Allow multi-select
        v_header = self.table.verticalHeader()
        if v_header is not None:
            v_header.setVisible(False)
            v_header.setDefaultSectionSize(40)
        self.table.cellDoubleClicked.connect(self.on_row_double_click)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.table, 1)

        # Pagination
        pagination_layout = QHBoxLayout()

        self.count_label = CaptionLabel("총 0개", self)
        pagination_layout.addWidget(self.count_label)

        pagination_layout.addStretch()

        self.prev_btn = PushButton("이전", self)
        self.prev_btn.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_btn)

        self.page_label = BodyLabel("1 / 1", self)
        pagination_layout.addWidget(self.page_label)

        self.next_btn = PushButton("다음", self)
        self.next_btn.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_btn)

        layout.addLayout(pagination_layout)
