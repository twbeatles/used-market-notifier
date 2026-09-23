"""자동 업데이트 상수.

개인키는 소스와 바이너리에 넣지 않습니다. GitHub Actions secret
UMN_UPDATE_PRIVATE_KEY_B64 에만 둡니다.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# GitHub raw 매니페스트. 릴리즈 워크플로가 main의 updates/latest.json 을 갱신합니다.
UPDATE_MANIFEST_URL: str = os.environ.get(
    "UMN_UPDATE_MANIFEST_URL",
    "https://raw.githubusercontent.com/twbeatles/used-market-notifier/main/updates/latest.json",
)

# Ed25519 공개키 (Base64, raw 32 bytes)
UPDATE_PUBLIC_KEY_B64_DEFAULT: str = "uKLYYgW7Q6lWCLbChoEUEFdjLxRH9y7+YyGfD7BZX5w="

UPDATE_PUBLIC_KEY_B64: str = os.environ.get(
    "UMN_UPDATE_PUBLIC_KEY_B64",
    UPDATE_PUBLIC_KEY_B64_DEFAULT,
)

UPDATE_RELEASES_URL: str = "https://github.com/twbeatles/used-market-notifier/releases/latest"

UPDATE_MANIFEST_MAX_BYTES: int = 256 * 1024
UPDATE_ARTIFACT_MAX_BYTES: int = 500 * 1024 * 1024
UPDATE_REQUEST_TIMEOUT_SECONDS: float = 20.0
UPDATE_BACKUP_KEEP_COUNT: int = 2
# PyQt/Playwright onefile 기동이 길 수 있어 스모크 대기를 120초로 둡니다.
UPDATE_SMOKE_TIMEOUT_SECONDS: float = 120.0

UPDATE_USER_AGENT: str = "UsedMarketNotifier-Updater"


def app_storage_root() -> Path:
    """설정·스테이징을 둘 디렉터리. 패키징 실행 파일은 exe 옆, 개발 실행은 저장소 루트."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent
