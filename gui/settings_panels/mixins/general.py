"""Settings dialog mixin: general."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QLineEdit, QSpinBox, QCheckBox, QLabel,
    QGroupBox, QPushButton, QComboBox, QMessageBox, QFrame,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from models import ThemeMode

class GeneralSettingsMixin:
    """General settings panel behavior."""

    def create_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(16, 16, 16, 16)

        # Monitoring settings
        monitor_group = QGroupBox("🔍 모니터링")
        monitor_layout = QFormLayout(monitor_group)
        monitor_layout.setSpacing(16)

        interval_row = QHBoxLayout()
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(60, 3600)
        self.interval_spin.setSingleStep(30)
        self.interval_spin.setSuffix(" 초")
        self.interval_spin.setMinimumWidth(120)
        self.interval_spin.setMinimumHeight(36)
        interval_row.addWidget(self.interval_spin)

        interval_hint = QLabel("(1분 ~ 1시간)")
        interval_hint.setStyleSheet("color: #565f89;")
        interval_row.addWidget(interval_hint)
        interval_row.addStretch()

        monitor_layout.addRow("검색 주기", interval_row)

        self.headless_check = QCheckBox("백그라운드 모드 (브라우저 창 숨김)")
        self.headless_check.setStyleSheet("font-size: 10pt;")
        monitor_layout.addRow("", self.headless_check)

        self.metadata_enrichment_check = QCheckBox("seller/location 보강 수집 사용")
        self.metadata_enrichment_check.setToolTip("상세 페이지를 한 번 더 열어 비어 있는 seller/location 정보만 보강합니다.")
        self.metadata_enrichment_check.setStyleSheet("font-size: 10pt;")
        monitor_layout.addRow("", self.metadata_enrichment_check)

        self.conditional_metadata_enrichment_check = QCheckBox("필터/차단 판단에 필요한 경우만 보강 수집")
        self.conditional_metadata_enrichment_check.setToolTip(
            "지역 필터 또는 차단 판매자 판별에 필요한 seller/location 정보가 비어 있을 때만 제한적으로 보강합니다."
        )
        self.conditional_metadata_enrichment_check.setStyleSheet("font-size: 10pt;")
        monitor_layout.addRow("", self.conditional_metadata_enrichment_check)

        scraper_row = QHBoxLayout()
        self.scraper_mode_combo = QComboBox()
        self.scraper_mode_combo.addItem("Playwright 우선 + Selenium fallback", "playwright_primary")
        self.scraper_mode_combo.addItem("Selenium 우선 + Playwright fallback", "selenium_primary")
        self.scraper_mode_combo.addItem("Selenium 전용", "selenium_only")
        self.scraper_mode_combo.setMinimumWidth(260)
        scraper_row.addWidget(self.scraper_mode_combo)
        scraper_row.addStretch()
        monitor_layout.addRow("스크래퍼 엔진", scraper_row)

        self.fallback_on_empty_check = QCheckBox("기본 엔진 결과가 0개일 때 fallback 사용")
        self.fallback_on_empty_check.setStyleSheet("font-size: 10pt;")
        monitor_layout.addRow("", self.fallback_on_empty_check)

        fallback_budget_row = QHBoxLayout()
        self.max_fallback_spin = QSpinBox()
        self.max_fallback_spin.setRange(0, 50)
        self.max_fallback_spin.setSuffix(" 회/사이클")
        self.max_fallback_spin.setMinimumWidth(140)
        self.max_fallback_spin.setMinimumHeight(36)
        fallback_budget_row.addWidget(self.max_fallback_spin)
        fallback_budget_row.addStretch()
        monitor_layout.addRow("fallback 최대 횟수", fallback_budget_row)

        # Theme settings
        theme_row = QHBoxLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("다크 모드 (Dark)", ThemeMode.DARK)
        self.theme_combo.addItem("라이트 모드 (Light)", ThemeMode.LIGHT)
        self.theme_combo.addItem("시스템 설정 (System)", ThemeMode.SYSTEM)
        self.theme_combo.setMinimumWidth(200)
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch()

        monitor_layout.addRow("테마 설정", theme_row)

        layout.addWidget(monitor_group)

        # Window settings
        window_group = QGroupBox("🖥️ 창 설정")
        window_layout = QVBoxLayout(window_group)
        window_layout.setSpacing(12)

        self.minimize_tray_check = QCheckBox("닫기 버튼 클릭 시 트레이로 최소화")
        window_layout.addWidget(self.minimize_tray_check)

        self.start_minimized_check = QCheckBox("시작 시 최소화 상태로 시작")
        window_layout.addWidget(self.start_minimized_check)

        self.auto_start_check = QCheckBox("시작 시 자동으로 모니터링 시작")
        window_layout.addWidget(self.auto_start_check)

        self.confirm_link_check = QCheckBox("상품 링크 열기 전 확인")
        window_layout.addWidget(self.confirm_link_check)

        self.notifications_enabled_check = QCheckBox("🔔 알림 받기 (텔레그램/디스코드/슬랙)")
        self.notifications_enabled_check.setToolTip("체크 해제 시 모든 알림이 비활성화됩니다")
        window_layout.addWidget(self.notifications_enabled_check)

        layout.addWidget(window_group)
        layout.addStretch()

        return widget
