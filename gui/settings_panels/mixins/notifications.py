from typing import TYPE_CHECKING

"""Settings dialog mixin: notifications."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CaptionLabel,
    CheckBox,
    LineEdit,
    PushButton,
    StrongBodyLabel,
)

from models import NotificationType

from ..workers import NotificationTestThread

if TYPE_CHECKING:
    from gui.settings_panels.dialog import SettingsDialog
    _HostBase_NotificationSettingsMixin = SettingsDialog
else:
    _HostBase_NotificationSettingsMixin = object

class NotificationSettingsMixin(_HostBase_NotificationSettingsMixin):
    """Notifications settings panel behavior."""

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
        enabled_check = CheckBox(f"{title} 알림 사용")
        setattr(self, enabled_var, enabled_check)
        form_layout.addRow("", enabled_check)

        # Fields
        for field_name, label, placeholder, is_password in fields:
            edit = LineEdit()
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

        group = QGroupBox("텔레그램 봇")
        form_layout = QFormLayout(group)
        form_layout.setSpacing(16)

        self.telegram_enabled = CheckBox("텔레그램 알림 사용")
        form_layout.addRow("", self.telegram_enabled)

        self.telegram_token = LineEdit()
        self.telegram_token.setPlaceholderText("123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        self.telegram_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.telegram_token.setMinimumHeight(40)
        form_layout.addRow("Bot Token", self.telegram_token)

        self.telegram_chat_id = LineEdit()
        self.telegram_chat_id.setPlaceholderText("123456789")
        self.telegram_chat_id.setMinimumHeight(40)
        form_layout.addRow("Chat ID", self.telegram_chat_id)

        layout.addWidget(group)

        # Help card
        help_frame = QFrame()
        help_layout = QVBoxLayout(help_frame)

        help_title = StrongBodyLabel("설정 방법")
        help_layout.addWidget(help_title)

        help_text = CaptionLabel(
            "1. @BotFather에서 /newbot으로 봇 생성\n"
            "2. 생성된 토큰을 위에 입력\n"
            "3. @userinfobot에서 Chat ID 확인\n"
            "4. 봇에게 /start 메시지 먼저 전송"
        )
        help_layout.addWidget(help_text)

        layout.addWidget(help_frame)

        test_btn = PushButton("테스트 알림 보내기")
        test_btn.clicked.connect(self.test_telegram)
        layout.addWidget(test_btn)

        layout.addStretch()
        return widget


    def create_discord_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        group = QGroupBox("디스코드 웹훅")
        form_layout = QFormLayout(group)
        form_layout.setSpacing(16)

        self.discord_enabled = CheckBox("디스코드 알림 사용")
        form_layout.addRow("", self.discord_enabled)

        self.discord_webhook = LineEdit()
        self.discord_webhook.setPlaceholderText("https://discord.com/api/webhooks/...")
        self.discord_webhook.setMinimumHeight(40)
        form_layout.addRow("Webhook URL", self.discord_webhook)

        layout.addWidget(group)

        help_frame = QFrame()
        help_layout = QVBoxLayout(help_frame)

        help_title = StrongBodyLabel("설정 방법")
        help_layout.addWidget(help_title)

        help_text = CaptionLabel(
            "1. 디스코드 채널 설정 → 연동\n"
            "2. 웹훅 → 새 웹훅 만들기\n"
            "3. 웹훅 URL 복사"
        )
        help_layout.addWidget(help_text)

        layout.addWidget(help_frame)

        test_btn = PushButton("테스트 알림 보내기")
        test_btn.clicked.connect(self.test_discord)
        layout.addWidget(test_btn)

        layout.addStretch()
        return widget


    def create_slack_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        group = QGroupBox("슬랙 웹훅")
        form_layout = QFormLayout(group)
        form_layout.setSpacing(16)

        self.slack_enabled = CheckBox("슬랙 알림 사용")
        form_layout.addRow("", self.slack_enabled)

        self.slack_webhook = LineEdit()
        self.slack_webhook.setPlaceholderText("https://hooks.slack.com/services/...")
        self.slack_webhook.setMinimumHeight(40)
        form_layout.addRow("Webhook URL", self.slack_webhook)

        layout.addWidget(group)

        help_frame = QFrame()
        help_layout = QVBoxLayout(help_frame)

        help_title = StrongBodyLabel("설정 방법")
        help_layout.addWidget(help_title)

        help_text = CaptionLabel(
            "1. Slack 앱 디렉토리에서 Incoming Webhooks 추가\n"
            "2. 채널 선택\n"
            "3. Webhook URL 복사"
        )
        help_layout.addWidget(help_text)

        layout.addWidget(help_frame)

        test_btn = PushButton("테스트 알림 보내기")
        test_btn.clicked.connect(self.test_slack)
        layout.addWidget(test_btn)

        layout.addStretch()
        return widget


    def test_telegram(self):
        """Test Telegram notification"""
        token = self.telegram_token.text().strip()
        chat_id = self.telegram_chat_id.text().strip()

        if not token or not chat_id:
            QMessageBox.warning(self, "오류", "토큰과 Chat ID를 모두 입력해주세요.")
            return

        self._start_test_thread(
            NotificationType.TELEGRAM,
            token=token,
            chat_id=chat_id
        )


    def test_discord(self):
        """Test Discord notification"""
        url = self.discord_webhook.text().strip()

        if not url:
            QMessageBox.warning(self, "오류", "Webhook URL을 입력해주세요.")
            return

        self._start_test_thread(
            NotificationType.DISCORD,
            url=url
        )


    def test_slack(self):
        """Test Slack notification"""
        url = self.slack_webhook.text().strip()

        if not url:
            QMessageBox.warning(self, "오류", "Webhook URL을 입력해주세요.")
            return

        self._start_test_thread(
            NotificationType.SLACK,
            url=url
        )


    def _start_test_thread(self, n_type, **kwargs):
        """Start notification test thread"""
        self.setCursor(Qt.CursorShape.WaitCursor)

        self.test_thread = NotificationTestThread(n_type, **kwargs)
        self.test_thread.finished.connect(self._on_test_finished)
        self.test_thread.start()


    def _on_test_finished(self, success, message):
        """Handle test thread completion"""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        if success:
            QMessageBox.information(self, "성공", message)
        else:
            QMessageBox.warning(self, "실패", message)
