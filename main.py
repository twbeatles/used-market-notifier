"""Application entry point for Used Market Notifier."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


def setup_logging():
    """Setup logging configuration with rotation."""
    from logging.handlers import RotatingFileHandler

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        "notifier.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception


def run_cli(settings_manager=None):
    """Run in CLI mode."""
    from monitor_engine import MonitorEngine
    from settings_manager import SettingsManager

    logger = logging.getLogger("CLI")
    logger.info("Starting in CLI mode")

    settings = settings_manager or SettingsManager()
    engine = MonitorEngine(settings)
    engine.on_status_update = lambda status: logger.info(status)
    engine.on_new_item = lambda item: logger.info(f"New item: {item.title}")
    engine.on_error = lambda error: logger.error(error)

    try:
        if sys.platform.startswith("win"):
            selector_policy = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)
            if selector_policy is not None:
                asyncio.set_event_loop_policy(selector_policy())
        asyncio.run(engine.start())
    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        asyncio.run(engine.close())
        logger.info("Goodbye.")


def run_gui(settings_manager=None):
    """Run in GUI mode."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication, QMessageBox

    from gui.main_window import MainWindow
    from settings_manager import SettingsManager

    def exception_hook(exc_type, exc_value, exc_tb):
        import traceback

        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logging.getLogger("Main").error(f"Uncaught exception:\n{error_msg}")
        if exc_type != KeyboardInterrupt:
            try:
                QMessageBox.critical(None, "오류", f"예상하지 못한 오류가 발생했습니다:\n{exc_value}")
            except Exception:
                pass

    sys.excepthook = exception_hook

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setApplicationName("Used Market Notifier")
    app.setOrganizationName("UsedMarketNotifier")
    app.setStyle("Fusion")

    try:
        window = MainWindow(settings_manager=settings_manager or SettingsManager())
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logging.getLogger("Main").error(f"Failed to start GUI: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def _console_print(message: str) -> None:
    stream = sys.stdout
    if stream is None:
        return
    print(message, file=stream)


def run_check_update() -> int:
    """Print whether a signed newer release exists. Network failures exit 1."""
    from updater import UpdateService
    from version import __version__

    service = UpdateService()
    try:
        manifest = service.check_for_update()
    except Exception as exc:
        _console_print(f"업데이트 확인 실패: {exc}")
        return 1
    if manifest is None:
        _console_print(f"이미 최신 버전입니다: v{__version__}")
        return 0
    _console_print(f"새 버전 v{manifest.version} (현재 v{__version__})")
    _console_print(manifest.artifact_url)
    return 0


def main():
    """Main entry point."""
    from version import __version__

    parser = argparse.ArgumentParser(description="Used Market Notifier")
    parser.add_argument("--cli", action="store_true", help="Run without the GUI")
    parser.add_argument("--headless", action="store_true", help="Use hidden browser mode for this session only")
    parser.add_argument("--smoke", action="store_true", help="Import core modules and exit")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"Used Market Notifier v{__version__}",
    )
    parser.add_argument("--check-update", action="store_true", help="Check the signed release manifest and exit")
    parser.add_argument("--apply-update", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--update-target", help=argparse.SUPPRESS)
    parser.add_argument("--update-staged", help=argparse.SUPPRESS)
    parser.add_argument("--update-backup", help=argparse.SUPPRESS)
    parser.add_argument("--update-parent-pid", type=int, default=0, help=argparse.SUPPRESS)
    parser.add_argument("--update-expected-sha256", help=argparse.SUPPRESS)
    parser.add_argument("--update-expected-size", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--update-result-file", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.smoke:
        from updater.smoke import run_smoke_check

        sys.exit(run_smoke_check())

    if args.apply_update:
        from updater.apply import handle_apply_update

        sys.exit(handle_apply_update(args))

    if args.check_update:
        sys.exit(run_check_update())

    setup_logging()

    from settings_manager import SettingsManager

    settings_manager = SettingsManager()
    if args.headless:
        settings_manager.settings.headless_mode = True

    if args.cli:
        run_cli(settings_manager=settings_manager)
    else:
        run_gui(settings_manager=settings_manager)


if __name__ == "__main__":
    main()
