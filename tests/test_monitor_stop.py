"""Regression: responsive, non-blocking monitor stop and serialized restarts (ISSUE-006)."""

import asyncio
import concurrent.futures
import os
import shutil
import tempfile
import time
import unittest
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from db import DatabaseManager
from models import AppSettings, Item, SearchKeyword
from monitor_engine import MonitorEngine


class _Settings:
    def __init__(self, keywords):
        self.settings = AppSettings(notifications_enabled=False, scraper_mode="selenium_only")
        self.settings.keywords = keywords


class _StopDuringSearchScraper:
    def __init__(self, engine_ref):
        self.engine_ref = engine_ref
        self.calls = 0

    def safe_search(self, keyword, location=None):
        self.calls += 1
        engine = self.engine_ref[0]
        # The user presses "stop" while the first keyword is being searched.
        engine._loop.call_soon_threadsafe(engine.request_stop)
        return [
            Item(
                platform="bunjang",
                article_id=f"{keyword}-1",
                title=f"{keyword} 매물",
                price="10,000원",
                link=f"https://m.bunjang.co.kr/products/{abs(hash(keyword)) % 100000}",
                keyword=keyword,
            )
        ]

    def enrich_item(self, item):
        return item

    def is_healthy(self):
        return True

    def close(self):
        return None


class EngineStopCheckTest(unittest.IsolatedAsyncioTestCase):
    async def test_stop_requested_mid_cycle_skips_remaining_keywords(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = DatabaseManager(os.path.join(tmp, "t.db"))
            keywords = [SearchKeyword(keyword=k, platforms=["bunjang"]) for k in ("a", "b", "c")]
            engine = MonitorEngine(_Settings(keywords), db=db)
            engine._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
            engine._stop_event = asyncio.Event()
            engine._loop = asyncio.get_running_loop()
            scraper = _StopDuringSearchScraper([engine])
            engine.primary_scrapers["bunjang"] = scraper
            engine.primary_scraper_kind["bunjang"] = "selenium"

            async def _ensure(platform, use_fallback=False):
                return not use_fallback

            engine._ensure_scraper = _ensure
            await engine.run_cycle()
            self.assertEqual(scraper.calls, 1)
            engine._executor.shutdown(wait=True)
            db.close()

    async def test_stop_before_start_prevents_monitoring(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = DatabaseManager(os.path.join(tmp, "t.db"))
            engine = MonitorEngine(_Settings([]), db=db)
            engine.request_stop()
            engine.initialize_scrapers = mock.AsyncMock()
            await engine.start()
            engine.initialize_scrapers.assert_not_called()
            db.close()


class _SlowEngine:
    """Minimal MonitorEngine stand-in: runs until stopped, then cleans up slowly."""

    instances: list["_SlowEngine"] = []

    def __init__(self, *args, **kwargs):
        self.db = kwargs.get("db")
        self.running = False
        self.is_first_run = kwargs.get("suppress_initial_notifications", True)
        self._stop_event = None
        self._start_task = None
        self.cleanup_seconds = 0.6
        self.active_at_start: list[int] = []
        _SlowEngine.instances.append(self)
        self.on_status_update = self.on_new_item = self.on_price_change = self.on_error = None

    async def start(self):
        self.active_at_start.append(sum(1 for e in _SlowEngine.instances if e.running))
        self.running = True
        self._stop_event = asyncio.Event()
        self._start_task = asyncio.current_task()
        try:
            await self._stop_event.wait()
        finally:
            await asyncio.sleep(self.cleanup_seconds)  # scraper/browser teardown
            self.running = False

    def request_stop(self):
        if self._stop_event is not None:
            self._stop_event.set()

    async def close(self):
        return None


def _pyside_fluent_available() -> bool:
    try:
        import qfluentwidgets  # noqa: F401
        from PySide6.QtWidgets import QApplication  # noqa: F401
    except Exception:
        return False
    return True


@unittest.skipUnless(_pyside_fluent_available(), "requires PySide6 + qfluentwidgets")
class WindowStopLifecycleTest(unittest.TestCase):
    def setUp(self):
        from PySide6.QtWidgets import QApplication

        from gui.main_window import MainWindow
        from settings_manager import SettingsManager

        _SlowEngine.instances = []
        self.app = QApplication.instance() or QApplication([])
        self._old_cwd = os.getcwd()
        self.tmp = tempfile.mkdtemp(prefix="umn_stop_test_")
        os.chdir(self.tmp)
        manager = SettingsManager(settings_path=os.path.join(self.tmp, "settings.json"))
        manager.settings.db_path = os.path.join(self.tmp, "listings.db")
        manager.settings.auto_backup_enabled = False
        manager.settings.auto_start_monitoring = False
        manager.settings.keywords = [SearchKeyword(keyword="아이폰", platforms=["bunjang"])]
        self.patcher = mock.patch("gui.main.window_mixins.monitoring.MonitorEngine", _SlowEngine)
        self.patcher.start()
        self.window = MainWindow(settings_manager=manager)

    def tearDown(self):
        self.window.stop_monitoring(wait=True, timeout_ms=10000)
        self.patcher.stop()
        try:
            self.window.db.close()
        except Exception:
            pass
        self.window.hide()
        self.window.deleteLater()
        os.chdir(self._old_cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _pump_until(self, predicate, timeout=10.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.app.processEvents()
            if predicate():
                return True
            time.sleep(0.01)
        return False

    def _wait_running(self, engine):
        self.assertTrue(self._pump_until(lambda: engine.running), "engine did not start")

    def test_stop_does_not_block_ui_thread(self):
        self.window.start_monitoring()
        engine = _SlowEngine.instances[-1]
        self._wait_running(engine)

        started = time.perf_counter()
        self.window.stop_monitoring()
        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, 0.2)
        self.assertTrue(self.window.is_monitoring_active(), "thread must be kept while shutting down")
        self.assertTrue(self._pump_until(lambda: not self.window.is_monitoring_active()))

    def test_restart_waits_for_previous_thread(self):
        self.window.start_monitoring()
        first = _SlowEngine.instances[-1]
        self._wait_running(first)
        self.assertTrue(first.is_first_run, "first engine of the process suppresses its first cycle")

        self.window.restart_monitoring()
        self.assertEqual(len(_SlowEngine.instances), 1, "new engine must wait for the old thread")
        self.assertTrue(
            self._pump_until(lambda: len(_SlowEngine.instances) == 2 and _SlowEngine.instances[-1].running)
        )
        second = _SlowEngine.instances[-1]
        self.assertEqual(second.active_at_start, [0], "old engine must have finished before the new one starts")
        self.assertFalse(second.is_first_run, "in-app restarts must not drop first-cycle notifications")

    def test_wait_stop_blocks_until_finished(self):
        self.window.start_monitoring()
        self._wait_running(_SlowEngine.instances[-1])
        self.assertTrue(self.window.stop_monitoring(wait=True, timeout_ms=10000))
        self.assertFalse(self.window.is_monitoring_active())


if __name__ == "__main__":
    unittest.main()
