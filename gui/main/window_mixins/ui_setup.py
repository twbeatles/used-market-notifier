# pyright: reportAttributeAccessIssue=false
"""Fluent navigation construction (MSFluentWindow + addSubInterface)."""

import contextlib

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import NavigationItemPosition, setThemeColor

from gui.design_tokens import (
    SCREEN_MARGIN,
    WINDOW_DEFAULT_HEIGHT,
    WINDOW_DEFAULT_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
from gui.favorites_widget import FavoritesWidget
from gui.fluent_theme import apply_native_widget_style, configure_fluent_window
from gui.icon import get_app_icon
from gui.keyword_manager import KeywordManagerWidget
from gui.listings_widget import ListingsWidget
from gui.log_widget import LogWidget
from gui.notification_history import NotificationHistoryWidget
from gui.pages import HostPage, MonitorPage, SettingsPage, UpdatePage
from gui.stats_widget import StatsWidget
from version import __version__


def preferred_window_size(avail_width: int, avail_height: int) -> tuple[int, int]:
    width = min(WINDOW_DEFAULT_WIDTH, max(WINDOW_MIN_WIDTH, avail_width - SCREEN_MARGIN))
    height = min(WINDOW_DEFAULT_HEIGHT, max(WINDOW_MIN_HEIGHT, avail_height - SCREEN_MARGIN))
    return width, height


class UiSetupMixin(QWidget):
    """Builds Fluent navigation pages (needs settings/engine attributes)."""

    def setup_ui(self):
        configure_fluent_window(self)
        setThemeColor("#0078D4")

        self.create_header()

        screen = QGuiApplication.primaryScreen()
        avail = screen.availableGeometry() if screen is not None else None
        width, height = preferred_window_size(
            avail.width() if avail is not None else WINDOW_DEFAULT_WIDTH,
            avail.height() if avail is not None else WINDOW_DEFAULT_HEIGHT,
        )
        self.resize(width, height)
        self.setMinimumSize(
            min(WINDOW_MIN_WIDTH, width),
            min(WINDOW_MIN_HEIGHT, height),
        )

        self.monitor_page = MonitorPage(self)
        self.monitor_page.start_btn.clicked.connect(self.toggle_monitoring)

        self.keyword_widget = KeywordManagerWidget(self.settings_manager)
        self.keyword_page = HostPage(self.keyword_widget, "keywordInterface", self)

        self.listings_widget = ListingsWidget(self.engine)
        self.listings_page = HostPage(self.listings_widget, "listingsInterface", self)

        self.favorites_widget = FavoritesWidget(self.engine)
        self.favorites_page = HostPage(self.favorites_widget, "favoritesInterface", self)

        self.stats_widget = StatsWidget(self.engine)
        self.stats_page = HostPage(self.stats_widget, "statsInterface", self)

        self.history_widget = NotificationHistoryWidget(self.engine)
        self.history_page = HostPage(self.history_widget, "historyInterface", self)

        self.log_widget = LogWidget()
        self.log_widget.setup_logging()
        self.log_page = HostPage(self.log_widget, "logInterface", self)

        self.settings_page = SettingsPage(self.settings_manager, self)
        self.update_page = UpdatePage(self)

        self.addSubInterface(self.monitor_page, FIF.HOME, "모니터링")
        self.addSubInterface(self.keyword_page, FIF.TAG, "키워드")
        self.addSubInterface(self.listings_page, FIF.SHOPPING_CART, "전체 매물")
        self.addSubInterface(self.favorites_page, FIF.HEART, "즐겨찾기")
        self.addSubInterface(self.stats_page, FIF.PIE_SINGLE, "통계")
        self.addSubInterface(self.history_page, FIF.HISTORY, "알림 내역")
        self.addSubInterface(self.log_page, FIF.COMMAND_PROMPT, "로그")
        self.addSubInterface(
            self.settings_page,
            FIF.SETTING,
            "설정",
            position=NavigationItemPosition.BOTTOM,
        )
        self.addSubInterface(
            self.update_page,
            FIF.UPDATE,
            "업데이트",
            position=NavigationItemPosition.BOTTOM,
        )

        self._nav_pages = [
            self.monitor_page,
            self.keyword_page,
            self.listings_page,
            self.favorites_page,
            self.stats_page,
            self.history_page,
            self.log_page,
        ]

        self.stackedWidget.currentChanged.connect(self._on_nav_changed)
        self.update_page.attach_to_window()

        apply_native_widget_style(self)
        with contextlib.suppress(Exception):
            from qfluentwidgets import qconfig

            qconfig.themeChanged.connect(lambda: apply_native_widget_style(self))

    def create_header(self):
        """Fluent 타이틀바 정체성 (제목 + 아이콘). 커스텀 헤더 위젯은 두지 않는다."""
        self.setWindowTitle(f"중고거래 알리미 v{__version__}")
        self.setWindowIcon(get_app_icon())

    def _on_nav_changed(self, _index: int):
        self._flush_live_data_refresh(force=False)

    def publish_status(self, text: str) -> None:
        monitor_page = getattr(self, "monitor_page", None)
        set_status = getattr(monitor_page, "set_status", None)
        if callable(set_status):
            set_status(text)


__all__ = ["UiSetupMixin", "preferred_window_size"]
