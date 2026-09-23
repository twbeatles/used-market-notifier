"""업데이터 헬퍼 프로세스: 부모 종료를 기다린 뒤 스테이징된 exe로 교체합니다."""

from __future__ import annotations

import os
import subprocess
import time

from updater.installer import apply_staged_update, write_update_result
from updater.process import is_process_running


def handle_apply_update(args) -> int:
    target = args.update_target
    staged = args.update_staged
    backup = args.update_backup
    parent_pid = args.update_parent_pid
    expected_sha256 = args.update_expected_sha256
    expected_size = args.update_expected_size
    result_file = args.update_result_file

    if parent_pid and parent_pid > 0:
        for _ in range(150):
            if not is_process_running(parent_pid):
                break
            time.sleep(0.1)
        if is_process_running(parent_pid):
            error_message = f"부모 프로세스 종료 대기 시간을 초과했습니다: pid={parent_pid}"
            if result_file:
                write_update_result(result_file, {"status": "failed", "error": error_message})
            return 1

    try:
        apply_staged_update(
            target=target,
            staged=staged,
            backup=backup,
            expected_sha256=expected_sha256,
            expected_size=expected_size,
        )
        if result_file:
            write_update_result(result_file, {"status": "applied", "target": target})
        if target and os.path.exists(target):
            subprocess.Popen([target], close_fds=True)
        return 0
    except Exception as exc:
        if result_file:
            write_update_result(result_file, {"status": "failed", "error": str(exc)})
        return 1
