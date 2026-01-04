# gui/main_window.py
"""Main application window - Fixed visibility issues"""

import asyncio
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QStatusBar, QMessageBox, QApplication,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QShortcut, QKeySequence
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from gui.styles import DARK_STYLE, LIGHT_STYLE
from models import ThemeMode
from gui.keyword_manager import KeywordManagerWidget
from gui.settings_dialog import SettingsDialog
from gui.stats_widget import StatsWidget
from gui.favorites_widget import FavoritesWidget
from gui.notification_history import NotificationHistoryWidget
from gui.system_tray import SystemTrayIcon
from gui.log_widget import LogWidget
from gui.listings_widget import ListingsWidget
from settings_manager import SettingsManager
from monitor_engine import MonitorEngine


class MonitorThread(QThread):
    """Thread for running the async monitor loop"""
    
    status_update = pyqtSignal(str)
    new_item = pyqtSignal(object)
    price_change = pyqtSignal(object, str, str)
    error = pyqtSignal(str)
    
    def __init__(self, engine: MonitorEngine):
        super().__init__()
        self.engine = engine
        self.loop = None
        self._stop_requested = False
    
    def run(self):
        # Windows requires ProactorEventLoop for Playwright subprocess handling
        import sys
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        self.engine.on_status_update = lambda s: self.status_update.emit(s)
        self.engine.on_new_item = lambda i: self.new_item.emit(i)
        self.engine.on_price_change = lambda i, o, n: self.price_change.emit(i, o, n)
        self.engine.on_error = lambda e: self.error.emit(e)
        
        try:
            self.loop.run_until_complete(self.engine.start())
        except Exception as e:
            if not self._stop_requested:  # Only report errors if not intentionally stopped
                import traceback
                error_msg = f"{str(e)}\n{traceback.format_exc()}"
                print(f"MonitorThread error: {error_msg}")
                self.error.emit(str(e))
        finally:
            # Clean up pending tasks
            try:
                pending = asyncio.all_tasks(self.loop)
                for task in pending:
                    task.cancel()
                # Allow cancelled tasks to complete
                if pending:
                    self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            try:
                self.loop.close()
            except Exception:
                pass
    
    def stop(self):
        self._stop_requested = True
        self.engine.running = False  # Signal engine to stop
        
        if self.loop and self.loop.is_running():
            # Schedule async stop and wait for it
            future = asyncio.run_coroutine_threadsafe(self.engine.stop(), self.loop)
            try:
                future.result(timeout=5.0)  # Wait max 5 seconds for stop
            except Exception:
                pass
            # Now stop the loop
            self.loop.call_soon_threadsafe(self.loop.stop)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.settings_manager = SettingsManager()
        self.engine = MonitorEngine(self.settings_manager)
        self.monitor_thread = None
        
        self.setup_ui()
        self.setup_tray()
        self.setup_shortcuts()
        
        if self.settings_manager.settings.start_minimized:
            self.hide()
            self.tray_icon.show()
        
        if self.settings_manager.settings.auto_start_monitoring:
            QTimer.singleShot(1000, self.start_monitoring)
    
    def setup_ui(self):
        self.setWindowTitle("🥕 중고거래 알리미")
        self.setMinimumSize(950, 700)
        self.resize(1050, 750)
        
        # Apply stylesheet
        # Apply stylesheet
        self.apply_theme()
        
        central = QWidget()
        central.setStyleSheet("background-color: #1e1e2e;")
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = self.create_header()
        layout.addWidget(header)
        
        # Content area
        content = QWidget()
        content.setStyleSheet("background-color: #1e1e2e;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(0)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        self.keyword_widget = KeywordManagerWidget(self.settings_manager)
        self.tabs.addTab(self.keyword_widget, "🔍 키워드")
        
        self.listings_widget = ListingsWidget(self.engine)
        self.tabs.addTab(self.listings_widget, "📋 전체 매물")
        
        self.stats_widget = StatsWidget(self.engine)
        self.tabs.addTab(self.stats_widget, "📊 통계")
        
        self.favorites_widget = FavoritesWidget(self.engine)
        self.tabs.addTab(self.favorites_widget, "⭐ 즐겨찾기")
        
        self.history_widget = NotificationHistoryWidget(self.engine)
        self.tabs.addTab(self.history_widget, "📢 알림 내역")
        
        self.log_widget = LogWidget()
        self.log_widget.setup_logging()
        self.tabs.addTab(self.log_widget, "📋 로그")
        
        content_layout.addWidget(self.tabs)
        layout.addWidget(content)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("준비됨")
    
    def create_header(self) -> QWidget:
        """Create the header with gradient background, logo, title, and enhanced controls"""
        from gui.components import PulsingDot
        
        header = QFrame()
        header.setObjectName("header")
        header.setStyleSheet("""
            QFrame#header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #181825, stop:0.5 #1e1e2e, stop:1 #181825);
                border-bottom: 1px solid rgba(137, 180, 250, 0.3);
            }
        """)
        header.setFixedHeight(80)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(16)
        
        # Logo with subtle glow effect
        logo = QLabel("🥕")
        logo.setStyleSheet("""
            font-size: 36pt; 
            background: transparent;
            padding: 4px;
        """)
        layout.addWidget(logo)
        
        # Title section
        title_widget = QWidget()
        title_widget.setStyleSheet("background: transparent;")
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)
        
        title = QLabel("중고거래 알리미")
        title.setStyleSheet("""
            font-size: 20pt; 
            font-weight: bold; 
            color: #cdd6f4; 
            background: transparent;
        """)
        title_layout.addWidget(title)
        
        subtitle = QLabel("🥕 당근마켓  ·  ⚡ 번개장터  ·  🛒 중고나라")
        subtitle.setStyleSheet("""
            font-size: 10pt; 
            color: #6c7086; 
            background: transparent;
        """)
        title_layout.addWidget(subtitle)
        
        layout.addWidget(title_widget)
        layout.addStretch()
        
        # Last search time indicator
        self.last_search_label = QLabel("마지막 검색: -")
        self.last_search_label.setStyleSheet("""
            color: #6c7086; 
            font-size: 9pt; 
            background: transparent;
            padding: 4px 8px;
        """)
        layout.addWidget(self.last_search_label)
        
        # Status indicator with glass effect
        self.status_frame = QFrame()
        self.status_frame.setObjectName("statusIndicator")
        self.status_frame.setStyleSheet("""
            QFrame#statusIndicator {
                background-color: rgba(49, 50, 68, 0.8);
                border: 1px solid rgba(69, 71, 90, 0.5);
                border-radius: 18px;
            }
        """)
        status_layout = QHBoxLayout(self.status_frame)
        status_layout.setContentsMargins(14, 6, 14, 6)
        status_layout.setSpacing(8)
        
        # Use PulsingDot component
        self.status_dot = PulsingDot("#6c7086")
        status_layout.addWidget(self.status_dot)
        
        self.status_text = QLabel("대기 중")
        self.status_text.setStyleSheet("""
            color: #a6adc8; 
            font-size: 10pt; 
            background: transparent;
        """)
        status_layout.addWidget(self.status_text)
        
        layout.addWidget(self.status_frame)
        
        # Start button with gradient
        self.start_btn = QPushButton("▶️ 시작")
        self.start_btn.setObjectName("success")
        self.start_btn.setMinimumWidth(110)
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setToolTip("모니터링 시작/중지 (Ctrl+S)")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #a6e3a1, stop:1 #94e2d5);
                color: #1e1e2e;
                border: none;
                padding: 10px 24px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #94e2d5, stop:1 #89dceb);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #89dceb, stop:1 #74c7ec);
            }
        """)
        self.start_btn.clicked.connect(self.toggle_monitoring)
        layout.addWidget(self.start_btn)
        
        # Settings button with glass effect
        settings_btn = QPushButton("⚙️ 설정")
        settings_btn.setMinimumHeight(40)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setToolTip("알림, 테마, 스케줄 설정 (Ctrl+,)")
        settings_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #45475a, stop:1 #313244);
                color: #cdd6f4;
                border: 1px solid rgba(69, 71, 90, 0.5);
                padding: 10px 20px;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #585b70, stop:1 #45475a);
                border: 1px solid rgba(137, 180, 250, 0.4);
            }
        """)
        settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(settings_btn)
        
        return header
    
    def setup_tray(self):
        self.tray_icon = SystemTrayIcon(self)
        self.tray_icon.show_window_requested.connect(self.show_window)
        self.tray_icon.start_monitoring_requested.connect(self.start_monitoring)
        self.tray_icon.stop_monitoring_requested.connect(self.stop_monitoring)
        self.tray_icon.quit_requested.connect(self.quit_app)
        self.tray_icon.show()
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts for common actions"""
        # Ctrl+S: Toggle monitoring
        shortcut_toggle = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut_toggle.activated.connect(self.toggle_monitoring)
        
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
    
    def show_shortcuts_help(self):
        """Show keyboard shortcuts help dialog"""
        help_text = """
<b>⌨️ 키보드 단축키</b><br><br>
<table>
<tr><td><b>Ctrl+S</b></td><td>모니터링 시작/중지</td></tr>
<tr><td><b>Ctrl+,</b></td><td>설정 열기</td></tr>
<tr><td><b>Ctrl+Q</b></td><td>프로그램 종료</td></tr>
<tr><td><b>Ctrl+1~6</b></td><td>탭 전환</td></tr>
<tr><td><b>F1</b></td><td>단축키 도움말</td></tr>
<tr><td><b>F5</b></td><td>현재 탭 새로고침</td></tr>
<tr><td><b>Enter</b></td><td>매물 링크 열기 (목록에서)</td></tr>
<tr><td><b>F</b></td><td>즐겨찾기 추가 (목록에서)</td></tr>
</table>
        """
        QMessageBox.information(self, "단축키 도움말", help_text)
    
    def refresh_current_tab(self):
        """Refresh data in current tab"""
        current = self.tabs.currentWidget()
        if hasattr(current, 'refresh_listings'):
            current.refresh_listings()
        elif hasattr(current, 'refresh_stats'):
            current.refresh_stats()
        elif hasattr(current, 'refresh_list'):
            current.refresh_list()
        elif hasattr(current, 'refresh'):
            current.refresh()
        self.status_bar.showMessage("새로고침 완료")
    
    def toggle_monitoring(self):
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        if self.monitor_thread and self.monitor_thread.isRunning():
            return
        
        # Check if there are keywords
        if not self.settings_manager.settings.keywords:
            QMessageBox.warning(
                self, "알림",
                "모니터링할 키워드가 없습니다.\n키워드를 먼저 추가해주세요."
            )
            return
        
        self.engine = MonitorEngine(self.settings_manager)
        self.stats_widget.set_engine(self.engine)
        self.listings_widget.set_engine(self.engine)
        
        self.monitor_thread = MonitorThread(self.engine)
        self.monitor_thread.status_update.connect(self.on_status_update)
        self.monitor_thread.new_item.connect(self.on_new_item)
        self.monitor_thread.price_change.connect(self.on_price_change)
        self.monitor_thread.error.connect(self.on_error)
        self.monitor_thread.start()
        
        self.update_ui_state(True)
    
    def stop_monitoring(self):
        if self.monitor_thread:
            self.monitor_thread.stop()
            self.monitor_thread.wait(5000)
            self.monitor_thread = None
        
        self.update_ui_state(False)
    
    def update_ui_state(self, is_running: bool):
        if is_running:
            self.start_btn.setText("⏹️ 중지")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #f38ba8, stop:1 #eba0ac);
                    color: #1e1e2e;
                    border: none;
                    padding: 10px 24px;
                    border-radius: 10px;
                    font-weight: bold;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #eba0ac, stop:1 #f5c2e7);
                }
            """)
            # Update status indicator
            self.status_dot.set_color("#a6e3a1")
            self.status_dot.start_pulsing()
            self.status_text.setText("모니터링 중")
            self.status_text.setStyleSheet("""
                color: #a6e3a1; 
                font-size: 10pt; 
                font-weight: bold; 
                background: transparent;
            """)
        else:
            self.start_btn.setText("▶️ 시작")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #a6e3a1, stop:1 #94e2d5);
                    color: #1e1e2e;
                    border: none;
                    padding: 10px 24px;
                    border-radius: 10px;
                    font-weight: bold;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #94e2d5, stop:1 #89dceb);
                }
            """)
            # Reset status indicator
            self.status_dot.stop_pulsing()
            self.status_dot.set_color("#6c7086")
            self.status_text.setText("대기 중")
            self.status_text.setStyleSheet("""
                color: #a6adc8; 
                font-size: 10pt; 
                background: transparent;
            """)
        
        self.tray_icon.set_monitoring_state(is_running)
    
    def on_status_update(self, status: str):
        self.status_bar.showMessage(status)
        # Update header status based on activity
        if "검색 중" in status or "스크래핑" in status:
            self.status_text.setText("검색 중...")
            self.status_dot.set_color("#f9e2af")
        elif "초기화" in status:
            self.status_text.setText("초기화 중...")
            self.status_dot.set_color("#89b4fa")
        elif "다음 검색까지" in status:
            self.status_text.setText("모니터링 중")
            self.status_dot.set_color("#a6e3a1")
            # Update last search time
            from datetime import datetime
            self.last_search_label.setText(f"마지막 검색: {datetime.now().strftime('%H:%M:%S')}")
    
    def on_new_item(self, item):
        # Skip notifications during initial crawl (is_first_run handled in engine)
        # Only show toast notifications for new items after first cycle
        if hasattr(self.engine, 'is_first_run') and self.engine.is_first_run:
            return
        
        self.tray_icon.show_notification(
            f"🆕 새 상품 - {item.platform}",
            f"{item.title}\n{item.price}"
        )
        self.stats_widget.refresh_stats()
        self.listings_widget.refresh_listings()
    
    def on_price_change(self, item, old_price: str, new_price: str):
        self.tray_icon.show_notification(
            "💰 가격 변동",
            f"{item.title}\n{old_price} → {new_price}"
        )
        self.stats_widget.refresh_stats()
        self.listings_widget.refresh_listings()
    
    def on_error(self, error: str):
        self.status_bar.showMessage(f"⚠️ 오류: {error}")
        self.status_text.setText("오류 발생")
        self.status_dot.setStyleSheet("color: #f38ba8; font-size: 10pt; background: transparent;")
    
    def open_settings(self):
        dialog = SettingsDialog(self.settings_manager, self)
        if dialog.exec():
            self.settings_manager.save_settings()
            
            # Apply theme
            self.apply_theme()
            
            # Update keywords
            self.keyword_widget.refresh_list()
            
            # Restart if running
            if self.monitor_thread and self.monitor_thread.isRunning():
                self.stop_monitoring()
                self.start_monitoring()

    def apply_theme(self):
        """Apply current theme with system detection"""
        mode = self.settings_manager.settings.theme_mode
        
        # Detect system theme for ThemeMode.SYSTEM
        if mode == ThemeMode.SYSTEM:
            is_dark = self._detect_system_dark_mode()
        else:
            is_dark = mode == ThemeMode.DARK
        
        style = DARK_STYLE if is_dark else LIGHT_STYLE
        self.setStyleSheet(style)
        
        # Update specific elements
        header_bg = "#181825" if is_dark else "#ffffff"
        header_border = "#313244" if is_dark else "#d1d1d6"
        
        header = self.findChild(QFrame, "header")
        if header:
             header.setStyleSheet(f"""
                QFrame#header {{
                    background-color: {header_bg};
                    border-bottom: 1px solid {header_border};
                }}
             """)
        
        central = self.centralWidget()
        if central:
             central.setStyleSheet(f"background-color: {'#1e1e2e' if is_dark else '#f2f2f7'};")
             
        # Optional: Update StatsWidget if method exists
        if hasattr(self, 'stats_widget') and hasattr(self.stats_widget, 'update_theme'):
            self.stats_widget.update_theme(is_dark)
    
    def _detect_system_dark_mode(self) -> bool:
        """Detect Windows system dark mode setting"""
        try:
            import sys
            if sys.platform == 'win32':
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                )
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return value == 0  # 0 = dark mode, 1 = light mode
        except Exception:
            pass
        return True  # Default to dark mode
    
    def show_window(self):
        self.show()
        self.activateWindow()
        self.raise_()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
    
    def quit_app(self):
        self.stop_monitoring()
        self.tray_icon.hide()
        QApplication.quit()
    
    def closeEvent(self, event: QCloseEvent):
        if self.settings_manager.settings.minimize_to_tray:
            event.ignore()
            self.hide()
            self.tray_icon.show_notification(
                "중고거래 알리미",
                "시스템 트레이에서 실행 중입니다."
            )
        else:
            self.quit_app()
