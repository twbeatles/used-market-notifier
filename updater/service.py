"""업데이트 확인, 다운로드, 검증, 설치를 조율합니다."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Callable

from version import __version__
from updater.constants import UPDATE_MANIFEST_URL, UPDATE_PUBLIC_KEY_B64, app_storage_root
from updater.installer import (
    consume_update_result,
    launch_update_helper,
    prepare_staged_update,
    resolve_update_staging_root,
    stream_update_artifact,
    update_result_path,
)
from updater.manifest import (
    NoUpdateAvailableError,
    ReleaseManifest,
    download_release_manifest,
    verify_release_manifest,
)

logger = logging.getLogger("UpdateService")


class UpdateService:
    """원격 매니페스트 확인과 스테이징된 실행 파일 교체를 담당합니다."""

    def __init__(
        self,
        current_version: str = __version__,
        manifest_url: str = UPDATE_MANIFEST_URL,
        public_key: str = UPDATE_PUBLIC_KEY_B64,
        storage_root: str | Path | None = None,
    ):
        self.current_version = current_version
        self.manifest_url = manifest_url
        self.public_key = public_key
        self.storage_root = Path(storage_root or app_storage_root()).resolve()
        self.staging_root = resolve_update_staging_root(storage_root=self.storage_root)

    def check_for_update(self) -> ReleaseManifest | None:
        """새 버전이 있으면 매니페스트를, 없으면 None을 반환합니다."""
        try:
            logger.info("업데이트 확인: %s", self.manifest_url)
            manifest_bytes = download_release_manifest(self.manifest_url)
            manifest = verify_release_manifest(
                manifest_bytes,
                public_key=self.public_key,
                current_version=self.current_version,
            )
            logger.info("새 버전 발견: %s", manifest.version)
            return manifest
        except NoUpdateAvailableError:
            logger.info("이미 최신 버전입니다: %s", self.current_version)
            return None
        except Exception:
            logger.warning("업데이트 확인 실패", exc_info=True)
            raise

    def check_last_result(self) -> dict[str, object] | None:
        return consume_update_result(update_result_path(self.staging_root))

    def download_and_stage(
        self,
        manifest: ReleaseManifest,
        progress_callback: Callable[[int, int], None] | None = None,
        cancel_event: Any = None,
    ) -> Path:
        """릴리즈 바이너리를 받아 해시가 맞는 스테이징 파일 경로를 반환합니다."""
        self.staging_root.mkdir(parents=True, exist_ok=True)

        def progress_chunks():
            total_downloaded = 0
            for chunk in stream_update_artifact(manifest, cancel_event=cancel_event):
                total_downloaded += len(chunk)
                if progress_callback:
                    progress_callback(total_downloaded, manifest.artifact_size)
                yield chunk

        staged_path = prepare_staged_update(
            manifest,
            chunks=progress_chunks(),
            staging_root=self.staging_root,
            cancel_event=cancel_event,
        )
        if staged_path is None or not staged_path.is_file():
            raise RuntimeError("업데이트 파일을 스테이징하지 못했습니다.")
        return staged_path

    def launch_update_and_exit(
        self,
        staged_path: Path,
        manifest: ReleaseManifest,
        before_exit: Callable[[], None] | None = None,
    ) -> None:
        """헬퍼를 띄운 뒤 현재 프로세스를 종료해 exe 교체가 가능하게 합니다."""
        if not getattr(sys, "frozen", False):
            logger.info("개발 환경에서는 교체를 건너뜁니다: %s", staged_path)
            raise RuntimeError(
                f"개발 환경에서는 실행 파일을 교체하지 않습니다. 검증된 파일: {staged_path}"
            )

        target = Path(sys.executable).resolve()
        backup = target.parent / f"{target.name}.v{self.current_version}.bak"
        result_file = update_result_path(self.staging_root)
        launch_update_helper(
            target=target,
            staged=staged_path,
            backup=backup,
            parent_pid=os.getpid(),
            expected_sha256=manifest.artifact_sha256,
            expected_size=manifest.artifact_size,
            result_file=result_file,
        )
        logger.info("업데이트 헬퍼를 시작했습니다.")
        if before_exit is not None:
            try:
                before_exit()
            except Exception:
                logger.exception("업데이트 종료 정리에 실패했습니다.")
        os._exit(0)
