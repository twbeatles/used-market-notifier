# gui/export_dialog.py
"""Enhanced export dialog with filtering options"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QCheckBox, QComboBox, QDateEdit, QRadioButton,
    QButtonGroup, QFileDialog, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from typing import Mapping


class ExportDialog(QDialog):
    """Dialog for configuring and executing data export"""
    
    def __init__(self, db, current_filters: Mapping[str, object] | None = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_filters = current_filters or {}
        self.setup_ui()
    
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
    
    def _toggle_filters(self, state):
        enabled = state != 2  # Qt.CheckState.Checked
        self.platform_combo.setEnabled(enabled)
        self.status_combo.setEnabled(enabled)
        self.include_sold.setEnabled(enabled)
    
    def _toggle_dates(self, state):
        enabled = state == 2  # Qt.CheckState.Checked
        self.date_from.setEnabled(enabled)
        self.date_to.setEnabled(enabled)
    
    def _get_selected_fields(self) -> list[str]:
        fields: list[str] = []
        field_map = {
            'title': self.col_title,
            'price': self.col_price,
            'platform': self.col_platform,
            'seller': self.col_seller,
            'location': self.col_location,
            'keyword': self.col_keyword,
            'created_at': self.col_date,
            'url': self.col_url,
            'sale_status': self.col_status,
            'note': self.col_note,
            'auto_tags': self.col_tags,
        }
        
        for field, checkbox in field_map.items():
            if checkbox.isChecked():
                fields.append(field)
        
        return fields
    
    def _do_export(self):
        # Get filters
        platform_map = {
            "전체": None,
            "당근마켓": "danggeun",
            "번개장터": "bunjang",
            "중고나라": "joonggonara"
        }
        status_map = {
            "전체": None,
            "판매중": "for_sale",
            "예약중": "reserved",
            "판매완료": "sold"
        }
        
        if self.use_current_filters.isChecked():
            platform = self.current_filters.get('platform')
            status = self.current_filters.get('status')
            include_sold = self.current_filters.get('include_sold', True)
            search = self.current_filters.get('search')
        else:
            platform = platform_map.get(self.platform_combo.currentText())
            status = status_map.get(self.status_combo.currentText())
            include_sold = self.include_sold.isChecked()
            search = None
        
        date_from = None
        date_to = None
        if self.use_date_range.isChecked():
            date_from = self.date_from.date().toString("yyyy-MM-dd")
            date_to = self.date_to.date().toString("yyyy-MM-dd")
        
        # Get data from database
        try:
            self.progress.show()
            self.progress.setValue(20)
            
            data = self.db.get_listings_for_export(
                platform=platform,
                search=search,
                status=status,
                date_from=date_from,
                date_to=date_to,
                include_sold=include_sold
            )
            
            self.progress.setValue(50)
            
            if not data:
                QMessageBox.warning(self, "알림", "내보낼 데이터가 없습니다.")
                self.progress.hide()
                return
            
            # Get file path
            is_excel = self.excel_radio.isChecked()
            ext = "xlsx" if is_excel else "csv"
            default_name = f"listings_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "내보내기 파일 저장",
                default_name,
                f"{'Excel Files (*.xlsx)' if is_excel else 'CSV Files (*.csv)'}"
            )
            
            if not file_path:
                self.progress.hide()
                return
            
            self.progress.setValue(70)
            
            # Export
            from export_manager import ExportManager
            fields: list[str] = self._get_selected_fields()
            
            # Map Korean field names
            field_names: dict[str, str] = {
                'title': '제목',
                'price': '가격',
                'platform': '플랫폼',
                'seller': '판매자',
                'location': '지역',
                'keyword': '키워드',
                'created_at': '등록일',
                'url': 'URL',
                'sale_status': '판매상태',
                'note': '메모',
                'auto_tags': '태그'
            }
            
            # Prepare export data with Korean headers
            export_data = []
            for item in data:
                row = {}
                for f in fields:
                    key = field_names.get(f, f)
                    value = item.get(f, '')
                    # Format sale status
                    if f == 'sale_status':
                        status_names = {
                            'for_sale': '판매중',
                            'reserved': '예약중',
                            'sold': '판매완료',
                            'unknown': '알수없음'
                        }
                        value = status_names.get(value, value)
                    row[key] = value
                export_data.append(row)
            
            if is_excel:
                success, message = ExportManager.export_to_excel(
                    export_data, 
                    file_path, 
                    [field_names.get(f, f) for f in fields]
                )
            else:
                success, message = ExportManager.export_to_csv(
                    export_data, 
                    file_path, 
                    [field_names.get(f, f) for f in fields]
                )
            
            self.progress.setValue(100)
            
            if success:
                QMessageBox.information(
                    self, 
                    "완료", 
                    f"✅ {message}\n\n파일: {file_path}"
                )
                self.accept()
            else:
                QMessageBox.critical(self, "오류", f"내보내기 실패: {message}")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"내보내기 중 오류가 발생했습니다:\n{str(e)}")
        finally:
            self.progress.hide()
    
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
