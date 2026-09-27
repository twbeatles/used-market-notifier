"""GUI 애플리케이션 진입점 (KTrain app.py 구조).

실행 방법 (우선순위):
  1. python main.py            (권장 GUI 진입점)
  2. python -m gui.app
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _fatal_gui_error(message: str) -> None:
    """GUI 시작 실패 메시지. frozen 빌드에서도 QMessageBox 우선."""
    if (
        os.environ.get("USED_NOTIFIER_GUI_SMOKE") == "1"
        or "--smoke" in sys.argv
        or os.environ.get("QT_QPA_PLATFORM") == "offscreen"
    ):
        # 헤드리스 스모크/offscreen에서는 모달을 띄우지 않는다.
        # 모달은 응답할 사용자가 없어 프로세스가 영원히 대기한다.
        print(message, file=sys.stderr)
        raise SystemExit(1)
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox

        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "중고거래 알리미", message)
        app.quit()
    except Exception:  # noqa: BLE001
        print(message, file=sys.stderr)
    raise SystemExit(1)


def _check_gui_dependencies() -> None:
    """GUI 필수 패키지 확인."""
    frozen = bool(getattr(sys, "frozen", False))
    try:
        import PySide6  # noqa: F401
        import qfluentwidgets  # noqa: F401
    except ImportError as exc:
        if frozen:
            extra = ""
            if "PyQt" in str(exc):
                extra = (
                    "\n\nPyQt Fluent 패키지가 번들된 것 같습니다.\n"
                    "pyinstaller used_market_notifier.spec 으로 다시 빌드하세요."
                )
            _fatal_gui_error(
                "GUI 번들 로드에 실패했습니다.\n\n"
                f"{exc}{extra}\n\n"
                "PyInstaller 빌드를 다시 실행하거나 개발 모드로 실행하세요.\n"
                '  pip install -e ".[gui]"'
            )
        missing: list[str] = []
        if "PySide6" in str(exc) or exc.name == "PySide6":
            missing.append("PySide6")
        else:
            missing.append("PySide6-Fluent-Widgets")
        if "PyQt" in str(exc):
            from .qt_binding import format_gui_qt_binding_error, inspect_gui_qt_bindings

            print(format_gui_qt_binding_error(inspect_gui_qt_bindings()), file=sys.stderr)
            raise SystemExit(1)
        packages = " ".join(missing)
        print(
            "GUI 실행에 필요한 패키지가 설치되지 않았습니다.\n"
            f"  누락: {packages}\n\n"
            "설치:\n"
            '  pip install -e ".[gui]"\n'
            "또는:\n"
            "  pip install PySide6 PySide6-Fluent-Widgets darkdetect",
            file=sys.stderr,
        )
        raise SystemExit(1)

    from .qt_binding import format_gui_qt_binding_error, inspect_gui_qt_bindings

    report = inspect_gui_qt_bindings(check_conflicting_dists=not frozen)
    if report.ok:
        return
    message = format_gui_qt_binding_error(report)
    if frozen:
        _fatal_gui_error(message)
    print(message, file=sys.stderr)
    raise SystemExit(1)


def _run_gui_smoke_if_requested() -> bool:
    """헤드리스 CI 스모크. 창을 띄우지 않고 의존성만 확인한다.

    ``USED_NOTIFIER_GUI_SMOKE=1`` 또는 ``--smoke``면 True를 반환하고
    호출측은 즉시 종료해야 한다.
    """
    if os.environ.get("USED_NOTIFIER_GUI_SMOKE") != "1" and "--smoke" not in sys.argv:
        return False
    _check_gui_dependencies()
    marker = os.environ.get("USED_NOTIFIER_GUI_SMOKE_MARKER", "").strip()
    if marker:
        Path(marker).write_text("ok\n", encoding="utf-8")
    print("used-market-notifier-gui smoke: ok", flush=True)
    return True


def configure_high_dpi() -> None:
    """고배율(125/150%)에서 흐림·1px 틀어짐을 줄인다. QApplication 생성 전에 호출."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )


def main(settings_manager=None) -> None:
    """GUI 메인 진입점."""
    if _run_gui_smoke_if_requested():
        return

    _check_gui_dependencies()

    from PySide6.QtWidgets import QApplication

    from settings_manager import SettingsManager

    from .fluent_theme import setup_app_theme
    from .icon import get_app_icon
    from .main_window import MainWindow

    configure_high_dpi()
    app = QApplication(sys.argv)
    app.setApplicationName("Used Market Notifier")
    app.setOrganizationName("UsedMarketNotifier")
    app.setWindowIcon(get_app_icon())

    manager = settings_manager or SettingsManager()
    setup_app_theme(app, manager.settings.theme_mode)

    window = MainWindow(settings_manager=manager)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
