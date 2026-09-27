# gui/__init__.py
"""GUI package (lazy exports keep Qt-free imports working anywhere)."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .fluent_theme import apply_theme_mode, setup_app_theme, sync_system_theme
    from .keyword_manager import KeywordManagerWidget
    from .main_window import MainWindow
    from .qt_binding import QtBindingReport, inspect_gui_qt_bindings
    from .settings_dialog import SettingsDialog
    from .stats_widget import StatsWidget
    from .system_tray import SystemTrayIcon

__all__ = [
    'KeywordManagerWidget',
    'MainWindow',
    'QtBindingReport',
    'SettingsDialog',
    'StatsWidget',
    'SystemTrayIcon',
    'apply_theme_mode',
    'inspect_gui_qt_bindings',
    'setup_app_theme',
    'sync_system_theme',
]

_LAZY = {
    'MainWindow': '.main_window',
    'KeywordManagerWidget': '.keyword_manager',
    'SettingsDialog': '.settings_dialog',
    'StatsWidget': '.stats_widget',
    'SystemTrayIcon': '.system_tray',
}


def __getattr__(name: str):
    if name in _LAZY:
        import importlib

        module = importlib.import_module(_LAZY[name], __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    if name in ('QtBindingReport', 'inspect_gui_qt_bindings'):
        from . import qt_binding as _qb

        value = getattr(_qb, name)
        globals()[name] = value
        return value
    if name in ('setup_app_theme', 'apply_theme_mode', 'sync_system_theme'):
        from . import fluent_theme as _ft

        value = getattr(_ft, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
