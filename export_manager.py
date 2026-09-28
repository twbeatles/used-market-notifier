# export_manager.py
"""Data export manager with detailed error messages"""

import csv
import logging
from typing import Any, Mapping, Sequence

# 스프레드시트가 수식으로 해석하는 선행 문자 (OWASP CSV Injection)
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def sanitize_cell(value: Any) -> Any:
    """Neutralize text that a spreadsheet would evaluate as a formula.

    Listing titles, sellers and locations come from marketplace users, so a
    value such as ``=HYPERLINK(...)`` must be exported as literal text.
    """
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


class ExportManager:
    """Manages data export to various formats"""
    
    @staticmethod
    def export_to_csv(
        data: Sequence[Mapping[str, Any]],
        filename: str,
        fields: Sequence[str] | None = None,
    ) -> tuple[bool, str]:
        """
        Export list of dicts to CSV.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not data:
            return False, "내보낼 데이터가 없습니다."
            
        try:
            field_names = list(fields) if fields else list(data[0].keys())
                
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=field_names)
                writer.writeheader()
                for row in data:
                    # Filter row to only include requested fields
                    filtered = {k: sanitize_cell(row.get(k)) for k in field_names}
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
    def export_to_excel(
        data: Sequence[Mapping[str, Any]],
        filename: str,
        fields: Sequence[str] | None = None,
    ) -> tuple[bool, str]:
        """
        Export list of dicts to Excel.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            from openpyxl import Workbook
            from openpyxl.utils import get_column_letter
        except ImportError:
            msg = "openpyxl 패키지가 설치되어 있지 않습니다. 'pip install openpyxl'을 실행하세요."
            logging.error(msg)
            return False, msg
            
        if not data:
            return False, "내보낼 데이터가 없습니다."
            
        try:
            wb = Workbook()
            ws = wb.active
            if ws is None:
                return False, "내보내기 실패: 워크시트를 생성하지 못했습니다."
            ws.title = "매물 목록"
            
            field_names = list(fields) if fields else list(data[0].keys())
            
            # Header with styling
            ws.append(field_names)
            
            # Data
            for row in data:
                ws.append([sanitize_cell(row.get(k)) for k in field_names])
                for cell in ws[ws.max_row]:
                    if isinstance(cell.value, str):
                        cell.data_type = "s"  # never store listing text as a formula
            
            # Auto-adjust column widths (approximate)
            for i, field in enumerate(field_names, 1):
                max_length = len(str(field))
                for row in data[:50]:  # Check first 50 rows for performance
                    cell_value = str(row.get(field, ''))
                    if len(cell_value) > max_length:
                        max_length = min(len(cell_value), 50)  # Cap at 50 chars
                ws.column_dimensions[get_column_letter(i)].width = max_length + 2
            
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
