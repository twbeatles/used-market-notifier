"""Background worker threads for the main window."""

import asyncio
from PyQt6.QtCore import QThread, pyqtSignal

from monitor_engine import MonitorEngine


class MonitorThread(QThread):
    """Thread for running the async monitor loop"""
    
    status_update = pyqtSignal(str)
    new_item = pyqtSignal(object)
    price_change = pyqtSignal(object, str, str)
    error = pyqtSignal(str)
    
    def __init__(self, engine: MonitorEngine):
        super().__init__()
        self.engine = engine
        self.loop = None
        self._stop_requested = False
    
    def run(self):
        # Ensure a Windows-compatible event loop policy for background asyncio work.
        import sys
        if sys.platform == 'win32':
            proactor_policy = getattr(asyncio, "WindowsProactorEventLoopPolicy", None)
            if proactor_policy is not None:
                asyncio.set_event_loop_policy(proactor_policy())
        
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        self.engine.on_status_update = lambda s: self.status_update.emit(s)
        self.engine.on_new_item = lambda i: self.new_item.emit(i)
        self.engine.on_price_change = lambda i, o, n: self.price_change.emit(i, o, n)
        self.engine.on_error = lambda e: self.error.emit(e)
        
        try:
            self.loop.run_until_complete(self.engine.start())
        except Exception as e:
            if not self._stop_requested:  # Only report errors if not intentionally stopped
                import traceback
                error_msg = f"{str(e)}\n{traceback.format_exc()}"
                print(f"MonitorThread error: {error_msg}")
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
    
    def stop(self):
        self._stop_requested = True
        self.engine.running = False  # Signal engine to stop
        
        if self.loop and self.loop.is_running():
            # Schedule async close and wait for it (ensures DB close too)
            future = asyncio.run_coroutine_threadsafe(self.engine.close(), self.loop)
            try:
                future.result(timeout=5.0)  # Wait max 5 seconds for stop
            except Exception:
                # If close is stuck, stop the loop to unwind run_until_complete and trigger finally cleanup.
                self.loop.call_soon_threadsafe(self.loop.stop)


class MaintenanceCleanupThread(QThread):
    """Run one-off maintenance tasks (cleanup) without blocking the UI."""

    completed = pyqtSignal(int)
    failed = pyqtSignal(str)

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
