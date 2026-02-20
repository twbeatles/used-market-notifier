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


class _FlakyNotifier:
    def __init__(self):
        self.calls = 0

    async def send_message(self, text: str) -> bool:
        return True

    async def send_item(self, item: Item, with_image: bool = True) -> bool:
        self.calls += 1
        # Fail once, then succeed.
        return self.calls >= 2

    async def send_price_change(self, item: Item, old_price: str, new_price: str) -> bool:
        self.calls += 1
        return True


class TestNotificationQueueFlow(unittest.IsolatedAsyncioTestCase):
    async def test_queue_retry_and_drain(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            db = DatabaseManager(db_path)
            try:
                settings = _SettingsWrapper()
                engine = MonitorEngine(settings, db=db)
                engine.notifiers = [_FlakyNotifier()]
                engine._notification_queue = asyncio.Queue()
                engine._stop_event = asyncio.Event()

                async def _no_sleep(_: float) -> None:
                    return

                engine._sleep_or_stop = _no_sleep  # speed up retry path in tests
                engine._notification_worker_task = asyncio.create_task(engine._notification_worker())

                item = Item(
                    platform="danggeun",
                    article_id="a1",
                    title="테스트 상품",
                    price="10,000원",
                    link="https://example.com/a1",
                    keyword="테스트",
                )
                _, _, listing_id = db.add_listing(item)
                self.assertIsNotNone(listing_id)

                await engine.send_notifications(item, listing_id=listing_id)
                await asyncio.wait_for(engine._notification_queue.join(), timeout=3.0)

                self.assertGreaterEqual(engine.notifiers[0].calls, 2)
                logs = db.get_notification_logs(limit=10)
                self.assertGreaterEqual(len(logs), 1)

                engine._stop_event.set()
                await engine._drain_notification_queue()
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
