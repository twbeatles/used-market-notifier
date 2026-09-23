"""패키징된 실행 파일의 --smoke 검사.

GUI를 띄우지 않고 핵심 모듈 import만 확인합니다. 업데이트 교체 직후
헬퍼가 이 검사에 실패하면 이전 exe로 롤백합니다.
"""

from __future__ import annotations

import importlib
import sys

from version import __version__

SMOKE_MODULES: tuple[str, ...] = (
    "version",
    "models",
    "settings_manager",
    "db",
    "monitor_engine",
    "notifiers",
    "backup_manager",
    "updater",
    "updater.manifest",
    "updater.installer",
    "updater.service",
)


def _emit(line: str) -> None:
    stream = sys.stdout
    if stream is None:
        return
    print(line, file=stream)


def run_smoke_check() -> int:
    failed: list[str] = []
    for name in SMOKE_MODULES:
        try:
            importlib.import_module(name)
        except Exception as exc:
            failed.append(f"{name}: {exc}")
    if failed:
        _emit("Used Market Notifier smoke check FAILED")
        for item in failed:
            _emit(f"  - {item}")
        return 1
    _emit(f"Used Market Notifier v{__version__} smoke check OK")
    return 0
