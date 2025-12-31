# export_manager.py
"""Data export manager"""

import csv
import logging
from typing import List, Dict, Any
from datetime import datetime

class ExportManager:
    """Manages data export to various formats"""
    
    @staticmethod
    def export_to_csv(data: List[Dict[str, Any]], filename: str, fields: List[str] = None) -> bool:
        """Export list of dicts to CSV"""
        if not data:
            return False
            
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
            return True
        except Exception as e:
            logging.error(f"CSV export failed: {e}")
            return False

    @staticmethod
    def export_to_excel(data: List[Dict[str, Any]], filename: str, fields: List[str] = None) -> bool:
        """Export list of dicts to Excel"""
        try:
            import openpyxl
        except ImportError:
            logging.error("openpyxl not installed")
            return False
            
        if not data:
            return False
            
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            
            if not fields:
                fields = list(data[0].keys())
            
            # Header
            ws.append(fields)
            
            # Data
            for row in data:
                values = [row.get(k) for k in fields]
                ws.append(values)
            
            wb.save(filename)
            return True
        except Exception as e:
            logging.error(f"Excel export failed: {e}")
            return False
