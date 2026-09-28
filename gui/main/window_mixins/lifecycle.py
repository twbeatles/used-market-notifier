# pyright: reportAttributeAccessIssue=false
"""Window lifecycle: show, quit, and close-to-tray behavior."""

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QWidget


class LifecycleMixin(QWidget):
    """Show/quit/close behavior (needs ``db``/``tray_icon`` attributes)."""

    def show_window(self):
        self.show()
        self.activateWindow()
        self.raise_()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)

    def quit_app(self):
        logging.getLogger("Main").info("quit_app called")
        self._is_quitting = True
        # Wait for the engine thread before closing the shared DB it writes to.
        stopped = self.stop_monitoring(wait=True, timeout_ms=60000)
        if stopped:
            try:
                if hasattr(self, "db") and self.db:
                    self.db.close()
            except Exception:
                pass
        else:
            logging.getLogger("Main").warning("Monitor thread still running at quit; leaving DB open")
        self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, a0: QCloseEvent | None):
        if a0 is None:
            return
        if self.settings_manager.settings.minimize_to_tray:
            a0.ignore()
            self.hide()
            self.tray_icon.show_notification(
                "중고거래 알리미",
                "시스템 트레이에서 실행 중입니다."
            )
        else:
            self.quit_app()


__all__ = ["LifecycleMixin"]
