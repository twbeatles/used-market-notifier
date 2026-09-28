"""Background worker threads for the main window."""

import asyncio
import sys

from PySide6.QtCore import QThread, Signal

from monitor_engine import MonitorEngine


def new_engine_event_loop() -> asyncio.AbstractEventLoop:
    """Create the monitor thread's event loop without the deprecated policy API.

    Windows needs a Proactor loop: Playwright launches its driver as a subprocess,
    which the Selector loop does not support there.
    """
    if sys.platform == "win32":
        proactor = getattr(asyncio, "ProactorEventLoop", None)
        if proactor is not None:
            return proactor()
    return asyncio.new_event_loop()


class MonitorThread(QThread):
    """Thread for running the async monitor loop.

    ``request_stop()`` only signals the engine and returns immediately; the thread
    finishes once the engine loop has unwound and cleaned up. Callers keep a
    reference to the thread until ``finished`` fires (dropping a running QThread
    aborts the process).
    """

    status_update = Signal(str)
    new_item = Signal(object)
    price_change = Signal(object, str, str)
    error = Signal(str)

    # Stop requested but the engine is still busy (e.g. a slow page load): cancel it.
    FORCE_CANCEL_AFTER_SECONDS = 20.0

    def __init__(self, engine: MonitorEngine):
        super().__init__()
        self.engine = engine
        self.loop: asyncio.AbstractEventLoop | None = None
        self._stop_requested = False

    def run(self):
        self.loop = new_engine_event_loop()
        asyncio.set_event_loop(self.loop)

        self.engine.on_status_update = lambda s: self.status_update.emit(s)
        self.engine.on_new_item = lambda i: self.new_item.emit(i)
        self.engine.on_price_change = lambda i, o, n: self.price_change.emit(i, o, n)
        self.engine.on_error = lambda e: self.error.emit(e)

        try:
            if not self._stop_requested:
                self.loop.run_until_complete(self.engine.start())
        except Exception as e:
            if not self._stop_requested:  # Only report errors if not intentionally stopped
                import logging
                import traceback

                logging.getLogger("MonitorThread").error(f"MonitorThread error: {e}\n{traceback.format_exc()}")
                self.error.emit(str(e))
        finally:
            # Always try to close engine resources (driver/executor/db) before loop shutdown.
            try:
                if self.loop and not self.loop.is_closed():
                    self.loop.run_until_complete(self.engine.close())
            except Exception:
                pass

            # Clean up pending tasks
            try:
                pending = asyncio.all_tasks(self.loop)
                for task in pending:
                    task.cancel()
                # Allow cancelled tasks to complete
                if pending:
                    self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            try:
                self.loop.close()
            except Exception:
                pass
            asyncio.set_event_loop(None)

    def _force_cancel(self) -> None:
        task = getattr(self.engine, "_start_task", None)
        if task is not None and not task.done():
            task.cancel()

    def _signal_engine_stop(self) -> None:
        """Runs on the engine loop thread."""
        request_stop = getattr(self.engine, "request_stop", None)
        if callable(request_stop):
            request_stop()
        loop = self.loop
        if loop is not None and not loop.is_closed():
            loop.call_later(self.FORCE_CANCEL_AFTER_SECONDS, self._force_cancel)

    def request_stop(self) -> None:
        """Signal the engine to stop without blocking the caller (UI thread)."""
        if self._stop_requested:
            return
        self._stop_requested = True
        self.engine.running = False
        loop = self.loop
        if loop is None or loop.is_closed():
            return
        try:
            loop.call_soon_threadsafe(self._signal_engine_stop)
        except RuntimeError:
            pass  # loop already closed

    def stop(self, timeout_ms: int = 30000) -> bool:
        """Request stop and block until the thread finishes (shutdown/restore paths)."""
        self.request_stop()
        return self.wait(timeout_ms)


class MaintenanceCleanupThread(QThread):
    """Run one-off maintenance tasks (cleanup) without blocking the UI."""

    completed = Signal(int)
    failed = Signal(str)

    def __init__(self, db_path: str, days: int, exclude_favorites: bool, exclude_noted: bool):
        super().__init__()
        self.db_path = db_path
        self.days = days
        self.exclude_favorites = exclude_favorites
        self.exclude_noted = exclude_noted

    def run(self):
        try:
            from db import DatabaseManager
            db = DatabaseManager(self.db_path)
            try:
                deleted = db.cleanup_old_listings(
                    days=self.days,
                    exclude_favorites=self.exclude_favorites,
                    exclude_noted=self.exclude_noted,
                )
            finally:
                try:
                    db.close()
                except Exception:
                    pass
            self.completed.emit(int(deleted))
        except Exception as e:
            self.failed.emit(str(e))
