from typing import TYPE_CHECKING
"""Mixin module: ui."""

"""Enhanced dialog for comparing multiple listings side by side."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QTextEdit, QMessageBox, QFileDialog, QApplication
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    PrimaryPushButton,
    PushButton,
    StrongBodyLabel,
    SubtitleLabel,
    TextEdit,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from gui.link_utils import open_external_url


if TYPE_CHECKING:
    from gui.compare.dialog import CompareDialog
    _HostBase_CompareUiMixin = CompareDialog
else:
    _HostBase_CompareUiMixin = object

class CompareUiMixin(_HostBase_CompareUiMixin):
    """Ui behavior."""

    def setup_ui(self):
        self.setWindowTitle("매물 비교")
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header
        header = QHBoxLayout()
        header.addWidget(SubtitleLabel(f"매물 비교 ({len(self.listings)}개)", self))
        header.addStretch()

        # Copy comparison button
        copy_btn = PrimaryPushButton("복사", self)
        copy_btn.setToolTip("비교 내용을 클립보드에 복사")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        header.addWidget(copy_btn)

        # Export button
        export_btn = PushButton("저장", self)
        export_btn.setToolTip("비교 결과를 텍스트 파일로 저장")
        export_btn.clicked.connect(self._export_comparison)
        header.addWidget(export_btn)

        close_btn = PushButton("닫기", self)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Price comparison bar chart (simple visual representation)
        price_frame = QFrame(self)
        price_layout = QHBoxLayout(price_frame)
        price_layout.setContentsMargins(16, 12, 16, 12)

        price_title = StrongBodyLabel("가격 비교:", self)
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
            if price == min_price and min_price > 0:
                price_label = StrongBodyLabel(f"{price_str} (최저가)", bar_widget)
            else:
                price_label = BodyLabel(price_str, bar_widget)

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
            num_label = CaptionLabel(f"매물 {i+1}", bar_widget)
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
                'danggeun': '당근마켓',
                'bunjang': '번개장터',
                'joonggonara': '중고나라'
            }

            # Row 0: Platform
            self.table.setItem(0, col, QTableWidgetItem(
                str(platform_icons.get(item.get('platform', ''), item.get('platform', '')) or "")
            ))

            # Row 1: Title
            title_item = QTableWidgetItem(item.get('title', ''))
            title_item.setToolTip(item.get('title', ''))  # Show full title on hover
            self.table.setItem(1, col, title_item)

            # Row 2: Price
            price_item = QTableWidgetItem(item.get('price', ''))
            if prices[col] == min_price and min_price > 0:
                price_item.setBackground(QColor("#2a4d3e"))
                price_item.setText(f"{item.get('price', '')} (최저가)")
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
                'for_sale': '판매중',
                'reserved': '예약중',
                'sold': '판매완료',
            }
            status = item.get('sale_status', 'for_sale')
            self.table.setItem(6, col, QTableWidgetItem(status_map.get(status, status or '알수없음')))

            # Row 7: Link
            link_item = QTableWidgetItem("열기")
            link_item.setData(Qt.ItemDataRole.UserRole, item.get('url', ''))
            self.table.setItem(7, col, link_item)

        # Style
        h_header = self.table.horizontalHeader()
        if h_header is not None:
            h_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        v_header = self.table.verticalHeader()
        if v_header is not None:
            v_header.setDefaultSectionSize(45)
        self.table.cellDoubleClicked.connect(self._on_cell_clicked)

        layout.addWidget(self.table)

        # Notes section
        notes_frame = QFrame(self)
        notes_layout = QVBoxLayout(notes_frame)
        notes_layout.setContentsMargins(12, 12, 12, 12)

        notes_label = StrongBodyLabel("비교 메모:", notes_frame)
        notes_layout.addWidget(notes_label)

        self.notes_edit = TextEdit(notes_frame)
        self.notes_edit.setPlaceholderText("비교하면서 메모할 내용을 입력하세요...")
        self.notes_edit.setMaximumHeight(80)
        notes_layout.addWidget(self.notes_edit)

        layout.addWidget(notes_frame)
