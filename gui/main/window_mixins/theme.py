# pyright: reportAttributeAccessIssue=false
"""Fluent theme application (구 Catppuccin QSS 테마 대체)."""

from PySide6.QtWidgets import QWidget

from gui.fluent_theme import apply_theme_mode, is_system_dark_mode


class ThemeMixin(QWidget):
    """설정의 테마 모드를 Fluent 테마에 반영한다."""

    def apply_theme(self):
        """Apply current theme mode (dark/light/system)."""
        apply_theme_mode(self.settings_manager.settings.theme_mode)

    def _detect_system_dark_mode(self) -> bool:
        """Windows 시스템 다크모드 여부 (네이티브 보정용 폴백 경로)."""
        return is_system_dark_mode()


__all__ = ["ThemeMixin"]
