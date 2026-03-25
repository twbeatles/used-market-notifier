"""Notification history widget."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor, QDesktopServices
from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class NotificationHistoryWidget(QWidget):
    """Widget to display notification history and channel health."""

    CHANNEL_NAMES = ("telegram", "discord", "slack")

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.db = engine.db
        self.health_labels: dict[str, QLabel] = {}
        self.setup_ui()

    def set_engine(self, engine):
        """Set or update the monitor engine (and DB reference)."""
        self.engine = engine
        self.db = engine.db if engine else None
        self.refresh_list()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        title = QLabel("알림 이력")
        title.setObjectName("title")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.type_filter = QComboBox()
        self.type_filter.addItem("전체 알림", "all")
        self.type_filter.addItem("Telegram", "telegram")
        self.type_filter.addItem("Discord", "discord")
        self.type_filter.addItem("Slack", "slack")
        self.type_filter.currentTextChanged.connect(self.refresh_list)
        header_layout.addWidget(self.type_filter)

        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.refresh_list)
        header_layout.addWidget(refresh_btn)
        layout.addLayout(header_layout)

        health_group = QGroupBox("채널 헬스 요약 (최근 7일)")
        health_layout = QGridLayout(health_group)
        health_layout.setHorizontalSpacing(16)
        health_layout.setVerticalSpacing(12)

        for index, channel in enumerate(self.CHANNEL_NAMES):
            label = QLabel()
            label.setWordWrap(True)
            label.setStyleSheet(
                "QLabel { background-color: #181825; border: 1px solid #313244; "
                "border-radius: 8px; padding: 10px; }"
            )
            self.health_labels[channel] = label
            health_layout.addWidget(label, 0, index)

        layout.addWidget(health_group)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["시간", "플랫폼", "채널", "제목", "미리보기"])
        h_header = self.table.horizontalHeader()
        if h_header is not None:
            h_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 300)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        v_header = self.table.verticalHeader()
        if v_header is not None:
            v_header.setVisible(False)
        self.table.setStyleSheet(
            """
            QTableWidget {
                background-color: #1e1e2e;
                alternate-background-color: #313244;
                gridline-color: #45475a;
                border: none;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:hover {
                background-color: #45475a;
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
            }
            """
        )
        self.table.cellDoubleClicked.connect(self.on_double_click)
        layout.addWidget(self.table)

        self.refresh_list()

    def refresh_summary(self):
        if not self.db:
            return
        summary = self.db.get_notification_delivery_summary(days=7)
        for channel in self.CHANNEL_NAMES:
            row = summary.get(channel, {})
            success_count = int(row.get("success_count") or 0)
            failed_count = int(row.get("failed_count") or 0)
            success_rate = float(row.get("success_rate") or 0.0)
            last_success = row.get("last_success_at") or "-"
            last_failure_message = row.get("last_failure_message") or "-"
            last_rate_limited = row.get("last_rate_limited_at") or "-"
            self.health_labels[channel].setText(
                "\n".join(
                    [
                        channel.capitalize(),
                        f"성공 {success_count} / 실패 {failed_count}",
                        f"성공률 {success_rate:.1f}%",
                        f"마지막 성공: {last_success}",
                        f"마지막 실패: {last_failure_message}",
                        f"마지막 429: {last_rate_limited}",
                    ]
                )
            )

    def refresh_list(self):
        if not self.db:
            return

        self.refresh_summary()
        logs = self.db.get_notification_logs(limit=100)
        filter_type = self.type_filter.currentData()
        if filter_type != "all":
            logs = [row for row in logs if row["notification_type"] == filter_type]

        self.table.setRowCount(len(logs))
        for row_index, item in enumerate(logs):
            self.table.setItem(row_index, 0, QTableWidgetItem(item["sent_at"]))
            self.table.setItem(row_index, 1, QTableWidgetItem(item.get("platform", "")))

            type_item = QTableWidgetItem(item["notification_type"].capitalize())
            if item["notification_type"] == "telegram":
                type_item.setForeground(QColor("#58a6ff"))
            elif item["notification_type"] == "discord":
                type_item.setForeground(QColor("#7289da"))
            elif item["notification_type"] == "slack":
                type_item.setForeground(QColor("#e01e5a"))
            self.table.setItem(row_index, 2, type_item)

            title_item = QTableWidgetItem(item.get("title", ""))
            title_item.setData(Qt.ItemDataRole.UserRole, item.get("url"))
            self.table.setItem(row_index, 3, title_item)

            self.table.setItem(row_index, 4, QTableWidgetItem(item.get("message_preview", "")))

    def on_double_click(self, row, col):
        _ = col
        title_item = self.table.item(row, 3)
        if not title_item:
            return

        url = title_item.data(Qt.ItemDataRole.UserRole)
        if not url:
            return

        if hasattr(self.engine, "settings") and self.engine.settings.settings.confirm_link_open:
            confirm = QMessageBox.question(
                self,
                "링크 열기",
                f"다음 링크로 이동할까요?\n{url}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

        QDesktopServices.openUrl(QUrl(str(url)))
