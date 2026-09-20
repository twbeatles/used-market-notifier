# pyright: reportAttributeAccessIssue=false
"""Keyboard shortcuts and small navigation helpers."""

from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QMessageBox, QWidget


class ShortcutsMixin(QWidget):
    """Registers global shortcuts and tab-navigation helpers."""

    def setup_shortcuts(self):
        """Setup keyboard shortcuts for common actions"""
        # Ctrl+S: Toggle monitoring
        shortcut_toggle = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut_toggle.activated.connect(self.toggle_monitoring)

        # Ctrl+N: Add new keyword (switch to Keyword tab)
        shortcut_new_keyword = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut_new_keyword.activated.connect(self.open_add_keyword)

        # Ctrl+F: Focus search in listings (switch to Listings tab)
        shortcut_find = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_find.activated.connect(self.focus_listings_search)

        # Ctrl+, : Open settings (common convention)
        shortcut_settings = QShortcut(QKeySequence("Ctrl+,"), self)
        shortcut_settings.activated.connect(self.open_settings)

        # Ctrl+Q: Quit application
        shortcut_quit = QShortcut(QKeySequence("Ctrl+Q"), self)
        shortcut_quit.activated.connect(self.quit_app)

        # Ctrl+1/2/3/4/5/6: Switch tabs
        for i in range(6):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i+1}"), self)
            shortcut.activated.connect(lambda idx=i: self.tabs.setCurrentIndex(idx))

        # F1: Show shortcuts help
        shortcut_help = QShortcut(QKeySequence("F1"), self)
        shortcut_help.activated.connect(self.show_shortcuts_help)

        # F5: Refresh current tab
        shortcut_refresh = QShortcut(QKeySequence("F5"), self)
        shortcut_refresh.activated.connect(self.refresh_current_tab)

    def open_add_keyword(self):
        try:
            # Keyword tab is index 0
            self.tabs.setCurrentIndex(0)
            if hasattr(self, "keyword_widget") and self.keyword_widget:
                self.keyword_widget.add_keyword()
        except Exception:
            pass

    def focus_listings_search(self):
        try:
            # Listings tab is index 1
            self.tabs.setCurrentIndex(1)
            if hasattr(self, "listings_widget") and self.listings_widget:
                if hasattr(self.listings_widget, "_focus_search"):
                    self.listings_widget._focus_search()
                elif hasattr(self.listings_widget, "search_input"):
                    self.listings_widget.search_input.setFocus()
                    self.listings_widget.search_input.selectAll()
        except Exception:
            pass

    def show_shortcuts_help(self):
        """Show keyboard shortcuts help dialog"""
        help_text = """
<b>⌨️ 키보드 단축키</b><br><br>
<table>
<tr><td><b>Ctrl+S</b></td><td>모니터링 시작/중지</td></tr>
<tr><td><b>Ctrl+,</b></td><td>설정 열기</td></tr>
<tr><td><b>Ctrl+N</b></td><td>새 키워드 추가</td></tr>
<tr><td><b>Ctrl+F</b></td><td>제목 검색 (전체 매물)</td></tr>
<tr><td><b>Ctrl+Q</b></td><td>프로그램 종료</td></tr>
<tr><td><b>Ctrl+1~6</b></td><td>탭 전환</td></tr>
<tr><td><b>F1</b></td><td>단축키 도움말</td></tr>
<tr><td><b>F5</b></td><td>현재 탭 새로고침</td></tr>
<tr><td><b>Enter</b></td><td>매물 링크 열기 (목록에서)</td></tr>
<tr><td><b>F</b></td><td>즐겨찾기 추가 (목록에서)</td></tr>
</table>
        """
        QMessageBox.information(self, "단축키 도움말", help_text)


__all__ = ["ShortcutsMixin"]
