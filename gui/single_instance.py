"""Single GUI instance per data folder (QLockFile, stale-lock aware)."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QLockFile

LOCK_FILE_NAME = ".used_market_notifier.lock"


class SingleInstanceGuard:
    """Holds the lock for the lifetime of the GUI process."""

    def __init__(self, lock_path: str | Path):
        self.lock_path = str(lock_path)
        self._lock = QLockFile(self.lock_path)
        # 0 = never time out a live owner; a lock left by a crashed process is
        # detected as stale through its PID and taken over automatically.
        self._lock.setStaleLockTime(0)

    def acquire(self, timeout_ms: int = 100) -> bool:
        """True if this process may run.

        Returns False only when another live instance holds the lock. Other lock
        errors (e.g. read-only folder) are logged and do not block startup.
        """
        if self._lock.tryLock(timeout_ms):
            return True
        error = self._lock.error()
        if error == QLockFile.LockError.LockFailedError:
            return False
        logging.getLogger("SingleInstance").warning(
            f"Instance lock unavailable ({error}); continuing without single-instance guard"
        )
        return True

    def release(self) -> None:
        if self._lock.isLocked():
            self._lock.unlock()


__all__ = ["LOCK_FILE_NAME", "SingleInstanceGuard"]
