# pyright: reportAttributeAccessIssue=false
"""System-tray wiring for the main window."""

from PyQt6.QtWidgets import QWidget

from gui.system_tray import SystemTrayIcon


class TrayMixin(QWidget):
    """Connects SystemTrayIcon signals to main-window slots."""

    def setup_tray(self):
        self.tray_icon = SystemTrayIcon(self)
        self.tray_icon.show_window_requested.connect(self.show_window)
        self.tray_icon.start_monitoring_requested.connect(self.start_monitoring)
        self.tray_icon.stop_monitoring_requested.connect(self.stop_monitoring)
        self.tray_icon.quit_requested.connect(self.quit_app)
        self.tray_icon.show()


__all__ = ["TrayMixin"]
