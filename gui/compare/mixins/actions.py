"""Mixin module: actions."""

"""Enhanced dialog for comparing multiple listings side by side."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QTextEdit, QMessageBox, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from gui.link_utils import open_external_url

class CompareActionsMixin:
    """Actions behavior."""

    def _on_cell_clicked(self, row, col):
        """Open link when link row is clicked"""
        if row == 7:  # Link row
            item = self.table.item(row, col)
            if item:
                url = item.data(Qt.ItemDataRole.UserRole)
                if url:
                    open_external_url(self, getattr(self.parent(), "engine", None), url, item.text())


    def _generate_comparison_text(self) -> str:
        """Generate text summary of comparison"""
        lines = ["📊 매물 비교 결과", "=" * 40, ""]

        for i, item in enumerate(self.listings):
            platform_icons = {
                'danggeun': '🥕 당근마켓',
                'bunjang': '⚡ 번개장터',
                'joonggonara': '🛒 중고나라'
            }

            lines.append(f"[매물 {i+1}]")
            lines.append(f"  플랫폼: {platform_icons.get(item.get('platform', ''), item.get('platform', ''))}")
            lines.append(f"  제목: {item.get('title', '-')}")
            lines.append(f"  가격: {item.get('price', '-')}")
            lines.append(f"  판매자: {item.get('seller', '-')}")
            lines.append(f"  지역: {item.get('location', '-')}")
            lines.append(f"  링크: {item.get('url', '-')}")
            lines.append("")

        # Add notes if any
        notes = self.notes_edit.toPlainText().strip()
        if notes:
            lines.append("📝 메모:")
            lines.append(notes)
            lines.append("")

        return "\n".join(lines)


    def _copy_to_clipboard(self):
        """Copy comparison to clipboard"""
        text = self._generate_comparison_text()
        clipboard = QApplication.clipboard()
        if clipboard is None:
            QMessageBox.warning(self, "오류", "클립보드를 사용할 수 없습니다.")
            return
        clipboard.setText(text)
        QMessageBox.information(self, "복사 완료", "📋 비교 내용이 클립보드에 복사되었습니다.")


    def _export_comparison(self):
        """Export comparison to text file"""
        from datetime import datetime

        default_name = f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "비교 결과 저장",
            default_name,
            "Text Files (*.txt)"
        )

        if file_path:
            try:
                text = self._generate_comparison_text()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, "저장 완료", f"📥 비교 결과가 저장되었습니다.\n\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"저장 중 오류가 발생했습니다:\n{str(e)}")
