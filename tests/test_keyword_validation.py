import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from gui.keyword_manager import KeywordEditDialog
from models import Item, SearchKeyword


class TestKeywordValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_min_price_cannot_exceed_max_price(self):
        dialog = KeywordEditDialog()
        try:
            dialog.keyword_edit.setText("아이폰")
            dialog.min_price_spin.setValue(200_000)
            dialog.max_price_spin.setValue(100_000)

            with patch("gui.widgets.keyword.dialog.QMessageBox.warning") as warning:
                dialog._validate_and_accept()

            warning.assert_called_once()
            self.assertEqual(dialog.result(), 0)
        finally:
            dialog.close()

    def test_unknown_price_still_passes_price_filter(self):
        keyword = SearchKeyword(keyword="아이폰", min_price=100_000, max_price=200_000)
        item = Item(
            platform="joonggonara",
            article_id="unknown-price",
            title="아이폰 가격문의",
            price="가격문의",
            link="https://example.com/item",
            keyword="아이폰",
        )

        self.assertTrue(keyword.matches_price(item))


if __name__ == "__main__":
    unittest.main()
