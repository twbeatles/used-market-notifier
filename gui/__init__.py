# gui/__init__.py
from .main_window import MainWindow
from .keyword_manager import KeywordManagerWidget
from .settings_dialog import SettingsDialog
from .stats_widget import StatsWidget
from .system_tray import SystemTrayIcon

__all__ = ['MainWindow', 'KeywordManagerWidget', 'SettingsDialog', 'StatsWidget', 'SystemTrayIcon']
