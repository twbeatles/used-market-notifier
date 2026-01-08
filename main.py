# main.py
"""
중고거래 알리미 (Used Market Notifier)

당근마켓, 번개장터, 중고나라에서 키워드를 모니터링하고 
새로운 상품이 등록되면 알림을 보내는 프로그램입니다.

Usage:
    python main.py          # GUI 모드
    python main.py --cli    # CLI 모드 (백그라운드)
"""

import sys
import os
import argparse
import asyncio
import logging

# Setup path
sys.path.insert(0, os.path.dirname(__file__))


def setup_logging():
    """Setup logging configuration with rotation"""
    from logging.handlers import RotatingFileHandler
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File handler with rotation (5MB max, keep 3 backups)
    file_handler = RotatingFileHandler(
        "notifier.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler]
    )
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.error("Ignored exception/Crash caused by:", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception


def run_cli():
    """Run in CLI mode (original behavior)"""
    from settings_manager import SettingsManager
    from monitor_engine import MonitorEngine
    
    logger = logging.getLogger("CLI")
    logger.info("Starting in CLI mode...")
    
    settings = SettingsManager()
    engine = MonitorEngine(settings)
    
    # Set callbacks
    engine.on_status_update = lambda s: logger.info(s)
    engine.on_new_item = lambda i: logger.info(f"New item: {i.title}")
    engine.on_error = lambda e: logger.error(e)
    
    try:
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(engine.start())
    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        asyncio.run(engine.close())
        logger.info("Goodbye.")


def run_gui():
    """Run in GUI mode"""
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtCore import Qt
    from gui.main_window import MainWindow
    
    # Global exception handler to prevent silent crashes
    def exception_hook(exc_type, exc_value, exc_tb):
        import traceback
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logging.getLogger("Main").error(f"Uncaught exception:\n{error_msg}")
        # Don't crash, just log
        if exc_type != KeyboardInterrupt:
            try:
                QMessageBox.critical(None, "오류", f"예상치 못한 오류가 발생했습니다:\n{exc_value}")
            except Exception:
                pass
    
    sys.excepthook = exception_hook
    
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("중고거래 알리미")
    app.setOrganizationName("UsedMarketNotifier")
    
    # Set application style
    app.setStyle("Fusion")
    
    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logging.getLogger("Main").error(f"Failed to start GUI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="중고거래 알리미 - 중고 마켓 모니터링 프로그램"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="CLI 모드로 실행 (GUI 없이 백그라운드 실행)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="브라우저 창 숨김 모드"
    )
    
    args = parser.parse_args()
    
    setup_logging()
    
    if args.cli:
        run_cli()
    else:
        run_gui()


if __name__ == "__main__":
    main()
