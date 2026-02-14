# gui/settings_dialog.py
"""Enhanced settings dialog with modern design"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QLineEdit, QSpinBox, QCheckBox, QLabel,
    QGroupBox, QPushButton, QComboBox, QMessageBox, QFrame,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from models import NotificationType, NotificationSchedule, ThemeMode
from notifiers import TelegramNotifier, DiscordNotifier, SlackNotifier
import asyncio


class SettingsDialog(QDialog):
    """Modern settings dialog with tab navigation"""
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.setup_ui()
        self.load_settings()
    
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
        self.seller_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
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

    def load_blocked_sellers(self):
        """Load blocked sellers from DB"""
        if not self.parent():
            return
            
        try:
            db = self.parent().engine.db
            sellers = db.get_blocked_sellers()
            self.seller_table.setRowCount(len(sellers))
            for i, seller in enumerate(sellers):
                self.seller_table.setItem(i, 0, QTableWidgetItem(seller['platform']))
                self.seller_table.setItem(i, 1, QTableWidgetItem(seller['seller_name']))
                self.seller_table.setItem(i, 2, QTableWidgetItem(seller['created_at'][:10]))
        except Exception as e:
            print(f"Error loading sellers: {e}")

    def unblock_seller(self):
        """Unblock selected seller"""
        row = self.seller_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "알림", "차단 해제할 판매자를 선택하세요.")
            return
            
        platform = self.seller_table.item(row, 0).text()
        seller = self.seller_table.item(row, 1).text()
        
        if QMessageBox.question(self, "확인", f"'{seller}' 판매자의 차단을 해제하시겠습니까?") == QMessageBox.StandardButton.Yes:
            try:
                db = self.parent().engine.db
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
                notifier = TelegramNotifier(
                    self.kwargs.get('token'), 
                    self.kwargs.get('chat_id')
                )
                success = loop.run_until_complete(
                    notifier.send_message("🔔 [테스트] 중고거래 알리미 알림 테스트입니다.")
                )
                if success:
                    self.finished.emit(True, "텔레그램 알림 전송 성공!")
                else:
                    self.finished.emit(False, "알림 전송 실패. 설정(토큰/ID)을 확인하세요.")
                    
            elif self.notifier_type == NotificationType.DISCORD:
                notifier = DiscordNotifier(self.kwargs.get('url'))
                success = loop.run_until_complete(
                    notifier.send_message("🔔 [테스트] 중고거래 알리미 알림 테스트입니다.")
                )
                if success:
                    self.finished.emit(True, "디스코드 알림 전송 성공!")
                else:
                    self.finished.emit(False, "알림 전송 실패. Webhook URL을 확인하세요.")
            
            elif self.notifier_type == NotificationType.SLACK:
                notifier = SlackNotifier(self.kwargs.get('url'))
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

