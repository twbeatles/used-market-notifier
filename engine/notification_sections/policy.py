# pyright: reportAttributeAccessIssue=false
"""Notification policy helpers: evaluation, preview, skip telemetry."""

from ..notifications import (
    NotificationJob,
    NotificationPolicy,
    NotificationPolicyDecision,
)


class NotificationPolicyMixin:
    def _notification_policy(self) -> NotificationPolicyDecision:
        return NotificationPolicy(self.settings.settings).evaluate()

    def _build_notification_preview(self, job: NotificationJob) -> str:
        prefix = "Price change" if job.is_price_change else "New item"
        if job.is_price_change and job.old_price and job.new_price:
            return f"{prefix}: {job.item.title} ({job.old_price} -> {job.new_price})"
        return f"{prefix}: {job.item.title}"

    def _log_notification_skip(self, job: NotificationJob, status: str, reason: str) -> None:
        self.logger.info("Notification %s: %s", status, reason)
        if not job.listing_id:
            return
        try:
            self.db.log_notification_delivery(
                job.listing_id,
                "system",
                status,
                attempt=job.attempts + 1,
                error_message=reason,
                rate_limited=False,
            )
        except Exception as e:
            self.logger.warning(f"Failed to record notification skip telemetry: {e}")


__all__ = ["NotificationPolicyMixin"]
