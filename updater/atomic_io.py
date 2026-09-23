"""원자적 JSON 쓰기. 업데이트 결과 파일이 중간에 잘리지 않게 합니다."""

from __future__ import annotations

import json
import os
from typing import Any


def write_json_atomic(path: str, data: Any, *, indent: int = 2) -> None:
    """임시 파일에 쓴 뒤 replace로 교체합니다."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    tmp_path = f"{path}.tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=indent)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise
