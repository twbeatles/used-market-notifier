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
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("notifier.log", encoding='utf-8')
        ]
    )


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
        engine.close()
        logger.info("Goodbye.")


def run_gui():
    """Run in GUI mode"""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from gui.main_window import MainWindow
    
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("중고거래 알리미")
    app.setOrganizationName("UsedMarketNotifier")
    
    # Set application style
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


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
