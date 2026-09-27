"""Mixin module: ui."""

"""Enhanced export dialog with filtering options."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QGroupBox, QDateEdit,
    QButtonGroup, QFileDialog, QMessageBox
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CheckBox,
    ComboBox,
    PrimaryPushButton,
    ProgressBar,
    PushButton,
    RadioButton,
    SubtitleLabel,
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime
from typing import Mapping, TYPE_CHECKING


if TYPE_CHECKING:
    from gui.export.dialog import ExportDialog
    _HostBase_ExportUiMixin = ExportDialog
else:
    _HostBase_ExportUiMixin = object

class ExportUiMixin(_HostBase_ExportUiMixin):
    """Ui behavior."""

    def setup_ui(self):
        self.setWindowTitle("데이터 내보내기")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        layout.addWidget(SubtitleLabel("매물 데이터 내보내기", self))
        
        # Format selection
        format_group = QGroupBox("파일 형식", self)
        format_layout = QHBoxLayout(format_group)
        
        self.format_group = QButtonGroup(self)
        self.csv_radio = RadioButton("CSV (.csv)", self)
        self.csv_radio.setChecked(True)
        self.excel_radio = RadioButton("Excel (.xlsx)", self)
        
        self.format_group.addButton(self.csv_radio, 0)
        self.format_group.addButton(self.excel_radio, 1)
        
        format_layout.addWidget(self.csv_radio)
        format_layout.addWidget(self.excel_radio)
        format_layout.addStretch()
        layout.addWidget(format_group)
        
        # Filter options
        filter_group = QGroupBox("필터 옵션", self)
        filter_layout = QVBoxLayout(filter_group)
        
        # Use current filters checkbox
        self.use_current_filters = CheckBox("현재 적용된 필터 사용", self)
        self.use_current_filters.setChecked(True)
        self.use_current_filters.stateChanged.connect(self._toggle_filters)
        filter_layout.addWidget(self.use_current_filters)
        
        # Platform filter
        platform_layout = QHBoxLayout()
        platform_label = BodyLabel("플랫폼:", self)
        self.platform_combo = ComboBox(self)
        self.platform_combo.addItems(["전체", "당근마켓", "번개장터", "중고나라"])
        self.platform_combo.setEnabled(False)
        platform_layout.addWidget(platform_label)
        platform_layout.addWidget(self.platform_combo)
        platform_layout.addStretch()
        filter_layout.addLayout(platform_layout)
        
        # Status filter
        status_layout = QHBoxLayout()
        status_label = BodyLabel("판매 상태:", self)
        self.status_combo = ComboBox(self)
        self.status_combo.addItems(["전체", "판매중", "예약중", "판매완료"])
        self.status_combo.setEnabled(False)
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_combo)
        status_layout.addStretch()
        filter_layout.addLayout(status_layout)
        
        # Include sold checkbox
        self.include_sold = CheckBox("판매완료 포함", self)
        self.include_sold.setChecked(True)
        self.include_sold.setEnabled(False)
        filter_layout.addWidget(self.include_sold)
        
        layout.addWidget(filter_group)
        
        # Date range
        date_group = QGroupBox("날짜 범위", self)
        date_layout = QHBoxLayout(date_group)
        
        self.use_date_range = CheckBox("날짜 필터", self)
        self.use_date_range.stateChanged.connect(self._toggle_dates)
        date_layout.addWidget(self.use_date_range)
        
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setEnabled(False)
        from_label = BodyLabel("부터", self)
        date_layout.addWidget(from_label)
        date_layout.addWidget(self.date_from)
        
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setEnabled(False)
        to_label = BodyLabel("까지", self)
        date_layout.addWidget(to_label)
        date_layout.addWidget(self.date_to)
        
        date_layout.addStretch()
        layout.addWidget(date_group)
        
        # Column selection
        col_group = QGroupBox("내보낼 항목", self)
        col_layout = QVBoxLayout(col_group)
        
        col_row1 = QHBoxLayout()
        self.col_title = CheckBox("제목")
        self.col_title.setChecked(True)
        self.col_price = CheckBox("가격")
        self.col_price.setChecked(True)
        self.col_platform = CheckBox("플랫폼")
        self.col_platform.setChecked(True)
        self.col_seller = CheckBox("판매자")
        self.col_seller.setChecked(True)
        
        for cb in [self.col_title, self.col_price, self.col_platform, self.col_seller]:
            col_row1.addWidget(cb)
        col_layout.addLayout(col_row1)
        
        col_row2 = QHBoxLayout()
        self.col_location = CheckBox("지역")
        self.col_location.setChecked(True)
        self.col_keyword = CheckBox("키워드")
        self.col_keyword.setChecked(True)
        self.col_date = CheckBox("등록일")
        self.col_date.setChecked(True)
        self.col_url = CheckBox("URL")
        self.col_url.setChecked(True)
        
        for cb in [self.col_location, self.col_keyword, self.col_date, self.col_url]:
            col_row2.addWidget(cb)
        col_layout.addLayout(col_row2)
        
        col_row3 = QHBoxLayout()
        self.col_status = CheckBox("판매상태")
        self.col_status.setChecked(True)
        self.col_note = CheckBox("메모")
        self.col_note.setChecked(False)
        self.col_tags = CheckBox("태그")
        self.col_tags.setChecked(False)
        
        for cb in [self.col_status, self.col_note, self.col_tags]:
            col_row3.addWidget(cb)
        col_row3.addStretch()
        col_layout.addLayout(col_row3)
        
        layout.addWidget(col_group)
        
        # Progress bar (hidden initially)
        self.progress = ProgressBar(self)
        self.progress.hide()
        layout.addWidget(self.progress)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = PushButton("취소", self)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.export_btn = PrimaryPushButton("내보내기", self)
        self.export_btn.clicked.connect(self._do_export)
        button_layout.addWidget(self.export_btn)
        
        layout.addLayout(button_layout)
