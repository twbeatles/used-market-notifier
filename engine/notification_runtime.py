# pyright: reportAttributeAccessIssue=false
"""NotificationRuntimeMixin for MonitorEngine."""

from .common import *


class NotificationRuntimeMixin:
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

    def _build_notification_preview(self, job: NotificationJob) -> str:
        prefix = "Price change" if job.is_price_change else "New item"
        if job.is_price_change and job.old_price and job.new_price:
            return f"{prefix}: {job.item.title} ({job.old_price} -> {job.new_price})"
        return f"{prefix}: {job.item.title}"

    async def _start_notification_worker(self) -> None:
        """Ensure notification queue worker is running."""
        if self._notification_queue is None:
            self._notification_queue = asyncio.Queue()
        if self._notification_worker_task is None or self._notification_worker_task.done():
            self._notification_worker_task = asyncio.create_task(
                self._notification_worker(), name="notification-worker"
            )

    async def _notification_worker(self) -> None:
        """Background worker that drains notification queue with retry."""
        queue = self._notification_queue
        if queue is None:
            return

        while True:
            if self._stop_event is not None and self._stop_event.is_set() and queue.empty():
                break
            try:
                job: NotificationJob = await asyncio.wait_for(queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            try:
                queue_wait_ms = (perf_counter() - job.enqueued_at) * 1000 if job.enqueued_at else 0.0
                result = await self._deliver_notification_channels(job, queue_wait_ms=queue_wait_ms)
                if result.failed_channels and job.attempts < self.NOTIFICATION_MAX_RETRIES - 1:
                    if self._stop_event is not None and self._stop_event.is_set():
                        self.logger.info("Notification retry skipped because shutdown is in progress")
                        continue
                    retry = NotificationJob(
                        item=job.item,
                        is_price_change=job.is_price_change,
                        old_price=job.old_price,
                        new_price=job.new_price,
                        listing_id=job.listing_id,
                        attempts=job.attempts + 1,
                        enqueued_at=perf_counter(),
                        target_channels=list(result.failed_channels),
                    )
                    backoff = min(2 ** retry.attempts, 8)
                    self.logger.warning(
                        f"Notification retry scheduled attempt={retry.attempts + 1}/{self.NOTIFICATION_MAX_RETRIES} "
                        f"channels={','.join(retry.target_channels)}"
                    )
                    await self._sleep_or_stop(backoff)
                    if self._stop_event is not None and self._stop_event.is_set():
                        self.logger.info("Notification retry cancelled after shutdown signal")
                        continue
                    await queue.put(retry)
            except Exception as e:
                self.logger.error(f"Notification worker error: {e}")
            finally:
                queue.task_done()

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

    def _notification_policy(self) -> NotificationPolicyDecision:
        return NotificationPolicy(self.settings.settings).evaluate()

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

    async def send_notifications(
        self,
        item: Item,
        is_price_change: bool = False,
        old_price: str | None = None,
        new_price: str | None = None,
        listing_id: int | None = None,
    ) -> None:
        """Queue notifications so the search loop is never blocked by network I/O."""
        base_job = NotificationJob(
            item=item,
            is_price_change=is_price_change,
            old_price=old_price,
            new_price=new_price,
            listing_id=listing_id,
            enqueued_at=perf_counter(),
        )
        decision = self._notification_policy()
        if not decision.allowed:
            self._log_notification_skip(base_job, decision.status, decision.reason)
            return
        if self._notification_queue is None:
            # Fallback (worker not ready yet): deliver inline.
            await self._deliver_notification_channels(base_job)
            return

        await self._notification_queue.put(base_job)
        qsize = self._notification_queue.qsize()
        if qsize >= 20:
            self.logger.warning(f"Notification queue backlog size={qsize}")
