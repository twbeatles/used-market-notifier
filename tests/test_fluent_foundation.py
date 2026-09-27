"""Fluent foundation regression tests (KTrain Strict Profile).

Pure-logic checks run everywhere. Window construction runs only when the
resolved ``qfluentwidgets`` is the PySide6 binding (otherwise skipped: the
system interpreter may intentionally carry the PyQt6 variant).
"""

import os
import re
import tempfile
import unittest
from pathlib import Path

from gui.design_tokens import (
    PAGE_MARGIN,
    TABLE_ROW_MIN_HEIGHT,
    WINDOW_DEFAULT_HEIGHT,
    WINDOW_DEFAULT_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WORK_PAGE_MARGIN,
)
from gui.qt_binding import (
    QtBindingReport,
    binding_from_source,
    fluent_binding_accepted,
    inspect_gui_qt_bindings,
    is_pyside6_binding,
)


def _resolved_fluent_is_pyside6() -> bool:
    try:
        report = inspect_gui_qt_bindings(check_conflicting_dists=False)
    except (ImportError, OSError):
        return False
    return bool(report.ok and report.fluent_binding == "PySide6")


class BindingDetectionTest(unittest.TestCase):
    def test_binding_from_source(self):
        self.assertEqual(binding_from_source("from PyQt6.QtCore import Qt"), "PyQt6")
        self.assertEqual(binding_from_source("import PySide6.QtWidgets"), "PySide6")
        self.assertEqual(binding_from_source("from PySide6.QtCore import Signal"), "PySide6")
        self.assertEqual(binding_from_source("x = 1"), "unknown")

    def test_is_pyside6_binding(self):
        self.assertTrue(is_pyside6_binding("PySide6"))
        self.assertFalse(is_pyside6_binding("PyQt6"))
        self.assertFalse(is_pyside6_binding("unknown"))

    def test_inspect_reports_dataclass_shape(self):
        report = inspect_gui_qt_bindings(check_conflicting_dists=False)
        self.assertIsInstance(report.ok, bool)
        self.assertIsInstance(report.errors, tuple)


def _binding_report(
    *,
    ok: bool,
    fluent_binding: str | None,
    errors: tuple[str, ...] = (),
) -> QtBindingReport:
    return QtBindingReport(
        ok=ok,
        skipped=fluent_binding is None and ok,
        errors=errors,
        fluent_path=None,
        fluent_binding=fluent_binding,
        frameless_path=None,
        frameless_binding=None,
        conflicting_dists=(),
    )


class FluentBindingAcceptedTest(unittest.TestCase):
    """frozen 번들에서는 fluent_binding=None이어도 진입 허용 (회귀).

    PYZ 아카이브 안에서는 소스 판독이 불가해 skipped 리포트가 돌아오는데,
    구 가드(``or not is_pyside6_binding(binding or "")``)는 이를 거부해
    frozen GUI가 항상 무반응 종료했다.
    """

    def test_frozen_skipped_report_accepted(self):
        self.assertTrue(
            fluent_binding_accepted(_binding_report(ok=True, fluent_binding=None))
        )

    def test_pyside6_source_report_accepted(self):
        self.assertTrue(
            fluent_binding_accepted(_binding_report(ok=True, fluent_binding="PySide6"))
        )

    def test_failed_report_rejected(self):
        self.assertFalse(
            fluent_binding_accepted(
                _binding_report(
                    ok=False, fluent_binding=None, errors=("missing",)
                )
            )
        )

    def test_pyqt_binding_rejected(self):
        self.assertFalse(
            fluent_binding_accepted(
                _binding_report(ok=True, fluent_binding="PyQt6")
            )
        )


class DesignTokensTest(unittest.TestCase):
    def test_window_profile(self):
        self.assertEqual((WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT), (1100, 800))
        self.assertEqual((WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT), (640, 560))

    def test_layout_density(self):
        self.assertEqual(PAGE_MARGIN, 24)
        self.assertEqual(WORK_PAGE_MARGIN, 16)
        self.assertGreaterEqual(TABLE_ROW_MIN_HEIGHT, 40)


@unittest.skipUnless(_resolved_fluent_is_pyside6(), "requires PySide6 qfluentwidgets binding")
class FluentWindowTest(unittest.TestCase):
    def test_main_window_navigation(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication

        from gui.main_window import MainWindow
        from settings_manager import SettingsManager

        _app = QApplication.instance() or QApplication([])
        tmp = tempfile.mkdtemp(prefix="umn_fluent_test_")
        manager = SettingsManager(settings_path=os.path.join(tmp, "settings.json"))
        manager.settings.db_path = os.path.join(tmp, "test.db")

        window = MainWindow(settings_manager=manager)
        try:
            self.assertEqual(len(window._nav_pages), 7)
            for page in list(window._nav_pages) + [window.settings_page, window.update_page]:
                window.switchTo(page)
                self.assertEqual(window.stackedWidget.currentWidget(), page)
            self.assertEqual(len(window.settings_page._tab_keys), 9)
            window.update_ui_state(True)
            window.update_ui_state(False)
            window.publish_status("test")
        finally:
            window.close()

    def test_settings_persist_core(self):
        from gui.pages.settings_page import SettingsPage  # noqa: F401  (import surface)
        from gui.settings_panels.mixins.persistence import SettingsPersistenceMixin

        self.assertTrue(callable(SettingsPersistenceMixin.persist_settings_form))


class PyprojectGuiExtraTest(unittest.TestCase):
    def test_gui_extra_declares_fluent_dependency(self):
        try:
            import tomllib  # pyright: ignore[reportMissingImports]
        except ImportError:
            self.skipTest("tomllib requires Python 3.11+")
        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        self.assertTrue(pyproject.is_file())
        with pyproject.open("rb") as fh:
            data = tomllib.load(fh)
        gui_extra = data["project"]["optional-dependencies"]["gui"]
        blob = "\n".join(gui_extra)
        self.assertIn("PySide6-Fluent-Widgets", blob)
        self.assertIn("PySide6", blob)
        self.assertIn("darkdetect", blob)


def _requirement_names(lines: list[str]) -> list[str]:
    """요구사항 줄에서 패키지 이름만 추출한다 (주석/빈 줄/옵션 제외)."""
    names: list[str] = []
    for raw in lines:
        line = raw.split("#", 1)[0].strip().strip("\"'")
        if not line or line.startswith("-"):
            continue
        names.append(re.split(r"[=<>!;\s\[]", line, maxsplit=1)[0].strip())
    return names


def _pyproject_gui_extra_lines(root: Path) -> list[str]:
    """tomllib 없이 [project.optional-dependencies] gui 블록을 추출한다."""
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r"gui\s*=\s*\[(.*?)\]", text, re.DOTALL)
    if match is None:
        return []
    return [line for line in match.group(1).splitlines() if line.strip()]


class GuiDependencyHygieneTest(unittest.TestCase):
    """PyQt-Fluent 오염 재발 방지: 선언 파일에 PyQt 계열이 없어야 한다.

    빌드 환경에 PyQt6-Fluent-Widgets가 설치되면 PyInstaller가 PyQt
    바인딩 트리를 번들에 넣어 ``No module named 'PyQt6'`` frozen 실패와
    모달 대기(무반응 실행)를 유발한다. 선언이 깨끗하면
    ``pip install -r requirements.txt`` / ``pip install -e ".[gui]"`` 로는
    오염이 재발하지 않는다.
    """

    def test_requirements_txt_has_no_pyqt(self):
        root = Path(__file__).resolve().parent.parent
        names = _requirement_names(
            (root / "requirements.txt").read_text(encoding="utf-8").splitlines()
        )
        self.assertTrue(names)
        offenders = [n for n in names if "pyqt" in n.lower()]
        self.assertEqual(offenders, [])

    def test_pyproject_gui_extra_has_no_pyqt(self):
        root = Path(__file__).resolve().parent.parent
        names = _requirement_names(_pyproject_gui_extra_lines(root))
        self.assertIn("PySide6-Fluent-Widgets", names)
        offenders = [n for n in names if "pyqt" in n.lower()]
        self.assertEqual(offenders, [])


_EMOJI_RX = re.compile(
    "[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u23E9-\u23FF\u25B6\u25C0\u2139\uFE0F]"
)
_CHROME_TRIGGERS = (
    "QLabel", "setText", "setTitle", "QPushButton", "addTab",
    "QGroupBox", "setWindowTitle", "showMessage", "QMessageBox",
    "setPlaceholderText", "setToolTip", "setTabText", "QCheckBox",
    "addAction",
)
# Intentional keeps: data-viz bar, log console document style, semantic
# update-status colors (legacy dialog path).
_QSS_ALLOW_SUBSTRINGS = (
    "bar.setStyleSheet",
    "_UPDATE_COLORS",
    'label.setStyleSheet(f"color: {color};")',
    "self.log_text.setStyleSheet",
)
_CONVERTED_FILES = (
    "gui/pages/monitor_page.py",
    "gui/pages/settings_page.py",
    "gui/pages/update_page.py",
    "gui/main/window_mixins/ui_setup.py",
    "gui/main/window_mixins/monitoring.py",
    "gui/widgets/keyword/widget.py",
    "gui/widgets/keyword/cards.py",
    "gui/widgets/keyword/dialog.py",
    "gui/widgets/listings/mixins/ui.py",
    "gui/widgets/favorites/mixins/ui.py",
    "gui/widgets/favorites/edit_dialog.py",
    "gui/widgets/stats/mixins/ui.py",
    "gui/compare/mixins/ui.py",
    "gui/export/mixins/ui.py",
    "gui/note_dialog.py",
    "gui/message_dialog.py",
    "gui/log_widget.py",
    "gui/notification_history.py",
    "gui/charts.py",
    "gui/loading_spinner.py",
    "gui/settings_panels/dialog.py",
    "gui/settings_panels/editors.py",
    "gui/settings_panels/mixins/general.py",
    "gui/settings_panels/mixins/notifications.py",
    "gui/settings_panels/mixins/schedule.py",
    "gui/settings_panels/mixins/seller.py",
    "gui/settings_panels/mixins/maintenance.py",
    "gui/settings_panels/mixins/auto_tagging.py",
    "gui/settings_panels/mixins/message_templates.py",
)


class FluentChromeContractTest(unittest.TestCase):
    """Converted files carry no page-level QSS and no emoji UI chrome."""

    def test_no_page_qss_in_converted_files(self):
        root = Path(__file__).resolve().parent.parent
        offenders = []
        for rel in _CONVERTED_FILES:
            for lineno, line in enumerate(
                (root / rel).read_text(encoding="utf-8").splitlines(), 1
            ):
                if "setStyleSheet" in line and not any(
                    allow in line for allow in _QSS_ALLOW_SUBSTRINGS
                ):
                    offenders.append(f"{rel}:{lineno}:{line.strip()[:80]}")
        self.assertEqual(offenders, [])

    def test_no_emoji_in_converted_chrome(self):
        root = Path(__file__).resolve().parent.parent
        offenders = []
        for rel in _CONVERTED_FILES:
            for lineno, line in enumerate(
                (root / rel).read_text(encoding="utf-8").splitlines(), 1
            ):
                if any(t in line for t in _CHROME_TRIGGERS) and _EMOJI_RX.search(line):
                    offenders.append(f"{rel}:{lineno}:{line.strip()[:80]}")
        self.assertEqual(offenders, [])


@unittest.skipUnless(_resolved_fluent_is_pyside6(), "requires PySide6 qfluentwidgets binding")
class EmptyStateWidgetTest(unittest.TestCase):
    def test_fluent_icon_renders_without_emoji(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        from qfluentwidgets import FluentIcon as FIF

        from gui.loading_spinner import EmptyStateWidget

        _app = QApplication.instance() or QApplication([])
        widget = EmptyStateWidget(icon=FIF.HEART, title="T", message="M")
        try:
            from PySide6.QtWidgets import QWidget

            for child in widget.findChildren(QWidget):
                text = getattr(child, "text", lambda: "")()
                if isinstance(text, str) and text:
                    self.assertFalse(_EMOJI_RX.search(text))
        finally:
            widget.close()

    def test_legacy_string_icon_still_accepted(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication

        from gui.loading_spinner import EmptyStateWidget

        _app = QApplication.instance() or QApplication([])
        widget = EmptyStateWidget(icon="*", title="T", message="M")
        try:
            self.assertIsNotNone(widget)
        finally:
            widget.close()


if __name__ == "__main__":
    unittest.main()
