"""Enhanced settings dialog with modern design."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton,
)
from models import TagRule, MessageTemplate
from backup_manager import BackupManager

from .editors import MessageTemplateEditDialog, TagRuleEditDialog
from .workers import CleanupWorker, NotificationTestThread
from .mixins import (
    GeneralSettingsMixin,
    NotificationSettingsMixin,
    ScheduleSettingsMixin,
    SellerSettingsMixin,
    MaintenanceSettingsMixin,
    AutoTaggingSettingsMixin,
    MessageTemplatesSettingsMixin,
    SettingsPersistenceMixin,
)

class SettingsDialog(
    GeneralSettingsMixin,
    NotificationSettingsMixin,
    ScheduleSettingsMixin,
    SellerSettingsMixin,
    MaintenanceSettingsMixin,
    AutoTaggingSettingsMixin,
    MessageTemplatesSettingsMixin,
    SettingsPersistenceMixin,
    QDialog,
):
    """Modern settings dialog with tab navigation."""

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

