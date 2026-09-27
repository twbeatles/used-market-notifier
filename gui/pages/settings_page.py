# pyright: reportGeneralTypeIssues=false
"""Fluent 설정 페이지: ScrollArea + Pivot + QStackedWidget (KTrain §17-18).

탭 내용은 기존 settings_panels 믹스인 빌더를 그대로 재사용한다.
업데이트 그룹은 유지보수 탭에 자동 포함되지 않는다(UpdateSettingsMixin
미상속 → getattr 폴백으로 스킵). 업데이트는 하단 Navigation의 UpdatePage가 담당.
"""

from PySide6.QtWidgets import (
    QHBoxLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    InfoBar,
    InfoBarPosition,
    Pivot,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    SubtitleLabel,
)

from backup_manager import BackupManager
from gui.settings_panels.mixins import (
    AutoTaggingSettingsMixin,
    GeneralSettingsMixin,
    MaintenanceSettingsMixin,
    MessageTemplatesSettingsMixin,
    NotificationSettingsMixin,
    ScheduleSettingsMixin,
    SellerSettingsMixin,
    SettingsPersistenceMixin,
)
from models import MessageTemplate, TagRule


class SettingsPage(
    GeneralSettingsMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    NotificationSettingsMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    ScheduleSettingsMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    SellerSettingsMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    MaintenanceSettingsMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    AutoTaggingSettingsMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    MessageTemplatesSettingsMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    SettingsPersistenceMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    ScrollArea,
):
    """Pivot 기반 설정 페이지."""

    _TABS: tuple[tuple[str, str, str], ...] = (
        ("general", "일반", "create_general_tab"),
        ("telegram", "텔레그램", "create_telegram_tab"),
        ("discord", "디스코드", "create_discord_tab"),
        ("slack", "슬랙", "create_slack_tab"),
        ("schedule", "스케줄", "create_schedule_tab"),
        ("seller", "차단 관리", "create_seller_tab"),
        ("maintenance", "유지보수", "create_maintenance_tab"),
        ("tagging", "자동 태깅", "create_auto_tagging_tab"),
        ("templates", "메시지 템플릿", "create_message_templates_tab"),
    )

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsInterface")
        self.settings = settings_manager
        self.backup_manager = BackupManager()
        self._tag_rules: list[TagRule] = []
        self._message_templates: list[MessageTemplate] = []

        self.setWidgetResizable(True)
        from PySide6.QtCore import Qt

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        self.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)

        layout.addWidget(SubtitleLabel("설정"))

        pivot_row = QHBoxLayout()
        pivot_row.setSpacing(8)
        self.pivot = Pivot(self)
        pivot_row.addWidget(self.pivot)
        pivot_row.addStretch()
        layout.addLayout(pivot_row)

        self.stacked = QStackedWidget(self)
        layout.addWidget(self.stacked, 1)

        self._tab_keys: list[str] = []
        for key, title, builder_name in self._TABS:
            builder = getattr(self, builder_name)
            tab = builder()
            self._tab_keys.append(key)
            self.pivot.addItem(key, title)
            self.stacked.addWidget(tab)
        self.pivot.setCurrentItem(self._tab_keys[0])
        self.pivot.currentItemChanged.connect(self._on_pivot_changed)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        button_row.addStretch()
        self.reload_btn = PushButton("다시 불러오기", self)
        self.reload_btn.clicked.connect(self._on_reload_clicked)
        button_row.addWidget(self.reload_btn)
        self.save_btn = PrimaryPushButton("저장", self)
        self.save_btn.clicked.connect(self._on_save_clicked)
        button_row.addWidget(self.save_btn)
        layout.addLayout(button_row)

        self.load_settings()

    # -- internal -------------------------------------------------------------
    def _get_parent_db(self):
        parent = self.parent()
        if parent is None:
            return None
        engine = getattr(parent, "engine", None)
        return getattr(engine, "db", None)

    def _on_pivot_changed(self, key: str) -> None:
        if key in self._tab_keys:
            self.stacked.setCurrentIndex(self._tab_keys.index(key))

    def _on_reload_clicked(self) -> None:
        self.load_settings()
        InfoBar.info(
            "설정",
            "저장된 설정을 다시 불러왔습니다.",
            parent=self.window(),
            position=InfoBarPosition.TOP,
        )

    def _on_save_clicked(self) -> None:
        self.persist_settings_form()
        self.settings.save()
        InfoBar.success(
            "저장 완료",
            "설정을 저장했습니다. 자동 태깅 규칙은 모니터링 재시작 시 적용됩니다.",
            parent=self.window(),
            position=InfoBarPosition.TOP,
        )
        window = self.window()
        apply_after = getattr(window, "_apply_settings_after_save", None)
        if callable(apply_after):
            apply_after()


__all__ = ["SettingsPage"]
