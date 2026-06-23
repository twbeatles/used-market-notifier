"""Mixin module: ui."""

# gui/listings_widget.py
"""All listings browser widget - Shows all scraped items"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QLineEdit, QMessageBox, QMenu, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence
from typing import Optional

from ....link_utils import open_external_url


class ListingsUiMixin:
    """Ui behavior."""

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("📋 전체 매물 목록")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #cdd6f4;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 제목 검색...")
        self.search_input.setMinimumWidth(200)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 8px 12px;
                color: #cdd6f4;
            }
            QLineEdit:focus {
                border: 1px solid #89b4fa;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_changed)
        header_layout.addWidget(self.search_input)

        # Platform filter
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["전체", "당근마켓", "번개장터", "중고나라"])
        self.platform_combo.setStyleSheet("""
            QComboBox {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 8px 12px;
                color: #cdd6f4;
                min-width: 100px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
        """)
        self.platform_combo.currentTextChanged.connect(self.on_platform_changed)
        header_layout.addWidget(self.platform_combo)

        # Status filter dropdown (replaces exclude_sold checkbox)
        status_label = QLabel("상태:")
        status_label.setStyleSheet("color: #a6adc8;")
        header_layout.addWidget(status_label)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["전체", "판매중", "예약중", "판매완료"])
        self.status_combo.setStyleSheet("""
            QComboBox {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 8px 12px;
                color: #cdd6f4;
                min-width: 80px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow { image: none; border: none; }
        """)
        self.status_combo.currentTextChanged.connect(self.on_status_changed)
        header_layout.addWidget(self.status_combo)

        # Refresh button
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
        """)
        refresh_btn.clicked.connect(lambda: self.refresh_listings(force=True))
        header_layout.addWidget(refresh_btn)

        # Compare button
        compare_btn = QPushButton("📊 비교")
        compare_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)
        compare_btn.setToolTip("선택한 매물들을 비교합니다 (2-5개 선택)")
        compare_btn.clicked.connect(self._compare_selected)
        header_layout.addWidget(compare_btn)

        # Export button (Feature #16)
        export_btn = QPushButton("📥 내보내기")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #f9e2af;
                color: #1e1e2e;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #fab387;
            }
        """)
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
        self.table.cellDoubleClicked.connect(self.on_row_double_click)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e2e;
                alternate-background-color: #313244;
                gridline-color: #45475a;
                border: none;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 8px;
                color: #cdd6f4;
            }
            QTableWidget::item:hover {
                background-color: #45475a;
            }
            QTableWidget::item:selected {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
            QHeaderView::section {
                background-color: #181825;
                color: #a6adc8;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #45475a;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table, 1)

        # Pagination
        pagination_layout = QHBoxLayout()

        self.count_label = QLabel("총 0개")
        self.count_label.setStyleSheet("color: #6c7086;")
        pagination_layout.addWidget(self.count_label)

        pagination_layout.addStretch()

        self.prev_btn = QPushButton("◀ 이전")
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
            QPushButton:disabled {
                color: #6c7086;
            }
        """)
        self.prev_btn.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_btn)

        self.page_label = QLabel("1 / 1")
        self.page_label.setStyleSheet("color: #cdd6f4; padding: 0 16px;")
        pagination_layout.addWidget(self.page_label)

        self.next_btn = QPushButton("다음 ▶")
        self.next_btn.setStyleSheet(self.prev_btn.styleSheet())
        self.next_btn.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_btn)

        layout.addLayout(pagination_layout)
