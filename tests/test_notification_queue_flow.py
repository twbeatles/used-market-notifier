import asyncio
import os
import tempfile
import unittest

from db import DatabaseManager
from models import AppSettings, Item
from monitor_engine import MonitorEngine


class _SettingsWrapper:
    def __init__(self):
        self.settings = AppSettings(notifications_enabled=True)


class TelegramNotifier:
    def __init__(self):
        self.calls = 0
        self._last_delivery_result = {"success": False, "error_message": None, "rate_limited": False}

    async def send_message(self, text: str) -> bool:
        _ = text
        self._last_delivery_result = {"success": True, "error_message": None, "rate_limited": False}
        return True

    async def send_item(self, item: Item, with_image: bool = True) -> bool:
        _ = (item, with_image)
        self.calls += 1
        self._last_delivery_result = {"success": True, "error_message": None, "rate_limited": False}
        return True

    async def send_price_change(self, item: Item, old_price: str, new_price: str) -> bool:
        _ = (item, old_price, new_price)
        self.calls += 1
        self._last_delivery_result = {"success": True, "error_message": None, "rate_limited": False}
        return True

    def get_last_delivery_result(self) -> dict:
        return dict(self._last_delivery_result)


class DiscordNotifier:
    def __init__(self):
        self.calls = 0
        self._last_delivery_result = {"success": False, "error_message": None, "rate_limited": False}

    async def send_message(self, text: str) -> bool:
        _ = text
        self._last_delivery_result = {"success": True, "error_message": None, "rate_limited": False}
        return True

    async def send_item(self, item: Item, with_image: bool = True) -> bool:
        _ = (item, with_image)
        self.calls += 1
        success = self.calls >= 2
        self._last_delivery_result = {
            "success": success,
            "error_message": None if success else "temporary failure",
            "rate_limited": False,
        }
        return success

    async def send_price_change(self, item: Item, old_price: str, new_price: str) -> bool:
        _ = (item, old_price, new_price)
        return await self.send_item(item)

    def get_last_delivery_result(self) -> dict:
        return dict(self._last_delivery_result)


class AlwaysFailNotifier(DiscordNotifier):
    async def send_item(self, item: Item, with_image: bool = True) -> bool:
        _ = (item, with_image)
        self.calls += 1
        self._last_delivery_result = {
            "success": False,
            "error_message": "still failing",
            "rate_limited": False,
        }
        return False


class TestNotificationQueueFlow(unittest.IsolatedAsyncioTestCase):
    async def test_partial_channel_retry_and_delivery_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            db = DatabaseManager(db_path)
            try:
                engine = MonitorEngine(_SettingsWrapper(), db=db)
                telegram = TelegramNotifier()
                discord = DiscordNotifier()
                engine.notifiers = [telegram, discord]
                engine._notification_queue = asyncio.Queue()
                engine._stop_event = asyncio.Event()

                async def _no_sleep(seconds: float) -> None:
                    _ = seconds
                    return

                engine._sleep_or_stop = _no_sleep
                engine._notification_worker_task = asyncio.create_task(engine._notification_worker())

                item = Item(
                    platform="danggeun",
                    article_id="a1",
                    title="test item",
                    price="10,000원",
                    link="https://example.com/a1",
                    keyword="test",
                )
                _, _, listing_id = db.add_listing(item)
                assert listing_id is not None

                await engine.send_notifications(item, listing_id=listing_id)
                await asyncio.wait_for(engine._notification_queue.join(), timeout=3.0)

                self.assertEqual(telegram.calls, 1)
                self.assertEqual(discord.calls, 2)

                success_logs = db.get_notification_logs(limit=10)
                self.assertEqual(len(success_logs), 2)
                self.assertEqual({row["notification_type"] for row in success_logs}, {"telegram", "discord"})

                summary = db.get_notification_delivery_summary(days=7)
                self.assertEqual(summary["telegram"]["success_count"], 1)
                self.assertEqual(summary["telegram"]["failed_count"], 0)
                self.assertEqual(summary["discord"]["success_count"], 1)
                self.assertEqual(summary["discord"]["failed_count"], 1)
                self.assertEqual(summary["discord"]["last_failure_message"], "temporary failure")

                engine._stop_event.set()
                await engine._drain_notification_queue()
            finally:
                db.close()

    async def test_shutdown_does_not_requeue_failed_notification(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            db = DatabaseManager(db_path)
            try:
                engine = MonitorEngine(_SettingsWrapper(), db=db)
                failing = AlwaysFailNotifier()
                engine.notifiers = [failing]
                engine._notification_queue = asyncio.Queue()
                engine._stop_event = asyncio.Event()

                async def _set_stop(seconds: float) -> None:
                    _ = seconds
                    assert engine._stop_event is not None
                    engine._stop_event.set()

                engine._sleep_or_stop = _set_stop  # type: ignore[method-assign]
                engine._notification_worker_task = asyncio.create_task(engine._notification_worker())

                item = Item(
                    platform="danggeun",
                    article_id="a2",
                    title="test item 2",
                    price="10,000원",
                    link="https://example.com/a2",
                    keyword="test",
                )
                _, _, listing_id = db.add_listing(item)
                assert listing_id is not None

                await engine.send_notifications(item, listing_id=listing_id)
                await asyncio.wait_for(engine._notification_queue.join(), timeout=3.0)

                self.assertEqual(failing.calls, 1)
                self.assertEqual(engine._notification_queue.qsize(), 0)
                await engine._drain_notification_queue()
            finally:
                db.close()

    async def test_disabled_notifications_record_skip_telemetry(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            db = DatabaseManager(db_path)
            try:
                settings = _SettingsWrapper()
                settings.settings.notifications_enabled = False
                engine = MonitorEngine(settings, db=db)
                item = Item(
                    platform="danggeun",
                    article_id="a3",
                    title="test item 3",
                    price="10,000원",
                    link="https://example.com/a3",
                    keyword="test",
                )
                _, _, listing_id = db.add_listing(item)
                assert listing_id is not None

                await engine.send_notifications(item, listing_id=listing_id)

                with db.lock:
                    cur = db.conn.cursor()
                    cur.execute(
                        "SELECT notification_type, status FROM notification_delivery_log WHERE listing_id = ?",
                        (listing_id,),
                    )
                    row = cur.fetchone()
                self.assertEqual(row["notification_type"], "system")
                self.assertEqual(row["status"], "skipped_disabled")
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
