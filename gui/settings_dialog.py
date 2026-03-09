# gui/settings_dialog.py
"""Enhanced settings dialog with modern design"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QLineEdit, QSpinBox, QCheckBox, QLabel,
    QGroupBox, QPushButton, QComboBox, QMessageBox, QFrame,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from typing import Any
from models import NotificationType, NotificationSchedule, ThemeMode, TagRule, MessageTemplate
from notifiers import TelegramNotifier, DiscordNotifier, SlackNotifier
import asyncio
import os

from auto_tagger import AutoTagger
from backup_manager import BackupManager
from message_templates import MessageTemplateManager


class SettingsDialog(QDialog):
    """Modern settings dialog with tab navigation"""
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.backup_manager = BackupManager()
        self._tag_rules: list[TagRule] = []
        self._message_templates: list[MessageTemplate] = []
        self.setup_ui()
        self.load_settings()

    def _get_parent_db(self):
        parent = self.parent()
        if parent is None:
            return None
        engine = getattr(parent, "engine", None)
        return getattr(engine, "db", None)
    
    def setup_ui(self):
        self.setWindowTitle("설정")
        self.setMinimumSize(800, 700)
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
        
        seller_widget = self.create_seller_tab()
        self.tabs.addTab(seller_widget, "🚫  차단 관리")

        maintenance_widget = self.create_maintenance_tab()
        self.tabs.addTab(maintenance_widget, "🧰  유지보수")

        tag_widget = self.create_auto_tagging_tab()
        self.tabs.addTab(tag_widget, "🏷️  자동 태깅")

        templates_widget = self.create_message_templates_tab()
        self.tabs.addTab(templates_widget, "💬  메시지 템플릿")
        
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
        self.confirm_link_check.setChecked(s.confirm_link_open)
        self.notifications_enabled_check.setChecked(getattr(s, 'notifications_enabled', False))

        # Maintenance (backup/cleanup)
        if hasattr(self, "auto_backup_enabled_check"):
            self.auto_backup_enabled_check.setChecked(getattr(s, "auto_backup_enabled", True))
            self.auto_backup_interval_spin.setValue(getattr(s, "auto_backup_interval_days", 7))
            self.backup_keep_count_spin.setValue(getattr(s, "backup_keep_count", 5))

        if hasattr(self, "auto_cleanup_enabled_check"):
            self.auto_cleanup_enabled_check.setChecked(getattr(s, "auto_cleanup_enabled", False))
            self.cleanup_days_spin.setValue(getattr(s, "cleanup_days", 30))
            self.cleanup_exclude_favorites_check.setChecked(getattr(s, "cleanup_exclude_favorites", True))
            self.cleanup_exclude_noted_check.setChecked(getattr(s, "cleanup_exclude_noted", True))
        
        # Load theme
        idx = self.theme_combo.findData(s.theme_mode)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        
        # Load blocked sellers
        self.load_blocked_sellers()
        
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

        # Load backups list / cleanup preview
        try:
            if hasattr(self, "backup_table"):
                self.refresh_backup_list()
            if hasattr(self, "cleanup_preview_label"):
                self.refresh_cleanup_preview()
        except Exception:
            pass

        # Tag rules (show defaults if empty)
        try:
            if hasattr(self, "auto_tagging_enabled_check"):
                self.auto_tagging_enabled_check.setChecked(getattr(s, "auto_tagging_enabled", True))
            if s.tag_rules:
                self._tag_rules = list(s.tag_rules)
            else:
                self._tag_rules = [
                    TagRule(
                        tag_name=r.get("tag_name", ""),
                        keywords=list(r.get("keywords", [])),
                        color=r.get("color", "#89b4fa"),
                        icon=r.get("icon", "🏷️"),
                        enabled=r.get("enabled", True),
                    )
                    for r in AutoTagger.DEFAULT_RULES
                ]
            self._refresh_tag_rules_table()
            if hasattr(self, "_on_auto_tagging_toggled"):
                self._on_auto_tagging_toggled(self.auto_tagging_enabled_check.isChecked())
        except Exception:
            pass

        # Message templates (show defaults if empty)
        try:
            if s.message_templates:
                self._message_templates = list(s.message_templates)
            else:
                self._message_templates = [
                    MessageTemplate(name=t.name, content=t.content, platform=t.platform)
                    for t in MessageTemplateManager.DEFAULT_TEMPLATES
                ]
            self._refresh_message_templates_table()
        except Exception:
            pass
    
    def save_settings(self):
        s = self.settings.settings
        
        s.check_interval_seconds = self.interval_spin.value()
        s.headless_mode = self.headless_check.isChecked()
        s.minimize_to_tray = self.minimize_tray_check.isChecked()
        s.start_minimized = self.start_minimized_check.isChecked()
        s.auto_start_monitoring = self.auto_start_check.isChecked()
        s.confirm_link_open = self.confirm_link_check.isChecked()
        s.notifications_enabled = self.notifications_enabled_check.isChecked()
        s.theme_mode = self.theme_combo.currentData()

        # Maintenance (backup/cleanup)
        if hasattr(self, "auto_backup_enabled_check"):
            s.auto_backup_enabled = self.auto_backup_enabled_check.isChecked()
            s.auto_backup_interval_days = self.auto_backup_interval_spin.value()
            s.backup_keep_count = self.backup_keep_count_spin.value()

        if hasattr(self, "auto_cleanup_enabled_check"):
            s.auto_cleanup_enabled = self.auto_cleanup_enabled_check.isChecked()
            s.cleanup_days = self.cleanup_days_spin.value()
            s.cleanup_exclude_favorites = self.cleanup_exclude_favorites_check.isChecked()
            s.cleanup_exclude_noted = self.cleanup_exclude_noted_check.isChecked()
        
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

        # Auto-tagging rules / message templates
        if hasattr(self, "auto_tagging_enabled_check"):
            s.auto_tagging_enabled = self.auto_tagging_enabled_check.isChecked()
        try:
            # Allow toggling enabled checkbox directly in the table.
            if hasattr(self, "tag_rules_table") and self._tag_rules:
                for i, r in enumerate(self._tag_rules):
                    item = self.tag_rules_table.item(i, 0)
                    if item:
                        r.enabled = item.checkState() == Qt.CheckState.Checked
        except Exception:
            pass
        s.tag_rules = list(self._tag_rules or [])
        s.message_templates = list(self._message_templates or [])
        
        self.settings.save()
        QMessageBox.information(
            self,
            "저장 완료",
            "설정이 저장되었습니다.\n\n"
            "참고: 자동 태깅 규칙은 모니터링 재시작 시 적용됩니다."
        )
        self.accept()
    
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

    def create_maintenance_tab(self) -> QWidget:
        """Backup/restore + cleanup controls"""
        widget = QWidget()
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Backup group
        backup_group = QGroupBox("💾 백업 / 복원")
        backup_layout = QVBoxLayout(backup_group)
        backup_layout.setSpacing(12)

        self.auto_backup_enabled_check = QCheckBox("자동 백업 사용")
        backup_layout.addWidget(self.auto_backup_enabled_check)

        backup_form = QFormLayout()
        backup_form.setSpacing(12)

        self.auto_backup_interval_spin = QSpinBox()
        self.auto_backup_interval_spin.setRange(1, 365)
        self.auto_backup_interval_spin.setSuffix(" 일")
        self.auto_backup_interval_spin.setMinimumHeight(34)
        backup_form.addRow("백업 주기", self.auto_backup_interval_spin)

        self.backup_keep_count_spin = QSpinBox()
        self.backup_keep_count_spin.setRange(1, 100)
        self.backup_keep_count_spin.setSuffix(" 개")
        self.backup_keep_count_spin.setMinimumHeight(34)
        backup_form.addRow("보관 개수", self.backup_keep_count_spin)

        backup_layout.addLayout(backup_form)

        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(3)
        self.backup_table.setHorizontalHeaderLabels(["파일", "날짜", "크기"])
        backup_h_header = self.backup_table.horizontalHeader()
        if backup_h_header is not None:
            backup_h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.backup_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.backup_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        backup_layout.addWidget(self.backup_table)

        backup_btns = QHBoxLayout()
        backup_btns.addStretch()

        create_btn = QPushButton("지금 백업 생성")
        create_btn.clicked.connect(self.create_backup_now)
        backup_btns.addWidget(create_btn)

        open_btn = QPushButton("백업 폴더 열기")
        open_btn.clicked.connect(self.open_backup_folder)
        backup_btns.addWidget(open_btn)

        restore_btn = QPushButton("선택 백업 복원")
        restore_btn.clicked.connect(self.restore_selected_backup)
        backup_btns.addWidget(restore_btn)

        backup_layout.addLayout(backup_btns)

        # Cleanup group
        cleanup_group = QGroupBox("🧹 자동 클린업")
        cleanup_layout = QVBoxLayout(cleanup_group)
        cleanup_layout.setSpacing(12)

        self.auto_cleanup_enabled_check = QCheckBox("앱 시작 시 1회 오래된 매물 정리 실행")
        cleanup_layout.addWidget(self.auto_cleanup_enabled_check)

        cleanup_form = QFormLayout()
        cleanup_form.setSpacing(12)

        self.cleanup_days_spin = QSpinBox()
        self.cleanup_days_spin.setRange(1, 3650)
        self.cleanup_days_spin.setSuffix(" 일 이전")
        self.cleanup_days_spin.setMinimumHeight(34)
        cleanup_form.addRow("삭제 기준", self.cleanup_days_spin)

        self.cleanup_exclude_favorites_check = QCheckBox("즐겨찾기 제외")
        cleanup_form.addRow("", self.cleanup_exclude_favorites_check)

        self.cleanup_exclude_noted_check = QCheckBox("메모/태그가 있는 항목 제외")
        cleanup_form.addRow("", self.cleanup_exclude_noted_check)

        cleanup_layout.addLayout(cleanup_form)

        preview_row = QHBoxLayout()
        self.cleanup_preview_label = QLabel("미리보기: -")
        self.cleanup_preview_label.setStyleSheet("color: #a6e3a1;")
        preview_row.addWidget(self.cleanup_preview_label)
        preview_row.addStretch()

        refresh_preview_btn = QPushButton("미리보기 새로고침")
        refresh_preview_btn.clicked.connect(self.refresh_cleanup_preview)
        preview_row.addWidget(refresh_preview_btn)

        cleanup_layout.addLayout(preview_row)

        cleanup_btns = QHBoxLayout()
        cleanup_btns.addStretch()

        self.run_cleanup_btn = QPushButton("지금 정리 실행")
        self.run_cleanup_btn.clicked.connect(self.run_cleanup_now)
        cleanup_btns.addWidget(self.run_cleanup_btn)

        cleanup_layout.addLayout(cleanup_btns)

        layout.addWidget(backup_group)
        layout.addWidget(cleanup_group)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)
        return widget

    def refresh_backup_list(self):
        backups = self.backup_manager.list_backups()
        self.backup_table.setRowCount(len(backups))
        for i, b in enumerate(backups):
            item0 = QTableWidgetItem(b.get("filename", ""))
            item0.setData(Qt.ItemDataRole.UserRole, b.get("path", ""))
            self.backup_table.setItem(i, 0, item0)
            self.backup_table.setItem(i, 1, QTableWidgetItem(b.get("date", "")))
            self.backup_table.setItem(i, 2, QTableWidgetItem(b.get("size_str", "")))

    def create_backup_now(self):
        s = self.settings.settings
        settings_path = str(getattr(self.settings, "settings_path", "settings.json"))
        backup_path = self.backup_manager.create_backup(
            db_path=getattr(s, "db_path", "listings.db"),
            settings_path=settings_path,
        )
        if not backup_path:
            QMessageBox.warning(self, "실패", "백업 생성에 실패했습니다. 로그를 확인하세요.")
            return

        try:
            self.backup_manager.cleanup_old_backups(keep_count=self.backup_keep_count_spin.value())
        except Exception:
            pass

        self.refresh_backup_list()
        QMessageBox.information(self, "완료", f"백업이 생성되었습니다.\n\n{backup_path}")

    def open_backup_folder(self):
        try:
            os.startfile(str(self.backup_manager.backup_dir.resolve()))
        except Exception as e:
            QMessageBox.warning(self, "오류", f"백업 폴더를 열 수 없습니다: {e}")

    def restore_selected_backup(self):
        row = self.backup_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "알림", "복원할 백업을 선택하세요.")
            return

        item = self.backup_table.item(row, 0)
        backup_path = item.data(Qt.ItemDataRole.UserRole) if item else ""
        if not backup_path:
            QMessageBox.warning(self, "오류", "백업 경로를 찾을 수 없습니다.")
            return

        if QMessageBox.question(
            self,
            "주의",
            "선택한 백업으로 DB/설정 파일을 덮어씁니다.\n"
            "복원 후 앱은 종료됩니다.\n\n계속하시겠습니까?",
        ) != QMessageBox.StandardButton.Yes:
            return

        # Stop monitoring if running and close DB connection for safety.
        parent = self.parent()
        try:
            monitor_thread = getattr(parent, "monitor_thread", None) if parent is not None else None
            is_running = getattr(monitor_thread, "isRunning", None)
            if callable(is_running) and is_running():
                stop_monitoring = getattr(parent, "stop_monitoring", None)
                if callable(stop_monitoring):
                    stop_monitoring()
        except Exception:
            pass

        # Do not forcibly close parent.engine.db here: the app is about to quit,
        # and the engine may be using a shared UI DB connection.

        s = self.settings.settings
        settings_path = str(getattr(self.settings, "settings_path", "settings.json"))
        ok = self.backup_manager.restore_backup(
            backup_file=str(backup_path),
            db_path=getattr(s, "db_path", "listings.db"),
            settings_path=settings_path,
        )
        if not ok:
            QMessageBox.warning(self, "실패", "복원에 실패했습니다. 로그를 확인하세요.")
            return

        QMessageBox.information(self, "완료", "복원이 완료되었습니다.\n데이터 일관성을 위해 앱을 종료합니다.")
        QApplication.quit()

    def refresh_cleanup_preview(self):
        try:
            from db import DatabaseManager
            s = self.settings.settings
            db = DatabaseManager(getattr(s, "db_path", "listings.db"))
            try:
                preview = db.get_cleanup_preview(
                    days=self.cleanup_days_spin.value(),
                    exclude_favorites=self.cleanup_exclude_favorites_check.isChecked(),
                    exclude_noted=self.cleanup_exclude_noted_check.isChecked(),
                )
            finally:
                try:
                    db.close()
                except Exception:
                    pass

            self.cleanup_preview_label.setText(
                f"미리보기: {preview.get('delete_count', 0):,} / {preview.get('total_count', 0):,} 삭제 예정"
            )
        except Exception as e:
            self.cleanup_preview_label.setText(f"미리보기 실패: {e}")

    def run_cleanup_now(self):
        parent = self.parent()
        try:
            monitor_thread = getattr(parent, "monitor_thread", None) if parent is not None else None
            is_running = getattr(monitor_thread, "isRunning", None)
            if callable(is_running) and is_running():
                if QMessageBox.question(
                    self,
                    "확인",
                    "모니터링이 실행 중입니다.\n정리 작업을 위해 모니터링을 중지할까요?",
                ) == QMessageBox.StandardButton.Yes:
                    stop_monitoring = getattr(parent, "stop_monitoring", None)
                    if callable(stop_monitoring):
                        stop_monitoring()
                else:
                    return
        except Exception:
            pass

        if QMessageBox.question(
            self,
            "확인",
            "지금 정리를 실행하면 조건에 맞는 오래된 매물이 DB에서 삭제됩니다.\n계속하시겠습니까?",
        ) != QMessageBox.StandardButton.Yes:
            return

        self.run_cleanup_btn.setEnabled(False)
        self.cleanup_preview_label.setText("정리 실행 중...")

        s = self.settings.settings
        self._cleanup_thread = CleanupWorker(
            db_path=getattr(s, "db_path", "listings.db"),
            days=self.cleanup_days_spin.value(),
            exclude_favorites=self.cleanup_exclude_favorites_check.isChecked(),
            exclude_noted=self.cleanup_exclude_noted_check.isChecked(),
        )
        self._cleanup_thread.completed.connect(self._on_cleanup_done)
        self._cleanup_thread.failed.connect(self._on_cleanup_failed)
        self._cleanup_thread.start()

    def _on_cleanup_done(self, deleted_count: int):
        self.run_cleanup_btn.setEnabled(True)
        self.refresh_cleanup_preview()
        QMessageBox.information(self, "완료", f"정리가 완료되었습니다.\n삭제된 항목: {deleted_count:,}개")

        # Best-effort refresh in main UI if available.
        parent = self.parent()
        try:
            stats_widget = getattr(parent, "stats_widget", None) if parent is not None else None
            listings_widget = getattr(parent, "listings_widget", None) if parent is not None else None
            refresh_stats = getattr(stats_widget, "refresh_stats", None)
            refresh_listings = getattr(listings_widget, "refresh_listings", None)
            if callable(refresh_stats):
                refresh_stats()
            if callable(refresh_listings):
                refresh_listings()
        except Exception:
            pass

    def _on_cleanup_failed(self, error: str):
        self.run_cleanup_btn.setEnabled(True)
        self.cleanup_preview_label.setText(f"정리 실패: {error}")
        QMessageBox.warning(self, "실패", f"정리 작업 실패: {error}")

    def create_auto_tagging_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        self.auto_tagging_enabled_check = QCheckBox("자동 태깅 사용")
        self.auto_tagging_enabled_check.setToolTip("끄면 자동 태그 생성/저장이 동작하지 않습니다.")
        self.auto_tagging_enabled_check.toggled.connect(self._on_auto_tagging_toggled)
        layout.addWidget(self.auto_tagging_enabled_check)

        desc = QLabel("🏷️ 제목 키워드에 따라 자동으로 태그를 부여합니다. (모니터링 재시작 시 적용)")
        desc.setStyleSheet("color: #89b4fa;")
        layout.addWidget(desc)

        self.tag_rules_table = QTableWidget()
        self.tag_rules_table.setColumnCount(5)
        self.tag_rules_table.setHorizontalHeaderLabels(["사용", "태그", "아이콘", "색상", "키워드"])
        tag_h_header = self.tag_rules_table.horizontalHeader()
        if tag_h_header is not None:
            tag_h_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tag_rules_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tag_rules_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tag_rules_table)

        btns = QHBoxLayout()
        btns.addStretch()

        self.tag_add_btn = QPushButton("추가")
        self.tag_add_btn.clicked.connect(self.add_tag_rule)
        btns.addWidget(self.tag_add_btn)

        self.tag_edit_btn = QPushButton("편집")
        self.tag_edit_btn.clicked.connect(self.edit_tag_rule)
        btns.addWidget(self.tag_edit_btn)

        self.tag_del_btn = QPushButton("삭제")
        self.tag_del_btn.clicked.connect(self.delete_tag_rule)
        btns.addWidget(self.tag_del_btn)

        self.tag_reset_btn = QPushButton("기본값으로 초기화")
        self.tag_reset_btn.clicked.connect(self.reset_tag_rules_default)
        btns.addWidget(self.tag_reset_btn)

        layout.addLayout(btns)
        return widget

    def _on_auto_tagging_toggled(self, enabled: bool):
        # Disable editing UI when feature is off (rules are still kept/saved).
        try:
            self.tag_rules_table.setEnabled(enabled)
            self.tag_add_btn.setEnabled(enabled)
            self.tag_edit_btn.setEnabled(enabled)
            self.tag_del_btn.setEnabled(enabled)
            self.tag_reset_btn.setEnabled(enabled)
        except Exception:
            pass

    def _refresh_tag_rules_table(self):
        if not hasattr(self, "tag_rules_table"):
            return
        rules = self._tag_rules or []
        self.tag_rules_table.setRowCount(len(rules))
        for i, r in enumerate(rules):
            enabled_item = QTableWidgetItem("")
            enabled_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable
            )
            enabled_item.setCheckState(Qt.CheckState.Checked if getattr(r, "enabled", True) else Qt.CheckState.Unchecked)
            self.tag_rules_table.setItem(i, 0, enabled_item)

            self.tag_rules_table.setItem(i, 1, QTableWidgetItem(getattr(r, "tag_name", "")))
            self.tag_rules_table.setItem(i, 2, QTableWidgetItem(getattr(r, "icon", "")))
            self.tag_rules_table.setItem(i, 3, QTableWidgetItem(getattr(r, "color", "")))

            keywords = getattr(r, "keywords", []) or []
            self.tag_rules_table.setItem(i, 4, QTableWidgetItem(", ".join(keywords)))

    def _selected_tag_rule_index(self) -> int:
        row = self.tag_rules_table.currentRow()
        return row if row >= 0 else -1

    def add_tag_rule(self):
        dlg = TagRuleEditDialog(parent=self)
        if dlg.exec():
            self._tag_rules.append(dlg.get_rule())
            self._refresh_tag_rules_table()

    def edit_tag_rule(self):
        idx = self._selected_tag_rule_index()
        if idx < 0 or idx >= len(self._tag_rules):
            QMessageBox.information(self, "알림", "편집할 규칙을 선택하세요.")
            return
        dlg = TagRuleEditDialog(rule=self._tag_rules[idx], parent=self)
        if dlg.exec():
            self._tag_rules[idx] = dlg.get_rule()
            self._refresh_tag_rules_table()

    def delete_tag_rule(self):
        idx = self._selected_tag_rule_index()
        if idx < 0 or idx >= len(self._tag_rules):
            QMessageBox.information(self, "알림", "삭제할 규칙을 선택하세요.")
            return
        if QMessageBox.question(self, "확인", "선택한 규칙을 삭제하시겠습니까?") != QMessageBox.StandardButton.Yes:
            return
        self._tag_rules.pop(idx)
        self._refresh_tag_rules_table()

    def reset_tag_rules_default(self):
        if QMessageBox.question(self, "확인", "기본 태그 규칙으로 초기화하시겠습니까?") != QMessageBox.StandardButton.Yes:
            return
        self._tag_rules = [
            TagRule(
                tag_name=r.get("tag_name", ""),
                keywords=list(r.get("keywords", [])),
                color=r.get("color", "#89b4fa"),
                icon=r.get("icon", "🏷️"),
                enabled=True,
            )
            for r in AutoTagger.DEFAULT_RULES
        ]
        self._refresh_tag_rules_table()

    def create_message_templates_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        desc = QLabel("💬 판매자에게 보낼 메시지 템플릿을 관리합니다.")
        desc.setStyleSheet("color: #89b4fa;")
        layout.addWidget(desc)

        self.templates_table = QTableWidget()
        self.templates_table.setColumnCount(3)
        self.templates_table.setHorizontalHeaderLabels(["이름", "플랫폼", "내용"])
        template_h_header = self.templates_table.horizontalHeader()
        if template_h_header is not None:
            template_h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.templates_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.templates_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.templates_table)

        btns = QHBoxLayout()
        btns.addStretch()

        add_btn = QPushButton("추가")
        add_btn.clicked.connect(self.add_template)
        btns.addWidget(add_btn)

        edit_btn = QPushButton("편집")
        edit_btn.clicked.connect(self.edit_template)
        btns.addWidget(edit_btn)

        del_btn = QPushButton("삭제")
        del_btn.clicked.connect(self.delete_template)
        btns.addWidget(del_btn)

        reset_btn = QPushButton("기본값으로 초기화")
        reset_btn.clicked.connect(self.reset_templates_default)
        btns.addWidget(reset_btn)

        layout.addLayout(btns)
        return widget

    def _refresh_message_templates_table(self):
        if not hasattr(self, "templates_table"):
            return
        templates = self._message_templates or []
        self.templates_table.setRowCount(len(templates))
        for i, t in enumerate(templates):
            name = getattr(t, "name", "")
            platform = getattr(t, "platform", "all") or "all"
            content = getattr(t, "content", "")
            preview = content.replace("\n", " ")
            if len(preview) > 80:
                preview = preview[:77] + "..."

            self.templates_table.setItem(i, 0, QTableWidgetItem(name))
            self.templates_table.setItem(i, 1, QTableWidgetItem(platform))
            self.templates_table.setItem(i, 2, QTableWidgetItem(preview))

    def _selected_template_index(self) -> int:
        row = self.templates_table.currentRow()
        return row if row >= 0 else -1

    def add_template(self):
        dlg = MessageTemplateEditDialog(parent=self)
        if dlg.exec():
            self._message_templates.append(dlg.get_template())
            self._refresh_message_templates_table()

    def edit_template(self):
        idx = self._selected_template_index()
        if idx < 0 or idx >= len(self._message_templates):
            QMessageBox.information(self, "알림", "편집할 템플릿을 선택하세요.")
            return
        dlg = MessageTemplateEditDialog(template=self._message_templates[idx], parent=self)
        if dlg.exec():
            self._message_templates[idx] = dlg.get_template()
            self._refresh_message_templates_table()

    def delete_template(self):
        idx = self._selected_template_index()
        if idx < 0 or idx >= len(self._message_templates):
            QMessageBox.information(self, "알림", "삭제할 템플릿을 선택하세요.")
            return
        if QMessageBox.question(self, "확인", "선택한 템플릿을 삭제하시겠습니까?") != QMessageBox.StandardButton.Yes:
            return
        self._message_templates.pop(idx)
        self._refresh_message_templates_table()

    def reset_templates_default(self):
        if QMessageBox.question(self, "확인", "기본 템플릿으로 초기화하시겠습니까?") != QMessageBox.StandardButton.Yes:
            return
        self._message_templates = [
            MessageTemplate(name=t.name, content=t.content, platform=t.platform)
            for t in MessageTemplateManager.DEFAULT_TEMPLATES
        ]
        self._refresh_message_templates_table()

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


class CleanupWorker(QThread):
    """Run DB cleanup in a background thread."""

    completed = pyqtSignal(int)
    failed = pyqtSignal(str)

    def __init__(self, db_path: str, days: int, exclude_favorites: bool, exclude_noted: bool):
        super().__init__()
        self.db_path = db_path
        self.days = days
        self.exclude_favorites = exclude_favorites
        self.exclude_noted = exclude_noted

    def run(self):
        try:
            from db import DatabaseManager
            db = DatabaseManager(self.db_path)
            try:
                deleted = db.cleanup_old_listings(
                    days=self.days,
                    exclude_favorites=self.exclude_favorites,
                    exclude_noted=self.exclude_noted,
                )
            finally:
                try:
                    db.close()
                except Exception:
                    pass
            self.completed.emit(int(deleted))
        except Exception as e:
            self.failed.emit(str(e))


class TagRuleEditDialog(QDialog):
    """Add/edit TagRule."""

    def __init__(self, rule: TagRule | None = None, parent=None):
        super().__init__(parent)
        self._rule = rule
        self._build_ui()
        if rule:
            self._load(rule)

    def _build_ui(self):
        self.setWindowTitle("태그 규칙 편집")
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(12)

        self.enabled_check = QCheckBox("사용")
        form.addRow("", self.enabled_check)

        self.tag_name_edit = QLineEdit()
        form.addRow("태그 이름*", self.tag_name_edit)

        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText("예: 🏷️")
        form.addRow("아이콘", self.icon_edit)

        self.color_edit = QLineEdit()
        self.color_edit.setPlaceholderText("예: #89b4fa")
        form.addRow("색상", self.color_edit)

        self.keywords_edit = QTextEdit()
        self.keywords_edit.setPlaceholderText("키워드들을 줄바꿈 또는 콤마로 구분해서 입력하세요")
        self.keywords_edit.setMinimumHeight(140)
        form.addRow("키워드*", self.keywords_edit)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()

        cancel = QPushButton("취소")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)

        ok = QPushButton("확인")
        ok.clicked.connect(self._on_ok)
        btns.addWidget(ok)

        layout.addLayout(btns)

    def _load(self, rule: TagRule):
        self.enabled_check.setChecked(getattr(rule, "enabled", True))
        self.tag_name_edit.setText(getattr(rule, "tag_name", ""))
        self.icon_edit.setText(getattr(rule, "icon", ""))
        self.color_edit.setText(getattr(rule, "color", ""))
        self.keywords_edit.setPlainText("\n".join(getattr(rule, "keywords", []) or []))

    def _on_ok(self):
        tag_name = self.tag_name_edit.text().strip()
        if not tag_name:
            QMessageBox.warning(self, "오류", "태그 이름은 필수입니다.")
            return

        raw = self.keywords_edit.toPlainText().strip()
        keywords: list[str] = []
        if raw:
            parts = []
            for line in raw.splitlines():
                parts.extend([p.strip() for p in line.split(",")])
            keywords = [p for p in parts if p]

        if not keywords:
            QMessageBox.warning(self, "오류", "키워드는 최소 1개 이상 필요합니다.")
            return

        self._result = TagRule(
            tag_name=tag_name,
            keywords=keywords,
            color=(self.color_edit.text().strip() or "#89b4fa"),
            icon=(self.icon_edit.text().strip() or "🏷️"),
            enabled=self.enabled_check.isChecked(),
        )
        self.accept()

    def get_rule(self) -> TagRule:
        return getattr(self, "_result", self._rule)  # type: ignore[return-value]


class MessageTemplateEditDialog(QDialog):
    """Add/edit MessageTemplate."""

    def __init__(self, template: MessageTemplate | None = None, parent=None):
        super().__init__(parent)
        self._template = template
        self._build_ui()
        if template:
            self._load(template)

    def _build_ui(self):
        self.setWindowTitle("메시지 템플릿 편집")
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.name_edit = QLineEdit()
        form.addRow("이름*", self.name_edit)

        self.platform_combo = QComboBox()
        self.platform_combo.addItem("all", "all")
        self.platform_combo.addItem("danggeun", "danggeun")
        self.platform_combo.addItem("bunjang", "bunjang")
        self.platform_combo.addItem("joonggonara", "joonggonara")
        form.addRow("플랫폼", self.platform_combo)

        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("변수: {title}, {price}, {seller}, {location}, {target_price}")
        self.content_edit.setMinimumHeight(180)
        form.addRow("내용*", self.content_edit)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()

        cancel = QPushButton("취소")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)

        ok = QPushButton("확인")
        ok.clicked.connect(self._on_ok)
        btns.addWidget(ok)

        layout.addLayout(btns)

    def _load(self, t: MessageTemplate):
        self.name_edit.setText(getattr(t, "name", ""))
        content = getattr(t, "content", "") or ""
        self.content_edit.setPlainText(content)
        platform = getattr(t, "platform", "all") or "all"
        idx = self.platform_combo.findData(platform)
        if idx >= 0:
            self.platform_combo.setCurrentIndex(idx)

    def _on_ok(self):
        name = self.name_edit.text().strip()
        content = self.content_edit.toPlainText().strip()
        if not name:
            QMessageBox.warning(self, "오류", "이름은 필수입니다.")
            return
        if not content:
            QMessageBox.warning(self, "오류", "내용은 필수입니다.")
            return
        self._result = MessageTemplate(
            name=name,
            content=content,
            platform=self.platform_combo.currentData(),
        )
        self.accept()

    def get_template(self) -> MessageTemplate:
        return getattr(self, "_result", self._template)  # type: ignore[return-value]


class NotificationTestThread(QThread):
    """Thread for testing notifications asynchronously"""
    finished = pyqtSignal(bool, str)
    
    def __init__(self, notifier_type, **kwargs):
        super().__init__()
        self.notifier_type = notifier_type
        self.kwargs = kwargs
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if self.notifier_type == NotificationType.TELEGRAM:
                token = str(self.kwargs.get('token') or "")
                chat_id = str(self.kwargs.get('chat_id') or "")
                notifier = TelegramNotifier(
                    token, 
                    chat_id
                )
                success = loop.run_until_complete(
                    notifier.send_message("🔔 [테스트] 중고거래 알리미 알림 테스트입니다.")
                )
                if success:
                    self.finished.emit(True, "텔레그램 알림 전송 성공!")
                else:
                    self.finished.emit(False, "알림 전송 실패. 설정(토큰/ID)을 확인하세요.")
                    
            elif self.notifier_type == NotificationType.DISCORD:
                url = str(self.kwargs.get('url') or "")
                notifier = DiscordNotifier(url)
                success = loop.run_until_complete(
                    notifier.send_message("🔔 [테스트] 중고거래 알리미 알림 테스트입니다.")
                )
                if success:
                    self.finished.emit(True, "디스코드 알림 전송 성공!")
                else:
                    self.finished.emit(False, "알림 전송 실패. Webhook URL을 확인하세요.")
            
            elif self.notifier_type == NotificationType.SLACK:
                url = str(self.kwargs.get('url') or "")
                notifier = SlackNotifier(url)
                success = loop.run_until_complete(
                    notifier.send_message("🔔 [테스트] 중고거래 알리미 알림 테스트입니다.")
                )
                if success:
                    self.finished.emit(True, "슬랙 알림 전송 성공!")
                else:
                    self.finished.emit(False, "알림 전송 실패. Webhook URL을 확인하세요.")
            
            loop.close()
            
        except Exception as e:
            self.finished.emit(False, f"오류 발생: {str(e)}")

