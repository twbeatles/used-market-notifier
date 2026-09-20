# pyright: reportAttributeAccessIssue=false
"""Notifier channel initialization (NotificationRuntimeMixin part)."""

from models import NotificationType
from notifiers import DiscordNotifier, SlackNotifier, TelegramNotifier

from ..types import NotifierProtocol


class NotificationChannelsMixin:
    def initialize_notifiers(self):
        """Initialize notification channels based on settings."""
        self.notifiers.clear()

        for config in self.settings.settings.notifiers:
            if not config.enabled:
                continue

            try:
                if config.type == NotificationType.TELEGRAM:
                    if config.token and config.chat_id:
                        notifier = TelegramNotifier(config.token, config.chat_id)
                        self.notifiers.append(notifier)
                        self.logger.info("Telegram notifier initialized")

                elif config.type == NotificationType.DISCORD:
                    if config.webhook_url:
                        notifier = DiscordNotifier(config.webhook_url)
                        self.notifiers.append(notifier)
                        self.logger.info("Discord notifier initialized")

                elif config.type == NotificationType.SLACK:
                    if config.webhook_url:
                        notifier = SlackNotifier(config.webhook_url)
                        self.notifiers.append(notifier)
                        self.logger.info("Slack notifier initialized")

            except Exception as e:
                self.logger.error(f"Failed to initialize {config.type.value} notifier: {e}")

    @staticmethod
    def _notifier_type(notifier: NotifierProtocol) -> str:
        return notifier.__class__.__name__.replace("Notifier", "").lower()


__all__ = ["NotificationChannelsMixin"]
