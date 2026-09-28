"""Atomic JSON writes for settings files."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def write_json_atomic(path: Path | str, data: object) -> None:
    """Write JSON so that an interrupted save leaves either the old or the new file intact."""
    target = Path(path)
    directory = str(target.parent) if str(target.parent) else "."
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, target)
    except BaseException:
        try:
            os.remove(tmp_name)
        except OSError:
            pass
        raise


__all__ = ["write_json_atomic"]
