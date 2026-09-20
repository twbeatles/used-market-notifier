# pyright: reportAttributeAccessIssue=false
"""Theme application with Windows system-theme detection."""

from PyQt6.QtWidgets import QFrame, QWidget

from gui.styles import DARK_STYLE, LIGHT_STYLE
from models import ThemeMode


class ThemeMixin(QWidget):
    """Applies the configured (or system) theme to the window."""

    def apply_theme(self):
        """Apply current theme with system detection"""
        mode = self.settings_manager.settings.theme_mode

        # Detect system theme for ThemeMode.SYSTEM
        if mode == ThemeMode.SYSTEM:
            is_dark = self._detect_system_dark_mode()
        else:
            is_dark = mode == ThemeMode.DARK

        style = DARK_STYLE if is_dark else LIGHT_STYLE
        self.setStyleSheet(style)

        # Update specific elements
        header_bg = "#181825" if is_dark else "#ffffff"
        header_border = "#313244" if is_dark else "#d1d1d6"

        header = self.findChild(QFrame, "header")
        if header:
             header.setStyleSheet(f"""
                QFrame#header {{
                    background-color: {header_bg};
                    border-bottom: 1px solid {header_border};
                }}
             """)

        central = self.centralWidget()
        if central:
             central.setStyleSheet(f"background-color: {'#1e1e2e' if is_dark else '#f2f2f7'};")

        # Optional: Update StatsWidget if method exists
        update_theme = getattr(getattr(self, "stats_widget", None), "update_theme", None)
        if callable(update_theme):
            update_theme(is_dark)

    def _detect_system_dark_mode(self) -> bool:
        """Detect Windows system dark mode setting"""
        try:
            import sys
            if sys.platform == 'win32':
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                )
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return value == 0  # 0 = dark mode, 1 = light mode
        except Exception:
            pass
        return True  # Default to dark mode


__all__ = ["ThemeMixin"]
