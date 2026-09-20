# pyright: reportAttributeAccessIssue=false
"""Public enqueue API: queue notifications without blocking the search loop."""

from time import perf_counter

from models import Item

from ..notifications import NotificationJob


class NotificationQueueMixin:
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


__all__ = ["NotificationQueueMixin"]
