"""Settings dialog mixin: persistence."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QLineEdit, QSpinBox, QCheckBox, QLabel,
    QGroupBox, QPushButton, QComboBox, QMessageBox, QFrame,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from models import NotificationType, NotificationSchedule, TagRule, MessageTemplate
from auto_tagger import AutoTagger
from message_templates import MessageTemplateManager

class SettingsPersistenceMixin:
    """Persistence settings panel behavior."""

    def load_settings(self):
        s = self.settings.settings

        self.interval_spin.setValue(s.check_interval_seconds)
        self.headless_check.setChecked(s.headless_mode)
        self.metadata_enrichment_check.setChecked(getattr(s, "metadata_enrichment_enabled", False))
        if hasattr(self, "conditional_metadata_enrichment_check"):
            self.conditional_metadata_enrichment_check.setChecked(
                getattr(s, "conditional_metadata_enrichment_enabled", True)
            )
        if hasattr(self, "scraper_mode_combo"):
            idx = self.scraper_mode_combo.findData(getattr(s, "scraper_mode", "playwright_primary"))
            self.scraper_mode_combo.setCurrentIndex(idx if idx >= 0 else 0)
        if hasattr(self, "fallback_on_empty_check"):
            self.fallback_on_empty_check.setChecked(getattr(s, "fallback_on_empty_results", True))
        if hasattr(self, "max_fallback_spin"):
            self.max_fallback_spin.setValue(int(getattr(s, "max_fallback_per_cycle", 3) or 0))
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
        s.metadata_enrichment_enabled = self.metadata_enrichment_check.isChecked()
        if hasattr(self, "conditional_metadata_enrichment_check"):
            s.conditional_metadata_enrichment_enabled = self.conditional_metadata_enrichment_check.isChecked()
        if hasattr(self, "scraper_mode_combo"):
            s.scraper_mode = self.scraper_mode_combo.currentData()
        if hasattr(self, "fallback_on_empty_check"):
            s.fallback_on_empty_results = self.fallback_on_empty_check.isChecked()
        if hasattr(self, "max_fallback_spin"):
            s.max_fallback_per_cycle = self.max_fallback_spin.value()
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
