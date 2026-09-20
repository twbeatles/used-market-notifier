# pyright: reportAttributeAccessIssue=false
"""System (non-listing) notification fan-out through the shared policy."""


class NotificationSystemMixin:
    async def _send_system_message(self, text: str) -> None:
        """Send a system notification message through the common notification policy."""
        decision = self._notification_policy()
        if not decision.allowed:
            self.logger.info("System notification %s: %s", decision.status, decision.reason)
            return
        if not self.notifiers:
            self.logger.info("System notification skipped_no_channel: no notifier channels configured")
            return

        for notifier in self.notifiers:
            try:
                await notifier.send_message(text)
            except Exception as e:
                channel = self._notifier_type(notifier)
                self.logger.warning(f"System notification failed ({channel}): {e}")


__all__ = ["NotificationSystemMixin"]
