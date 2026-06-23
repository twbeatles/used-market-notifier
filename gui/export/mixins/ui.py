"""Mixin module: ui."""

"""Enhanced export dialog with filtering options."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QCheckBox, QComboBox, QDateEdit, QRadioButton,
    QButtonGroup, QFileDialog, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from typing import Mapping

class ExportUiMixin:
    """Ui behavior."""

    def setup_ui(self):
        self.setWindowTitle("📥 데이터 내보내기")
        self.setMinimumWidth(450)
        self.setStyleSheet("QDialog { background-color: #1e1e2e; }")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("📥 매물 데이터 내보내기")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #cdd6f4;")
        layout.addWidget(title)
        
        # Format selection
        format_group = QGroupBox("📄 파일 형식")
        format_group.setStyleSheet(self._group_style())
        format_layout = QHBoxLayout(format_group)
        
        self.format_group = QButtonGroup(self)
        self.csv_radio = QRadioButton("CSV (.csv)")
        self.csv_radio.setChecked(True)
        self.csv_radio.setStyleSheet("color: #cdd6f4;")
        self.excel_radio = QRadioButton("Excel (.xlsx)")
        self.excel_radio.setStyleSheet("color: #cdd6f4;")
        
        self.format_group.addButton(self.csv_radio, 0)
        self.format_group.addButton(self.excel_radio, 1)
        
        format_layout.addWidget(self.csv_radio)
        format_layout.addWidget(self.excel_radio)
        format_layout.addStretch()
        layout.addWidget(format_group)
        
        # Filter options
        filter_group = QGroupBox("🔍 필터 옵션")
        filter_group.setStyleSheet(self._group_style())
        filter_layout = QVBoxLayout(filter_group)
        
        # Use current filters checkbox
        self.use_current_filters = QCheckBox("현재 적용된 필터 사용")
        self.use_current_filters.setChecked(True)
        self.use_current_filters.setStyleSheet("color: #cdd6f4;")
        self.use_current_filters.stateChanged.connect(self._toggle_filters)
        filter_layout.addWidget(self.use_current_filters)
        
        # Platform filter
        platform_layout = QHBoxLayout()
        platform_label = QLabel("플랫폼:")
        platform_label.setStyleSheet("color: #a6adc8;")
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["전체", "당근마켓", "번개장터", "중고나라"])
        self.platform_combo.setStyleSheet(self._combo_style())
        self.platform_combo.setEnabled(False)
        platform_layout.addWidget(platform_label)
        platform_layout.addWidget(self.platform_combo)
        platform_layout.addStretch()
        filter_layout.addLayout(platform_layout)
        
        # Status filter
        status_layout = QHBoxLayout()
        status_label = QLabel("판매 상태:")
        status_label.setStyleSheet("color: #a6adc8;")
        self.status_combo = QComboBox()
        self.status_combo.addItems(["전체", "판매중", "예약중", "판매완료"])
        self.status_combo.setStyleSheet(self._combo_style())
        self.status_combo.setEnabled(False)
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_combo)
        status_layout.addStretch()
        filter_layout.addLayout(status_layout)
        
        # Include sold checkbox
        self.include_sold = QCheckBox("판매완료 포함")
        self.include_sold.setChecked(True)
        self.include_sold.setStyleSheet("color: #cdd6f4;")
        self.include_sold.setEnabled(False)
        filter_layout.addWidget(self.include_sold)
        
        layout.addWidget(filter_group)
        
        # Date range
        date_group = QGroupBox("📅 날짜 범위")
        date_group.setStyleSheet(self._group_style())
        date_layout = QHBoxLayout(date_group)
        
        self.use_date_range = QCheckBox("날짜 필터")
        self.use_date_range.setStyleSheet("color: #cdd6f4;")
        self.use_date_range.stateChanged.connect(self._toggle_dates)
        date_layout.addWidget(self.use_date_range)
        
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setEnabled(False)
        self.date_from.setStyleSheet(self._date_style())
        from_label = QLabel("부터")
        from_label.setStyleSheet("color: #a6adc8;")
        date_layout.addWidget(from_label)
        date_layout.addWidget(self.date_from)
        
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setEnabled(False)
        self.date_to.setStyleSheet(self._date_style())
        to_label = QLabel("까지")
        to_label.setStyleSheet("color: #a6adc8;")
        date_layout.addWidget(to_label)
        date_layout.addWidget(self.date_to)
        
        date_layout.addStretch()
        layout.addWidget(date_group)
        
        # Column selection
        col_group = QGroupBox("📋 내보낼 항목")
        col_group.setStyleSheet(self._group_style())
        col_layout = QVBoxLayout(col_group)
        
        col_row1 = QHBoxLayout()
        self.col_title = QCheckBox("제목")
        self.col_title.setChecked(True)
        self.col_price = QCheckBox("가격")
        self.col_price.setChecked(True)
        self.col_platform = QCheckBox("플랫폼")
        self.col_platform.setChecked(True)
        self.col_seller = QCheckBox("판매자")
        self.col_seller.setChecked(True)
        
        for cb in [self.col_title, self.col_price, self.col_platform, self.col_seller]:
            cb.setStyleSheet("color: #cdd6f4;")
            col_row1.addWidget(cb)
        col_layout.addLayout(col_row1)
        
        col_row2 = QHBoxLayout()
        self.col_location = QCheckBox("지역")
        self.col_location.setChecked(True)
        self.col_keyword = QCheckBox("키워드")
        self.col_keyword.setChecked(True)
        self.col_date = QCheckBox("등록일")
        self.col_date.setChecked(True)
        self.col_url = QCheckBox("URL")
        self.col_url.setChecked(True)
        
        for cb in [self.col_location, self.col_keyword, self.col_date, self.col_url]:
            cb.setStyleSheet("color: #cdd6f4;")
            col_row2.addWidget(cb)
        col_layout.addLayout(col_row2)
        
        col_row3 = QHBoxLayout()
        self.col_status = QCheckBox("판매상태")
        self.col_status.setChecked(True)
        self.col_note = QCheckBox("메모")
        self.col_note.setChecked(False)
        self.col_tags = QCheckBox("태그")
        self.col_tags.setChecked(False)
        
        for cb in [self.col_status, self.col_note, self.col_tags]:
            cb.setStyleSheet("color: #cdd6f4;")
            col_row3.addWidget(cb)
        col_row3.addStretch()
        col_layout.addLayout(col_row3)
        
        layout.addWidget(col_group)
        
        # Progress bar (hidden initially)
        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #45475a;
                border-radius: 4px;
                background-color: #313244;
                text-align: center;
                color: #cdd6f4;
            }
            QProgressBar::chunk {
                background-color: #a6e3a1;
            }
        """)
        self.progress.hide()
        layout.addWidget(self.progress)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("취소")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #585b70; }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.export_btn = QPushButton("📥 내보내기")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1;
                color: #1e1e2e;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #94e2d5; }
        """)
        self.export_btn.clicked.connect(self._do_export)
        button_layout.addWidget(self.export_btn)
        
        layout.addLayout(button_layout)
