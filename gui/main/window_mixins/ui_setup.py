# pyright: reportAttributeAccessIssue=false
"""Main-window UI construction (central widget, tabs, header)."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QStatusBar,
    QTabWidget, QVBoxLayout, QWidget,
)

from gui.favorites_widget import FavoritesWidget
from gui.keyword_manager import KeywordManagerWidget
from gui.listings_widget import ListingsWidget
from gui.log_widget import LogWidget
from gui.notification_history import NotificationHistoryWidget
from gui.stats_widget import StatsWidget


class UiSetupMixin(QWidget):
    """Builds the main window layout and header (needs widget attributes)."""

    def setup_ui(self):
        self.setWindowTitle("🥕 중고거래 알리미")
        self.setMinimumSize(950, 700)
        self.resize(1050, 750)

        # Apply stylesheet
        # Apply stylesheet
        self.apply_theme()

        central = QWidget()
        central.setStyleSheet("background-color: #1e1e2e;")
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self.create_header()
        layout.addWidget(header)

        # Content area
        content = QWidget()
        content.setStyleSheet("background-color: #1e1e2e;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(0)

        # Tab widget
        self.tabs = QTabWidget()

        self.keyword_widget = KeywordManagerWidget(self.settings_manager)
        self.tabs.addTab(self.keyword_widget, "🔍 키워드")

        self.listings_widget = ListingsWidget(self.engine)
        self.tabs.addTab(self.listings_widget, "📋 전체 매물")

        self.stats_widget = StatsWidget(self.engine)
        self.tabs.addTab(self.stats_widget, "📊 통계")

        self.favorites_widget = FavoritesWidget(self.engine)
        self.tabs.addTab(self.favorites_widget, "⭐ 즐겨찾기")

        self.history_widget = NotificationHistoryWidget(self.engine)
        self.tabs.addTab(self.history_widget, "📢 알림 내역")

        self.log_widget = LogWidget()
        self.log_widget.setup_logging()
        self.tabs.addTab(self.log_widget, "📋 로그")
        self.tabs.currentChanged.connect(self._on_tab_changed)

        content_layout.addWidget(self.tabs)
        layout.addWidget(content)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("준비됨")

    def create_header(self) -> QWidget:
        """Create the header with gradient background, logo, title, and enhanced controls"""
        from gui.components import PulsingDot

        header = QFrame()
        header.setObjectName("header")
        header.setStyleSheet("""
            QFrame#header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #181825, stop:0.5 #1e1e2e, stop:1 #181825);
                border-bottom: 1px solid rgba(137, 180, 250, 0.3);
            }
        """)
        header.setFixedHeight(80)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(16)

        # Logo with subtle glow effect
        logo = QLabel("🥕")
        logo.setStyleSheet("""
            font-size: 36pt;
            background: transparent;
            padding: 4px;
        """)
        layout.addWidget(logo)

        # Title section
        title_widget = QWidget()
        title_widget.setStyleSheet("background: transparent;")
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        title = QLabel("중고거래 알리미")
        title.setStyleSheet("""
            font-size: 20pt;
            font-weight: bold;
            color: #cdd6f4;
            background: transparent;
        """)
        title_layout.addWidget(title)

        subtitle = QLabel("🥕 당근마켓  ·  ⚡ 번개장터  ·  🛒 중고나라")
        subtitle.setStyleSheet("""
            font-size: 10pt;
            color: #6c7086;
            background: transparent;
        """)
        title_layout.addWidget(subtitle)

        layout.addWidget(title_widget)
        layout.addStretch()

        # Last search time indicator
        self.last_search_label = QLabel("마지막 검색: -")
        self.last_search_label.setStyleSheet("""
            color: #6c7086;
            font-size: 9pt;
            background: transparent;
            padding: 4px 8px;
        """)
        layout.addWidget(self.last_search_label)

        # Status indicator with glass effect
        self.status_frame = QFrame()
        self.status_frame.setObjectName("statusIndicator")
        self.status_frame.setStyleSheet("""
            QFrame#statusIndicator {
                background-color: rgba(49, 50, 68, 0.8);
                border: 1px solid rgba(69, 71, 90, 0.5);
                border-radius: 18px;
            }
        """)
        status_layout = QHBoxLayout(self.status_frame)
        status_layout.setContentsMargins(14, 6, 14, 6)
        status_layout.setSpacing(8)

        # Use PulsingDot component
        self.status_dot = PulsingDot("#6c7086")
        status_layout.addWidget(self.status_dot)

        self.status_text = QLabel("대기 중")
        self.status_text.setStyleSheet("""
            color: #a6adc8;
            font-size: 10pt;
            background: transparent;
        """)
        status_layout.addWidget(self.status_text)

        layout.addWidget(self.status_frame)

        # Start button with gradient
        self.start_btn = QPushButton("▶️ 시작")
        self.start_btn.setObjectName("success")
        self.start_btn.setMinimumWidth(110)
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setToolTip("모니터링 시작/중지 (Ctrl+S)")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a6e3a1, stop:1 #94e2d5);
                color: #1e1e2e;
                border: none;
                padding: 10px 24px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #94e2d5, stop:1 #89dceb);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #89dceb, stop:1 #74c7ec);
            }
        """)
        self.start_btn.clicked.connect(self.toggle_monitoring)
        layout.addWidget(self.start_btn)

        # Settings button with glass effect
        settings_btn = QPushButton("⚙️ 설정")
        settings_btn.setMinimumHeight(40)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setToolTip("알림, 테마, 스케줄 설정 (Ctrl+,)")
        settings_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #45475a, stop:1 #313244);
                color: #cdd6f4;
                border: 1px solid rgba(69, 71, 90, 0.5);
                padding: 10px 20px;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #585b70, stop:1 #45475a);
                border: 1px solid rgba(137, 180, 250, 0.4);
            }
        """)
        settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(settings_btn)

        return header


__all__ = ["UiSetupMixin"]
