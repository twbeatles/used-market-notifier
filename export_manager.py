# export_manager.py
"""Data export manager with detailed error messages"""

import csv
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime


class ExportManager:
    """Manages data export to various formats"""
    
    @staticmethod
    def export_to_csv(data: List[Dict[str, Any]], filename: str, fields: List[str] = None) -> Tuple[bool, str]:
        """
        Export list of dicts to CSV.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not data:
            return False, "내보낼 데이터가 없습니다."
            
        try:
            if not fields:
                fields = list(data[0].keys())
                
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                for row in data:
                    # Filter row to only include requested fields
                    filtered = {k: row.get(k) for k in fields}
                    writer.writerow(filtered)
            return True, f"{len(data):,}개 항목을 저장했습니다."
        except PermissionError:
            msg = "파일 쓰기 권한이 없습니다. 다른 프로그램에서 파일을 사용 중인지 확인하세요."
            logging.error(f"CSV export failed: {msg}")
            return False, msg
        except OSError as e:
            msg = f"파일 저장 실패: {e.strerror}"
            logging.error(f"CSV export failed: {msg}")
            return False, msg
        except Exception as e:
            msg = f"내보내기 실패: {str(e)}"
            logging.error(f"CSV export failed: {e}")
            return False, msg

    @staticmethod
    def export_to_excel(data: List[Dict[str, Any]], filename: str, fields: List[str] = None) -> Tuple[bool, str]:
        """
        Export list of dicts to Excel.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            import openpyxl
        except ImportError:
            msg = "openpyxl 패키지가 설치되어 있지 않습니다. 'pip install openpyxl'을 실행하세요."
            logging.error(msg)
            return False, msg
            
        if not data:
            return False, "내보낼 데이터가 없습니다."
            
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "매물 목록"
            
            if not fields:
                fields = list(data[0].keys())
            
            # Header with styling
            ws.append(fields)
            
            # Data
            for row in data:
                values = [row.get(k) for k in fields]
                ws.append(values)
            
            # Auto-adjust column widths (approximate)
            for i, field in enumerate(fields, 1):
                max_length = len(str(field))
                for row in data[:50]:  # Check first 50 rows for performance
                    cell_value = str(row.get(field, ''))
                    if len(cell_value) > max_length:
                        max_length = min(len(cell_value), 50)  # Cap at 50 chars
                ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = max_length + 2
            
            wb.save(filename)
            return True, f"{len(data):,}개 항목을 저장했습니다."
        except PermissionError:
            msg = "파일 쓰기 권한이 없습니다. 다른 프로그램에서 파일을 사용 중인지 확인하세요."
            logging.error(f"Excel export failed: {msg}")
            return False, msg
        except OSError as e:
            msg = f"파일 저장 실패: {e.strerror}"
            logging.error(f"Excel export failed: {msg}")
            return False, msg
        except Exception as e:
            msg = f"내보내기 실패: {str(e)}"
            logging.error(f"Excel export failed: {e}")
            return False, msg
