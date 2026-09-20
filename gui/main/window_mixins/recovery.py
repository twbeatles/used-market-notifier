# pyright: reportAttributeAccessIssue=false
"""Settings-recovery notice shown once at startup."""

from PyQt6.QtWidgets import QMessageBox, QWidget


class RecoveryMixin(QWidget):
    """Informs the user when settings were repaired from backup/defaults."""

    def _show_settings_recovery_notice(self):
        state = getattr(self.settings_manager, "load_recovery_state", {}) or {}
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

        QMessageBox.information(self, "설정 복구 안내", "\n".join(lines))


__all__ = ["RecoveryMixin"]
