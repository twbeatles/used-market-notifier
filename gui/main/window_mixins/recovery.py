# pyright: reportAttributeAccessIssue=false
"""Settings-recovery notice shown once at startup (InfoBar)."""

from PySide6.QtWidgets import QWidget
from qfluentwidgets import InfoBar, InfoBarPosition


class RecoveryMixin(QWidget):
    """Informs the user when settings were repaired from backup/defaults."""

    def _show_settings_recovery_notice(self):
        state = getattr(self.settings_manager, "load_recovery_state", {}) or {}
        self._show_secret_decrypt_notice(state)
        if not state or not (state.get("broken_settings_path") or state.get("recovered_from_backup") or state.get("used_default")):
            return

        lines = ["설정 파일을 정상적으로 읽지 못해 복구 절차를 진행했습니다."]
        broken_path = state.get("broken_settings_path")
        recovered_backup = state.get("recovered_backup_path")
        error_text = state.get("error")

        if broken_path:
            lines.append(f"손상 파일: {broken_path}")
        if recovered_backup:
            lines.append(f"복구에 사용한 백업: {recovered_backup}")
        if state.get("used_default"):
            lines.append("유효한 백업을 찾지 못해 기본 설정으로 시작했습니다.")
        if error_text:
            lines.append(f"원인: {error_text}")

        InfoBar.warning(
            "설정 복구 안내",
            " ".join(lines),
            parent=self.window(),
            position=InfoBarPosition.TOP,
            duration=-1,
        )


    def _show_secret_decrypt_notice(self, state: dict) -> None:
        failed = state.get("secret_decrypt_failed") if isinstance(state, dict) else None
        if not failed:
            return
        InfoBar.warning(
            "알림 설정 재입력 필요",
            "저장된 알림 토큰/웹훅을 이 Windows 계정에서 복호화하지 못해 비워 두었습니다 "
            "(다른 PC·계정의 설정 또는 백업일 수 있습니다). "
            f"설정에서 다시 입력해주세요: {', '.join(str(f) for f in failed)}",
            parent=self.window(),
            position=InfoBarPosition.TOP,
            duration=-1,
        )


__all__ = ["RecoveryMixin"]
