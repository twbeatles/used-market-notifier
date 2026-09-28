"""Resolve the MainWindow host of settings panels.

Settings mixins are shared by the legacy ``SettingsDialog`` (parent = MainWindow)
and the Fluent ``SettingsPage``. The latter is re-parented into the navigation
stack by ``addSubInterface``, so ``parent()`` is a stacked widget, not the window.
Always resolve the host through this module instead of ``self.parent()``.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("SettingsHost")


def _is_host(candidate: Any) -> bool:
    return candidate is not None and callable(getattr(candidate, "stop_monitoring", None))


def resolve_settings_host(widget: Any) -> Any | None:
    """Return the MainWindow-like host (has ``stop_monitoring``) or None."""
    window_fn = getattr(widget, "window", None)
    window = window_fn() if callable(window_fn) else None
    if window is not widget and _is_host(window):
        return window
    parent_fn = getattr(widget, "parent", None)
    parent = parent_fn() if callable(parent_fn) else None
    if _is_host(parent):
        return parent
    return None


def resolve_host_db(host: Any) -> Any | None:
    """Shared UI database of the host (falls back to the current engine's DB)."""
    if host is None:
        return None
    db = getattr(host, "db", None)
    if db is not None:
        return db
    return getattr(getattr(host, "engine", None), "db", None)


def host_monitoring_active(host: Any) -> bool:
    if host is None:
        return False
    is_active = getattr(host, "is_monitoring_active", None)
    if callable(is_active):
        return bool(is_active())
    thread = getattr(host, "monitor_thread", None)
    is_running = getattr(thread, "isRunning", None)
    return bool(callable(is_running) and is_running())


def stop_host_monitoring(host: Any, timeout_ms: int = 60000) -> bool:
    """Stop monitoring and wait for the engine thread. True when nothing is running anymore."""
    if host is None:
        return False
    stop = getattr(host, "stop_monitoring", None)
    if not callable(stop):
        return False
    try:
        stop(wait=True, timeout_ms=timeout_ms)
    except TypeError:
        stop()  # legacy host without the wait parameter
    except Exception as exc:
        logger.warning(f"stop_monitoring failed: {exc}")
        return False
    return not host_monitoring_active(host)


__all__ = [
    "host_monitoring_active",
    "resolve_host_db",
    "resolve_settings_host",
    "stop_host_monitoring",
]
