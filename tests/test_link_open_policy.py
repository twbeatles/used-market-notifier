import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QTableWidgetItem, QMessageBox

from gui.link_utils import open_external_url
from gui.listings_widget import ListingsWidget
from models import AppSettings


class _SettingsWrapper:
    def __init__(self, confirm_link_open: bool = True):
        self.settings = AppSettings(confirm_link_open=confirm_link_open)


class _Engine:
    def __init__(self, confirm_link_open: bool = True):
        self.settings = _SettingsWrapper(confirm_link_open)


class TestLinkOpenPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_confirmation_can_cancel_open(self):
        with (
            patch("gui.link_utils.QMessageBox.question", return_value=QMessageBox.StandardButton.No) as question,
            patch("gui.link_utils.QDesktopServices.openUrl", return_value=True) as open_url,
        ):
            opened = open_external_url(None, _Engine(confirm_link_open=True), "https://example.com/item")

        self.assertFalse(opened)
        question.assert_called_once()
        open_url.assert_not_called()

    def test_non_http_schemes_are_blocked(self):
        for url in ("javascript:alert(1)", "file:///C:/Windows/win.ini", ""):
            with (
                patch("gui.link_utils.QMessageBox.warning") as warning,
                patch("gui.link_utils.QDesktopServices.openUrl", return_value=True) as open_url,
            ):
                opened = open_external_url(None, _Engine(confirm_link_open=False), url)

            self.assertFalse(opened)
            open_url.assert_not_called()
            if url:
                warning.assert_called_once()
            else:
                warning.assert_not_called()

    def test_listings_widget_uses_shared_confirmation_policy(self):
        widget = ListingsWidget(engine=_Engine(confirm_link_open=True))
        try:
            widget.refresh_timer.stop()
            widget.search_timer.stop()
            widget.table.setRowCount(1)
            title_item = QTableWidgetItem("테스트 상품")
            title_item.setData(Qt.ItemDataRole.UserRole, {"url": "https://example.com/listing"})
            widget.table.setItem(0, 0, title_item)

            with (
                patch("gui.link_utils.QMessageBox.question", return_value=QMessageBox.StandardButton.No),
                patch("gui.link_utils.QDesktopServices.openUrl", return_value=True) as open_url,
            ):
                widget.on_row_double_click(0, 0)

            open_url.assert_not_called()
        finally:
            widget.close()


if __name__ == "__main__":
    unittest.main()
