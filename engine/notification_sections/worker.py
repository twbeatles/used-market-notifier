# pyright: reportAttributeAccessIssue=false
"""Background notification queue worker with channel-scoped retry."""

import asyncio
from time import perf_counter

from ..notifications import NotificationJob


class NotificationWorkerMixin:
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


__all__ = ["NotificationWorkerMixin"]
