# gui/settings_dialog.py
"""Enhanced settings dialog with modern design"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QLineEdit, QSpinBox, QCheckBox, QLabel,
    QGroupBox, QPushButton, QComboBox, QMessageBox, QFrame,
    QScrollArea
)
from PyQt6.QtCore import Qt
import sys
sys.path.insert(0, '..')
from models import NotificationType, NotificationSchedule


class SettingsDialog(QDialog):
    """Modern settings dialog with tab navigation"""
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        self.setWindowTitle("설정")
        self.setMinimumSize(600, 550)
        self.setStyleSheet("QDialog { background-color: #1a1b26; }")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("⚙️ 설정")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #7aa2f7;")
        layout.addWidget(title)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        general_widget = self.create_general_tab()
        self.tabs.addTab(general_widget, "⚙️  일반")
        
        telegram_widget = self.create_telegram_tab()
        self.tabs.addTab(telegram_widget, "📲  텔레그램")
        
        discord_widget = self.create_discord_tab()
        self.tabs.addTab(discord_widget, "💬  디스코드")
        
        slack_widget = self.create_slack_tab()
        self.tabs.addTab(slack_widget, "💼  슬랙")
        
        schedule_widget = self.create_schedule_tab()
        self.tabs.addTab(schedule_widget, "⏰  스케줄")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        cancel_btn = QPushButton("취소")
        cancel_btn.setObjectName("secondary")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 저장")
        save_btn.setObjectName("success")
        save_btn.setMinimumWidth(100)
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
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
        
        layout.addWidget(window_group)
        layout.addStretch()
        
        return widget
    
    def create_notification_tab(self, title: str, icon: str, 
                                 enabled_var: str, fields: list) -> QWidget:
        """Generic notification tab creator"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        group = QGroupBox(f"{icon} {title} 설정")
        form_layout = QFormLayout(group)
        form_layout.setSpacing(16)
        
        # Enabled checkbox
        enabled_check = QCheckBox(f"{title} 알림 사용")
        enabled_check.setStyleSheet("font-size: 11pt; font-weight: bold;")
        setattr(self, enabled_var, enabled_check)
        form_layout.addRow("", enabled_check)
        
        # Fields
        for field_name, label, placeholder, is_password in fields:
            edit = QLineEdit()
            edit.setPlaceholderText(placeholder)
            edit.setMinimumHeight(40)
            if is_password:
                edit.setEchoMode(QLineEdit.EchoMode.Password)
            setattr(self, field_name, edit)
            form_layout.addRow(label, edit)
        
        layout.addWidget(group)
        
        return widget
    
    def create_telegram_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        group = QGroupBox("📲 텔레그램 봇")
        form_layout = QFormLayout(group)
        form_layout.setSpacing(16)
        
        self.telegram_enabled = QCheckBox("텔레그램 알림 사용")
        self.telegram_enabled.setStyleSheet("font-size: 11pt; font-weight: bold;")
        form_layout.addRow("", self.telegram_enabled)
        
        self.telegram_token = QLineEdit()
        self.telegram_token.setPlaceholderText("123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        self.telegram_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.telegram_token.setMinimumHeight(40)
        form_layout.addRow("Bot Token", self.telegram_token)
        
        self.telegram_chat_id = QLineEdit()
        self.telegram_chat_id.setPlaceholderText("123456789")
        self.telegram_chat_id.setMinimumHeight(40)
        form_layout.addRow("Chat ID", self.telegram_chat_id)
        
        layout.addWidget(group)
        
        # Help card
        help_frame = QFrame()
        help_frame.setStyleSheet("""
            QFrame {
                background-color: #24283b;
                border: 2px solid #3b4261;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        help_layout = QVBoxLayout(help_frame)
        
        help_title = QLabel("💡 설정 방법")
        help_title.setStyleSheet("font-weight: bold; color: #7aa2f7;")
        help_layout.addWidget(help_title)
        
        help_text = QLabel(
            "1. @BotFather에서 /newbot으로 봇 생성\n"
            "2. 생성된 토큰을 위에 입력\n"
            "3. @userinfobot에서 Chat ID 확인\n"
            "4. 봇에게 /start 메시지 먼저 전송"
        )
        help_text.setStyleSheet("color: #7982a9; line-height: 1.6;")
        help_layout.addWidget(help_text)
        
        layout.addWidget(help_frame)
        
        test_btn = QPushButton("🔔 테스트 알림 보내기")
        test_btn.clicked.connect(self.test_telegram)
        layout.addWidget(test_btn)
        
        layout.addStretch()
        return widget
    
    def create_discord_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        group = QGroupBox("💬 디스코드 웹훅")
        form_layout = QFormLayout(group)
        form_layout.setSpacing(16)
        
        self.discord_enabled = QCheckBox("디스코드 알림 사용")
        self.discord_enabled.setStyleSheet("font-size: 11pt; font-weight: bold;")
        form_layout.addRow("", self.discord_enabled)
        
        self.discord_webhook = QLineEdit()
        self.discord_webhook.setPlaceholderText("https://discord.com/api/webhooks/...")
        self.discord_webhook.setMinimumHeight(40)
        form_layout.addRow("Webhook URL", self.discord_webhook)
        
        layout.addWidget(group)
        
        help_frame = QFrame()
        help_frame.setStyleSheet("""
            QFrame {
                background-color: #24283b;
                border: 2px solid #3b4261;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        help_layout = QVBoxLayout(help_frame)
        
        help_title = QLabel("💡 설정 방법")
        help_title.setStyleSheet("font-weight: bold; color: #7aa2f7;")
        help_layout.addWidget(help_title)
        
        help_text = QLabel(
            "1. 디스코드 채널 설정 → 연동\n"
            "2. 웹훅 → 새 웹훅 만들기\n"
            "3. 웹훅 URL 복사"
        )
        help_text.setStyleSheet("color: #7982a9;")
        help_layout.addWidget(help_text)
        
        layout.addWidget(help_frame)
        
        test_btn = QPushButton("🔔 테스트 알림 보내기")
        test_btn.clicked.connect(self.test_discord)
        layout.addWidget(test_btn)
        
        layout.addStretch()
        return widget
    
    def create_slack_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        group = QGroupBox("💼 슬랙 웹훅")
        form_layout = QFormLayout(group)
        form_layout.setSpacing(16)
        
        self.slack_enabled = QCheckBox("슬랙 알림 사용")
        self.slack_enabled.setStyleSheet("font-size: 11pt; font-weight: bold;")
        form_layout.addRow("", self.slack_enabled)
        
        self.slack_webhook = QLineEdit()
        self.slack_webhook.setPlaceholderText("https://hooks.slack.com/services/...")
        self.slack_webhook.setMinimumHeight(40)
        form_layout.addRow("Webhook URL", self.slack_webhook)
        
        layout.addWidget(group)
        
        help_frame = QFrame()
        help_frame.setStyleSheet("""
            QFrame {
                background-color: #24283b;
                border: 2px solid #3b4261;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        help_layout = QVBoxLayout(help_frame)
        
        help_title = QLabel("💡 설정 방법")
        help_title.setStyleSheet("font-weight: bold; color: #7aa2f7;")
        help_layout.addWidget(help_title)
        
        help_text = QLabel(
            "1. Slack 앱 디렉토리에서 Incoming Webhooks 추가\n"
            "2. 채널 선택\n"
            "3. Webhook URL 복사"
        )
        help_text.setStyleSheet("color: #7982a9;")
        help_layout.addWidget(help_text)
        
        layout.addWidget(help_frame)
        
        test_btn = QPushButton("🔔 테스트 알림 보내기")
        test_btn.clicked.connect(self.test_slack)
        layout.addWidget(test_btn)
        
        layout.addStretch()
        return widget
    
    def create_schedule_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        group = QGroupBox("⏰ 알림 스케줄")
        form_layout = QVBoxLayout(group)
        form_layout.setSpacing(16)
        
        self.schedule_enabled = QCheckBox("스케줄 제한 사용")
        self.schedule_enabled.setStyleSheet("font-size: 11pt; font-weight: bold;")
        form_layout.addWidget(self.schedule_enabled)
        
        # Time range
        time_frame = QFrame()
        time_layout = QHBoxLayout(time_frame)
        time_layout.setContentsMargins(0, 8, 0, 8)
        
        time_layout.addWidget(QLabel("알림 시간:"))
        
        self.start_hour = QSpinBox()
        self.start_hour.setRange(0, 23)
        self.start_hour.setSuffix(" 시")
        self.start_hour.setMinimumWidth(80)
        self.start_hour.setMinimumHeight(36)
        time_layout.addWidget(self.start_hour)
        
        time_layout.addWidget(QLabel("부터"))
        
        self.end_hour = QSpinBox()
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
            cb = QCheckBox(name)
            cb.setChecked(True)
            cb.setStyleSheet("font-size: 11pt;")
            self.day_checks.append(cb)
            days_layout.addWidget(cb)
        days_layout.addStretch()
        
        form_layout.addWidget(days_frame)
        
        layout.addWidget(group)
        
        # Info card
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #9ece6a22;
                border: 2px solid #9ece6a44;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        
        info_text = QLabel(
            "💡 예: 9시~22시 설정 시 해당 시간에만 알림을 받습니다.\n"
            "야간에는 알림을 받지 않도록 설정할 수 있습니다."
        )
        info_text.setStyleSheet("color: #9ece6a;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_frame)
        layout.addStretch()
        
        return widget
    
    def load_settings(self):
        s = self.settings.settings
        
        self.interval_spin.setValue(s.check_interval_seconds)
        self.headless_check.setChecked(s.headless_mode)
        self.minimize_tray_check.setChecked(s.minimize_to_tray)
        self.start_minimized_check.setChecked(s.start_minimized)
        self.auto_start_check.setChecked(s.auto_start_monitoring)
        
        tg_config = self.settings.get_telegram_config()
        if tg_config:
            self.telegram_enabled.setChecked(tg_config.enabled)
            self.telegram_token.setText(tg_config.token)
            self.telegram_chat_id.setText(tg_config.chat_id)
        
        dc_config = self.settings.get_discord_config()
        if dc_config:
            self.discord_enabled.setChecked(dc_config.enabled)
            self.discord_webhook.setText(dc_config.webhook_url)
        
        sl_config = self.settings.get_slack_config()
        if sl_config:
            self.slack_enabled.setChecked(sl_config.enabled)
            self.slack_webhook.setText(sl_config.webhook_url)
        
        sched = s.notification_schedule
        self.schedule_enabled.setChecked(sched.enabled)
        self.start_hour.setValue(sched.start_hour)
        self.end_hour.setValue(sched.end_hour)
        for i, cb in enumerate(self.day_checks):
            cb.setChecked(i in sched.days)
    
    def save_settings(self):
        s = self.settings.settings
        
        s.check_interval_seconds = self.interval_spin.value()
        s.headless_mode = self.headless_check.isChecked()
        s.minimize_to_tray = self.minimize_tray_check.isChecked()
        s.start_minimized = self.start_minimized_check.isChecked()
        s.auto_start_monitoring = self.auto_start_check.isChecked()
        
        for n in s.notifiers:
            if n.type == NotificationType.TELEGRAM:
                n.enabled = self.telegram_enabled.isChecked()
                n.token = self.telegram_token.text().strip()
                n.chat_id = self.telegram_chat_id.text().strip()
            elif n.type == NotificationType.DISCORD:
                n.enabled = self.discord_enabled.isChecked()
                n.webhook_url = self.discord_webhook.text().strip()
            elif n.type == NotificationType.SLACK:
                n.enabled = self.slack_enabled.isChecked()
                n.webhook_url = self.slack_webhook.text().strip()
        
        s.notification_schedule = NotificationSchedule(
            enabled=self.schedule_enabled.isChecked(),
            start_hour=self.start_hour.value(),
            end_hour=self.end_hour.value(),
            days=[i for i, cb in enumerate(self.day_checks) if cb.isChecked()]
        )
        
        self.settings.save()
        QMessageBox.information(self, "저장 완료", "설정이 저장되었습니다.")
        self.accept()
    
    def test_telegram(self):
        QMessageBox.information(self, "테스트", "텔레그램 테스트 알림 전송 기능은 추후 지원 예정입니다.")
    
    def test_discord(self):
        QMessageBox.information(self, "테스트", "디스코드 테스트 알림 전송 기능은 추후 지원 예정입니다.")
    
    def test_slack(self):
        QMessageBox.information(self, "테스트", "슬랙 테스트 알림 전송 기능은 추후 지원 예정입니다.")
