"""Settings dialog mixin: seller."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QLineEdit, QSpinBox, QCheckBox, QLabel,
    QGroupBox, QPushButton, QComboBox, QMessageBox, QFrame,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class SellerSettingsMixin:
    """Seller settings panel behavior."""

    def create_seller_tab(self) -> QWidget:
        """Create tab for managing blocked sellers"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        desc = QLabel("🚫 차단된 판매자 목록 (이 판매자들의 상품은 알림이 오지 않습니다)")
        desc.setStyleSheet("color: #89b4fa;")
        layout.addWidget(desc)

        self.seller_table = QTableWidget()
        self.seller_table.setColumnCount(3)
        self.seller_table.setHorizontalHeaderLabels(["플랫폼", "판매자명", "차단일"])
        seller_h_header = self.seller_table.horizontalHeader()
        if seller_h_header is not None:
            seller_h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.seller_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.seller_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.seller_table)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        unblock_btn = QPushButton("🔓 차단 해제")
        unblock_btn.setToolTip("선택한 판매자의 차단을 해제합니다")
        unblock_btn.clicked.connect(self.unblock_seller)
        btn_row.addWidget(unblock_btn)

        layout.addLayout(btn_row)

        return widget


    def load_blocked_sellers(self):
        """Load blocked sellers from DB"""
        db = self._get_parent_db()
        if db is None:
            return

        try:
            sellers = db.get_blocked_sellers()
            self.seller_table.setRowCount(len(sellers))
            for i, seller in enumerate(sellers):
                self.seller_table.setItem(i, 0, QTableWidgetItem(seller['platform']))
                self.seller_table.setItem(i, 1, QTableWidgetItem(seller['seller_name']))
                created_at = seller.get('created_at', '') or ''
                created_str = created_at[:10] if isinstance(created_at, str) else str(created_at)
                self.seller_table.setItem(i, 2, QTableWidgetItem(created_str))
        except Exception as e:
            print(f"Error loading sellers: {e}")


    def unblock_seller(self):
        """Unblock selected seller"""
        row = self.seller_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "알림", "차단 해제할 판매자를 선택하세요.")
            return
        platform_item = self.seller_table.item(row, 0)
        seller_item = self.seller_table.item(row, 1)
        if platform_item is None or seller_item is None:
            QMessageBox.warning(self, "오류", "선택한 행 데이터가 올바르지 않습니다.")
            return
        platform = platform_item.text()
        seller = seller_item.text()

        if QMessageBox.question(self, "확인", f"'{seller}' 판매자의 차단을 해제하시겠습니까?") == QMessageBox.StandardButton.Yes:
            try:
                db = self._get_parent_db()
                if db is None:
                    raise RuntimeError("데이터베이스 연결을 찾을 수 없습니다.")
                db.remove_seller_filter(seller, platform)
                self.load_blocked_sellers()
                QMessageBox.information(self, "완료", "차단이 해제되었습니다.")
            except Exception as e:
                QMessageBox.warning(self, "오류", f"차단 해제 실패: {e}")
