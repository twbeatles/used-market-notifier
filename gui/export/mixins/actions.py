"""Mixin module: actions."""

"""Enhanced export dialog with filtering options."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QCheckBox, QComboBox, QDateEdit, QRadioButton,
    QButtonGroup, QFileDialog, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from typing import Mapping
from export_manager import ExportManager

class ExportActionsMixin:
    """Actions behavior."""

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
