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


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Used Market Notifier")
    parser.add_argument("--cli", action="store_true", help="Run without the GUI")
    parser.add_argument("--headless", action="store_true", help="Use hidden browser mode for this session only")
    args = parser.parse_args()

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
