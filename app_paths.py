"""Application data root.

Settings, the database, logs, backups and debug output use relative paths.
They are resolved against the application folder (next to the frozen exe, or
the repository root for source runs), never against the launch directory, so a
shortcut/terminal/Task Scheduler start uses the same data. This matches
``updater.constants.app_storage_root()``.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def ensure_app_root_cwd() -> Path:
    """Switch the working directory to the application folder (best effort)."""
    root = app_root()
    try:
        os.chdir(root)
    except OSError as exc:
        logging.getLogger("AppPaths").warning(f"Could not change working directory to {root}: {exc}")
    return root


__all__ = ["app_root", "ensure_app_root_cwd"]
