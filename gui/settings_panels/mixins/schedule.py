from typing import TYPE_CHECKING

"""Settings dialog mixin: schedule."""

from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CaptionLabel,
    CheckBox,
    SpinBox,
)

if TYPE_CHECKING:
    from gui.settings_panels.dialog import SettingsDialog
    _HostBase_ScheduleSettingsMixin = SettingsDialog
else:
    _HostBase_ScheduleSettingsMixin = object

class ScheduleSettingsMixin(_HostBase_ScheduleSettingsMixin):
    """Schedule settings panel behavior."""

    def create_schedule_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        group = QGroupBox("알림 스케줄")
        form_layout = QVBoxLayout(group)
        form_layout.setSpacing(16)

        self.schedule_enabled = CheckBox("스케줄 제한 사용")
        form_layout.addWidget(self.schedule_enabled)

        # Time range
        time_frame = QFrame()
        time_layout = QHBoxLayout(time_frame)
        time_layout.setContentsMargins(0, 8, 0, 8)

        time_layout.addWidget(QLabel("알림 시간:"))

        self.start_hour = SpinBox()
        self.start_hour.setRange(0, 23)
        self.start_hour.setSuffix(" 시")
        self.start_hour.setMinimumWidth(80)
        self.start_hour.setMinimumHeight(36)
        time_layout.addWidget(self.start_hour)

        time_layout.addWidget(QLabel("부터"))

        self.end_hour = SpinBox()
        self.end_hour.setRange(0, 24)
        self.end_hour.setSuffix(" 시")
        self.end_hour.setMinimumWidth(80)
        self.end_hour.setMinimumHeight(36)
        time_layout.addWidget(self.end_hour)

        time_layout.addWidget(QLabel("까지"))
        time_layout.addStretch()

        form_layout.addWidget(time_frame)

        # Days of week
        days_frame = QFrame()
        days_layout = QHBoxLayout(days_frame)
        days_layout.setContentsMargins(0, 8, 0, 8)

        days_layout.addWidget(QLabel("알림 요일:"))

        self.day_checks = []
        day_names = ["월", "화", "수", "목", "금", "토", "일"]
        for i, name in enumerate(day_names):
            cb = CheckBox(name)
            cb.setChecked(True)
            self.day_checks.append(cb)
            days_layout.addWidget(cb)
        days_layout.addStretch()

        form_layout.addWidget(days_frame)

        layout.addWidget(group)

        # Info card
        info_frame = QFrame(self)
        info_layout = QVBoxLayout(info_frame)

        info_text = CaptionLabel(
            "예: 9시~22시 설정 시 해당 시간에만 알림을 받습니다.\n"
            "야간에는 알림을 받지 않도록 설정할 수 있습니다."
        )
        info_layout.addWidget(info_text)

        layout.addWidget(info_frame)
        layout.addStretch()

        return widget
