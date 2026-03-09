# gui/compare_dialog.py
"""Enhanced dialog for comparing multiple listings side by side"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QTextEdit, QMessageBox, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QColor


class CompareDialog(QDialog):
    """Enhanced dialog to compare selected listings side by side"""
    
    def __init__(self, listings: list, parent=None):
        super().__init__(parent)
        self.listings = listings
        self.notes = {}  # Row notes for comparison
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("📊 매물 비교")
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)
        self.setStyleSheet("QDialog { background-color: #1e1e2e; }")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QHBoxLayout()
        title = QLabel(f"📊 매물 비교 ({len(self.listings)}개)")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #cdd6f4;")
        header.addWidget(title)
        header.addStretch()
        
        # Copy comparison button
        copy_btn = QPushButton("📋 복사")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #b4befe; }
        """)
        copy_btn.setToolTip("비교 내용을 클립보드에 복사")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        header.addWidget(copy_btn)
        
        # Export button
        export_btn = QPushButton("📥 저장")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #f9e2af;
                color: #1e1e2e;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #fab387; }
        """)
        export_btn.setToolTip("비교 결과를 텍스트 파일로 저장")
        export_btn.clicked.connect(self._export_comparison)
        header.addWidget(export_btn)
        
        close_btn = QPushButton("✖ 닫기")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #585b70; }
        """)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)
        
        # Price comparison bar chart (simple visual representation)
        price_frame = QFrame()
        price_frame.setStyleSheet("""
            QFrame {
                background-color: #313244;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        price_layout = QHBoxLayout(price_frame)
        price_layout.setContentsMargins(16, 12, 16, 12)
        
        price_title = QLabel("💰 가격 비교:")
        price_title.setStyleSheet("color: #cdd6f4; font-weight: bold;")
        price_layout.addWidget(price_title)
        
        # Get prices and find min/max
        prices = []
        for item in self.listings:
            price_num = item.get('price_numeric', 0)
            if not price_num:
                # Try to parse from price string
                price_str = item.get('price', '')
                try:
                    price_num = int(''.join(c for c in price_str if c.isdigit()) or '0')
                except:
                    price_num = 0
            prices.append(price_num)
        
        max_price = max(prices) if prices and max(prices) > 0 else 1
        min_price = min(p for p in prices if p > 0) if any(p > 0 for p in prices) else 0
        
        for i, (item, price) in enumerate(zip(self.listings, prices)):
            bar_widget = QFrame()
            bar_layout = QVBoxLayout(bar_widget)
            bar_layout.setSpacing(4)
            bar_layout.setContentsMargins(8, 0, 8, 0)
            
            # Price label
            price_str = item.get('price', '가격미정')
            price_label = QLabel(price_str)
            
            # Highlight lowest price
            if price == min_price and min_price > 0:
                price_label.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 11pt;")
                price_label.setText(f"⭐ {price_str}")
            else:
                price_label.setStyleSheet("color: #cdd6f4; font-size: 10pt;")
            
            bar_layout.addWidget(price_label, alignment=Qt.AlignmentFlag.AlignCenter)
            
            # Bar
            bar_height = int((price / max_price) * 40) if max_price > 0 and price > 0 else 5
            bar = QFrame()
            bar_color = "#a6e3a1" if price == min_price and min_price > 0 else "#89b4fa"
            bar.setStyleSheet(f"""
                background-color: {bar_color};
                border-radius: 4px;
                min-width: 60px;
                min-height: {bar_height}px;
                max-height: {bar_height}px;
            """)
            bar_layout.addWidget(bar, alignment=Qt.AlignmentFlag.AlignCenter)
            
            # Item number
            num_label = QLabel(f"매물 {i+1}")
            num_label.setStyleSheet("color: #6c7086; font-size: 9pt;")
            bar_layout.addWidget(num_label, alignment=Qt.AlignmentFlag.AlignCenter)
            
            price_layout.addWidget(bar_widget)
        
        price_layout.addStretch()
        layout.addWidget(price_frame)
        
        # Comparison table (rows = attributes, columns = items)
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.listings))
        self.table.setRowCount(8)  # Platform, Title, Price, Seller, Location, Date, Status, Link
        
        # Row headers
        row_labels = ["플랫폼", "제목", "가격", "판매자", "지역", "등록일", "상태", "링크"]
        self.table.setVerticalHeaderLabels(row_labels)
        
        # Column headers (item numbers)
        col_labels = [f"매물 {i+1}" for i in range(len(self.listings))]
        self.table.setHorizontalHeaderLabels(col_labels)
        
        # Fill data
        for col, item in enumerate(self.listings):
            platform_icons = {
                'danggeun': '🥕 당근마켓',
                'bunjang': '⚡ 번개장터',
                'joonggonara': '🛒 중고나라'
            }
            
            # Row 0: Platform
            self.table.setItem(0, col, QTableWidgetItem(
                platform_icons.get(item.get('platform', ''), item.get('platform', ''))
            ))
            
            # Row 1: Title
            title_item = QTableWidgetItem(item.get('title', ''))
            title_item.setToolTip(item.get('title', ''))  # Show full title on hover
            self.table.setItem(1, col, title_item)
            
            # Row 2: Price
            price_item = QTableWidgetItem(item.get('price', ''))
            if prices[col] == min_price and min_price > 0:
                price_item.setBackground(QColor("#2a4d3e"))
                price_item.setText(f"⭐ {item.get('price', '')} (최저가)")
            self.table.setItem(2, col, price_item)
            
            # Row 3: Seller
            self.table.setItem(3, col, QTableWidgetItem(item.get('seller', '-')))
            
            # Row 4: Location
            self.table.setItem(4, col, QTableWidgetItem(item.get('location', '-')))
            
            # Row 5: Date
            created = item.get('created_at', '')
            if created:
                created = created[:10]  # Just the date part
            self.table.setItem(5, col, QTableWidgetItem(created or '-'))
            
            # Row 6: Status
            status_map = {
                'for_sale': '🟢 판매중',
                'reserved': '🟡 예약중',
                'sold': '🔴 판매완료',
            }
            status = item.get('sale_status', 'for_sale')
            self.table.setItem(6, col, QTableWidgetItem(status_map.get(status, status or '알수없음')))
            
            # Row 7: Link
            link_item = QTableWidgetItem("🔗 열기")
            link_item.setData(Qt.ItemDataRole.UserRole, item.get('url', ''))
            self.table.setItem(7, col, link_item)
        
        # Style
        h_header = self.table.horizontalHeader()
        if h_header is not None:
            h_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        v_header = self.table.verticalHeader()
        if v_header is not None:
            v_header.setDefaultSectionSize(45)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e2e;
                gridline-color: #45475a;
                border: none;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 8px;
                color: #cdd6f4;
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
        self.table.cellDoubleClicked.connect(self._on_cell_clicked)
        
        layout.addWidget(self.table)
        
        # Notes section
        notes_frame = QFrame()
        notes_frame.setStyleSheet("""
            QFrame {
                background-color: #313244;
                border-radius: 8px;
            }
        """)
        notes_layout = QVBoxLayout(notes_frame)
        notes_layout.setContentsMargins(12, 12, 12, 12)
        
        notes_label = QLabel("📝 비교 메모:")
        notes_label.setStyleSheet("color: #cdd6f4; font-weight: bold;")
        notes_layout.addWidget(notes_label)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("비교하면서 메모할 내용을 입력하세요...")
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        notes_layout.addWidget(self.notes_edit)
        
        layout.addWidget(notes_frame)
    
    def _on_cell_clicked(self, row, col):
        """Open link when link row is clicked"""
        if row == 7:  # Link row
            item = self.table.item(row, col)
            if item:
                url = item.data(Qt.ItemDataRole.UserRole)
                if url:
                    QDesktopServices.openUrl(QUrl(url))
    
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
