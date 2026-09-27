"""OS 테마 자동 연동 + 네이티브 Qt 위젯 보정 (KTrain theme.py 복제)."""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets import Theme, isDarkTheme, setTheme

from models import ThemeMode

_POLL_MS = 3000


def setup_app_theme(app: QApplication, mode: ThemeMode = ThemeMode.SYSTEM) -> None:
    """QApplication 생성 직후, 윈도우 생성 전에 호출."""
    apply_theme_mode(mode)
    _install_theme_watcher(app)


def apply_theme_mode(mode: ThemeMode) -> None:
    """설정의 테마 모드를 Fluent 테마에 반영."""
    if mode == ThemeMode.DARK:
        setTheme(Theme.DARK)
        return
    if mode == ThemeMode.LIGHT:
        setTheme(Theme.LIGHT)
        return
    setTheme(Theme.AUTO)
    sync_system_theme()


def is_system_dark_mode() -> bool:
    """OS 다크모드 여부 (darkdetect 우선, Windows 레지스트리 폴백)."""
    try:
        import darkdetect

        return darkdetect.theme() == "Dark"
    except Exception:  # noqa: BLE001, S110
        pass
    try:
        import sys

        if sys.platform == "win32":
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return value == 0  # 0 = dark mode, 1 = light mode
    except Exception:  # noqa: BLE001, S110
        pass
    return True  # Default to dark mode


def sync_system_theme() -> None:
    """OS 다크/라이트 설정을 qfluentwidgets에 반영."""
    try:
        import darkdetect

        system = darkdetect.theme()
    except Exception:  # noqa: BLE001
        return

    if system == "Dark":
        setTheme(Theme.DARK)
    elif system == "Light":
        setTheme(Theme.LIGHT)


def _install_theme_watcher(app: QApplication) -> None:
    hints = QGuiApplication.styleHints()
    if hasattr(hints, "colorSchemeChanged"):
        hints.colorSchemeChanged.connect(lambda _scheme: QTimer.singleShot(0, sync_system_theme))

    timer = QTimer(app)
    timer.timeout.connect(sync_system_theme)
    timer.start(_POLL_MS)


def configure_fluent_window(window: QWidget) -> None:
    """FluentWindow 계열 Mica/배경 깨짐 완화 (기본 OFF)."""
    set_mica = getattr(window, "setMicaEffectEnabled", None)
    if callable(set_mica):
        try:
            set_mica(False)
        except Exception:  # noqa: BLE001, S110
            pass


def apply_native_widget_style(root: QWidget) -> None:
    """QCheckBox·QListWidget 등 기본 Qt 위젯 다크모드 가독성 보정."""
    if isDarkTheme():
        root.setStyleSheet(
            root.styleSheet()
            + """
            QCheckBox, QLabel, QSpinBox, QDoubleSpinBox, QListWidget, QListWidget::item {
                color: #E8E8E8;
                background-color: transparent;
            }
            QSpinBox, QDoubleSpinBox, QListWidget {
                background-color: #2B2B2B;
                border: 1px solid #3E3E3E;
                border-radius: 4px;
                padding: 2px 4px;
            }
            QListWidget::item:selected {
                background-color: #3A3A3A;
            }
            QTableWidget {
                color: #E8E8E8;
                background-color: #2B2B2B;
                gridline-color: #3E3E3E;
            }
            QHeaderView::section {
                color: #E8E8E8;
                background-color: #333333;
            }
            """
        )
    else:
        # 라이트모드: 과도한 커스텀 제거 (플랫폼 기본 사용)
        pass


def platform_accent_color(platform: str) -> str:
    """도메인 상태 표현용 플랫폼 색상 (Fluent accent 대체 아님)."""
    return {
        "danggeun": "#FF6F00",
        "bunjang": "#F50057",
        "joonggonara": "#2E7D32",
    }.get(platform, "#0078D4")


__all__ = [
    "apply_native_widget_style",
    "apply_theme_mode",
    "configure_fluent_window",
    "is_system_dark_mode",
    "platform_accent_color",
    "setup_app_theme",
    "sync_system_theme",
]
