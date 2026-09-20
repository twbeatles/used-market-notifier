# pyright: reportAttributeAccessIssue=false
"""Channel-level notification delivery with per-channel telemetry."""

from ..notifications import NotificationDeliveryResult, NotificationJob


class NotificationDeliveryMixin:
    async def _deliver_notification(self, job: NotificationJob, queue_wait_ms: float = 0.0) -> bool:
        """Send one notification job to all configured channels."""
        decision = self._notification_policy()
        if not decision.allowed:
            return True
        if not self.notifiers:
            return True

        sent_count = 0
        for notifier in self.notifiers:
            try:
                if job.is_price_change:
                    success = await notifier.send_price_change(
                        job.item,
                        job.old_price or "",
                        job.new_price or "",
                    )
                else:
                    success = await notifier.send_item(job.item, with_image=True)

                if success:
                    sent_count += 1
                    if job.listing_id:
                        noti_type = notifier.__class__.__name__.replace("Notifier", "").lower()
                        msg_preview = (
                            f"{'📉 Price change' if job.is_price_change else '🆕 New item'}: {job.item.title}"
                        )
                        self.db.log_notification(job.listing_id, noti_type, msg_preview)
            except Exception as e:
                self.logger.error(f"Notification error: {e}")

        self.logger.info(
            f"[perf] notification queue_wait_ms={queue_wait_ms:.1f} "
            f"targets={len(self.notifiers)} sent={sent_count}"
        )
        return sent_count > 0

    async def _deliver_notification_channels(
        self, job: NotificationJob, queue_wait_ms: float = 0.0
    ) -> NotificationDeliveryResult:
        """Send one notification job and track channel-level outcomes."""
        result = NotificationDeliveryResult()
        decision = self._notification_policy()
        if not decision.allowed:
            self._log_notification_skip(job, decision.status, decision.reason)
            return result
        if not self.notifiers:
            self._log_notification_skip(job, "skipped_no_channel", "no notifier channels configured")
            return result

        target_channels = {channel.strip().lower() for channel in (job.target_channels or []) if channel}
        target_notifiers = [
            notifier
            for notifier in self.notifiers
            if not target_channels or self._notifier_type(notifier) in target_channels
        ]
        if not target_notifiers:
            self._log_notification_skip(job, "skipped_target_channel", "no target notifier matched retry scope")
            return result

        msg_preview = self._build_notification_preview(job)
        for notifier in target_notifiers:
            channel = self._notifier_type(notifier)
            result.attempted_channels.append(channel)
            success = False
            error_message: str | None = None
            rate_limited = False
            try:
                if job.is_price_change:
                    success = await notifier.send_price_change(
                        job.item,
                        job.old_price or "",
                        job.new_price or "",
                    )
                else:
                    success = await notifier.send_item(job.item, with_image=True)

                delivery_meta = (
                    notifier.get_last_delivery_result() if hasattr(notifier, "get_last_delivery_result") else {}
                )
                if isinstance(delivery_meta, dict):
                    rate_limited = bool(delivery_meta.get("rate_limited"))
                    error_message = delivery_meta.get("error_message") or None
                    if delivery_meta.get("success") is not None:
                        success = bool(delivery_meta.get("success"))
            except Exception as e:
                error_message = str(e)
                self.logger.error(f"Notification error ({channel}): {e}")

            if not success and not error_message:
                error_message = "send returned False"

            if success:
                result.successful_channels.append(channel)
            else:
                result.failed_channels.append(channel)

            if job.listing_id:
                self.db.log_notification_delivery(
                    job.listing_id,
                    channel,
                    "success" if success else "failed",
                    attempt=job.attempts + 1,
                    error_message=error_message,
                    rate_limited=rate_limited,
                )
                if success:
                    self.db.log_notification(job.listing_id, channel, msg_preview)

        self.logger.info(
            f"[perf] notification queue_wait_ms={queue_wait_ms:.1f} "
            f"targets={len(target_notifiers)} attempted={len(result.attempted_channels)} "
            f"sent={len(result.successful_channels)} failed={len(result.failed_channels)}"
        )
        return result


__all__ = ["NotificationDeliveryMixin"]
