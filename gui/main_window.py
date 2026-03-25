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
from backup_manager import BackupManager
from db import DatabaseManager


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
        # Ensure a Windows-compatible event loop policy for background asyncio work.
        import sys
        if sys.platform == 'win32':
            proactor_policy = getattr(asyncio, "WindowsProactorEventLoopPolicy", None)
            if proactor_policy is not None:
                asyncio.set_event_loop_policy(proactor_policy())
        
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
            # Always try to close engine resources (driver/executor/db) before loop shutdown.
            try:
                if self.loop and not self.loop.is_closed():
                    self.loop.run_until_complete(self.engine.close())
            except Exception:
                pass

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
            # Schedule async close and wait for it (ensures DB close too)
            future = asyncio.run_coroutine_threadsafe(self.engine.close(), self.loop)
            try:
                future.result(timeout=5.0)  # Wait max 5 seconds for stop
            except Exception:
                # If close is stuck, stop the loop to unwind run_until_complete and trigger finally cleanup.
                self.loop.call_soon_threadsafe(self.loop.stop)


class MaintenanceCleanupThread(QThread):
    """Run one-off maintenance tasks (cleanup) without blocking the UI."""

    completed = pyqtSignal(int)
    failed = pyqtSignal(str)

    def __init__(self, db_path: str, days: int, exclude_favorites: bool, exclude_noted: bool):
        super().__init__()
        self.db_path = db_path
        self.days = days
        self.exclude_favorites = exclude_favorites
        self.exclude_noted = exclude_noted

    def run(self):
        try:
            from db import DatabaseManager
            db = DatabaseManager(self.db_path)
            try:
                deleted = db.cleanup_old_listings(
                    days=self.days,
                    exclude_favorites=self.exclude_favorites,
                    exclude_noted=self.exclude_noted,
                )
            finally:
                try:
                    db.close()
                except Exception:
                    pass
            self.completed.emit(int(deleted))
        except Exception as e:
            self.failed.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, settings_manager: SettingsManager | None = None):
        super().__init__()
        
        self.settings_manager = settings_manager or SettingsManager()
        # Shared DB connection for the UI lifetime (engine must not close this DB).
        self.db = DatabaseManager(self.settings_manager.settings.db_path)
        self.engine = MonitorEngine(self.settings_manager, db=self.db)
        self.monitor_thread = None
        self._is_quitting = False
        self._live_data_dirty = {"stats": False, "listings": False}
        self._ui_refresh_request_count = 0
        
        self.setup_ui()
        self.setup_tray()
        self.setup_shortcuts()
        self._ui_refresh_timer = QTimer(self)
        self._ui_refresh_timer.setSingleShot(True)
        self._ui_refresh_timer.timeout.connect(self._flush_live_data_refresh)
        
        if self.settings_manager.settings.start_minimized:
            self.hide()
            self.tray_icon.show()
        
        # Check for auto backup on startup
        self.backup_manager = BackupManager()
        if self.settings_manager.settings.auto_backup_enabled:
            self._check_auto_backup()

        QTimer.singleShot(0, self._show_settings_recovery_notice)
        # Run startup maintenance (cleanup) once after UI is shown.
        QTimer.singleShot(0, self._run_startup_maintenance)

    def _show_settings_recovery_notice(self):
        state = getattr(self.settings_manager, "load_recovery_state", {}) or {}
        if not state or not (state.get("broken_settings_path") or state.get("recovered_from_backup") or state.get("used_default")):
            return

        lines = ["설정 파일을 정상적으로 읽지 못해 복구 절차를 진행했습니다."]
        broken_path = state.get("broken_settings_path")
        recovered_backup = state.get("recovered_backup_path")
        error_text = state.get("error")

        if broken_path:
            lines.append(f"손상 파일: {broken_path}")
        if recovered_backup:
            lines.append(f"복구에 사용한 백업: {recovered_backup}")
        if state.get("used_default"):
            lines.append("유효한 백업을 찾지 못해 기본 설정으로 시작했습니다.")
        if error_text:
            lines.append(f"원인: {error_text}")

        QMessageBox.information(self, "설정 복구 안내", "\n".join(lines))

    def _run_startup_maintenance(self):
        s = self.settings_manager.settings

        # Auto cleanup: run once on startup (user preference).
        if getattr(s, "auto_cleanup_enabled", False):
            try:
                # Prevent racing with monitoring start/clicks.
                if hasattr(self, "start_btn") and self.start_btn:
                    self.start_btn.setEnabled(False)
                self.status_bar.showMessage("🧹 오래된 매물 정리 중...")
                if hasattr(self, "log_widget") and self.log_widget:
                    self.log_widget.append_log("자동 클린업을 시작합니다...", "INFO")

                self._startup_cleanup_thread = MaintenanceCleanupThread(
                    db_path=s.db_path,
                    days=s.cleanup_days,
                    exclude_favorites=s.cleanup_exclude_favorites,
                    exclude_noted=s.cleanup_exclude_noted,
                )
                self._startup_cleanup_thread.completed.connect(self._on_startup_cleanup_done)
                self._startup_cleanup_thread.failed.connect(self._on_startup_cleanup_failed)
                self._startup_cleanup_thread.start()
                return
            except Exception as e:
                self._on_startup_cleanup_failed(str(e))

        # No cleanup, proceed with auto-start if enabled.
        if s.auto_start_monitoring:
            QTimer.singleShot(1000, self.start_monitoring)

    def _on_startup_cleanup_done(self, deleted_count: int):
        msg = f"🧹 클린업 완료: {deleted_count:,}개 삭제"
        self.status_bar.showMessage(msg)
        if hasattr(self, "log_widget") and self.log_widget:
            self.log_widget.append_log(msg, "INFO")

        # Existing engine connection may have cached stats.
        try:
            if hasattr(self, "engine") and self.engine and hasattr(self.engine, "db"):
                self.engine.db._invalidate_cache()
        except Exception:
            pass

        try:
            if hasattr(self, "stats_widget") and self.stats_widget:
                self.stats_widget.refresh_stats(force=True)
            if hasattr(self, "listings_widget") and self.listings_widget:
                self.listings_widget.refresh_listings(force=True)
            self._live_data_dirty = {"stats": False, "listings": False}
        except Exception:
            pass

        if hasattr(self, "start_btn") and self.start_btn:
            self.start_btn.setEnabled(True)

        if self.settings_manager.settings.auto_start_monitoring:
            QTimer.singleShot(500, self.start_monitoring)

    def _on_startup_cleanup_failed(self, error: str):
        msg = f"⚠️ 자동 클린업 실패: {error}"
        self.status_bar.showMessage(msg)
        if hasattr(self, "log_widget") and self.log_widget:
            self.log_widget.append_log(msg, "WARNING")
        if hasattr(self, "start_btn") and self.start_btn:
            self.start_btn.setEnabled(True)

        if self.settings_manager.settings.auto_start_monitoring:
            QTimer.singleShot(500, self.start_monitoring)
    
    def _check_auto_backup(self):
        """Check and create auto backup if needed"""
        try:
            backup_path = self.backup_manager.auto_backup_if_needed(
                max_age_days=self.settings_manager.settings.auto_backup_interval_days,
                db_path=self.settings_manager.settings.db_path
            )
            if backup_path:
                self.backup_manager.cleanup_old_backups(
                    keep_count=self.settings_manager.settings.backup_keep_count
                )
                print(f"Auto backup created: {backup_path}")
        except Exception as e:
            print(f"Auto backup failed: {e}")
    
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
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
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

    def _mark_live_data_dirty(self, reason: str = ""):
        self._live_data_dirty["stats"] = True
        self._live_data_dirty["listings"] = True
        self._ui_refresh_request_count += 1
        if self._ui_refresh_request_count % 20 == 0 and hasattr(self, "log_widget") and self.log_widget:
            self.log_widget.append_log(
                f"[perf] UI refresh requests={self._ui_refresh_request_count}, reason={reason or 'event'}",
                "INFO",
            )
        if not self._ui_refresh_timer.isActive():
            self._ui_refresh_timer.start(400)

    def _flush_live_data_refresh(self, force: bool = False):
        if not hasattr(self, "tabs") or not self.tabs:
            return
        current = self.tabs.currentIndex()

        if self._live_data_dirty.get("listings") and (force or current == 1):
            try:
                self.listings_widget.refresh_listings(force=True)
                self._live_data_dirty["listings"] = False
            except Exception:
                pass

        if self._live_data_dirty.get("stats") and (force or current == 2):
            try:
                self.stats_widget.refresh_stats(force=True)
                self._live_data_dirty["stats"] = False
            except Exception:
                pass

    def _on_tab_changed(self, index: int):
        self._flush_live_data_refresh(force=False)
    
    def refresh_current_tab(self):
        """Refresh data in current tab"""
        current = self.tabs.currentWidget()
        if current is None:
            self.status_bar.showMessage("새로고침 완료")
            return
        refresh_listings = getattr(current, "refresh_listings", None)
        refresh_stats = getattr(current, "refresh_stats", None)
        refresh_list = getattr(current, "refresh_list", None)
        refresh = getattr(current, "refresh", None)

        if callable(refresh_listings):
            refresh_listings(force=True)
        elif callable(refresh_stats):
            refresh_stats(force=True)
        elif callable(refresh_list):
            refresh_list()
        elif callable(refresh):
            refresh()
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
        
        self.engine = MonitorEngine(self.settings_manager, db=self.db)
        self.stats_widget.set_engine(self.engine)
        self.listings_widget.set_engine(self.engine)
        if hasattr(self, "favorites_widget") and self.favorites_widget:
            self.favorites_widget.set_engine(self.engine)
        if hasattr(self, "history_widget") and self.history_widget:
            self.history_widget.set_engine(self.engine)
        
        self.monitor_thread = MonitorThread(self.engine)
        self.monitor_thread.status_update.connect(self.on_status_update)
        self.monitor_thread.new_item.connect(self.on_new_item)
        self.monitor_thread.price_change.connect(self.on_price_change)
        self.monitor_thread.error.connect(self.on_error)
        # Handle thread termination to reset UI
        self.monitor_thread.finished.connect(self.on_monitor_finished)
        self.monitor_thread.start()
        
        self.update_ui_state(True)
    
    def on_monitor_finished(self):
        """Called when monitor thread finishes (unexpectedly or normally)"""
        self.update_ui_state(False)
        if self.monitor_thread and not self.monitor_thread._stop_requested:
            # Thread ended unexpectedly
            self.on_status_update("모니터링이 종료되었습니다. 다시 시작하려면 버튼을 눌러주세요.")
    
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
        # Skip NOTIFICATIONS during initial crawl, but still update UI
        skip_notification = hasattr(self.engine, 'is_first_run') and self.engine.is_first_run
        
        if not skip_notification:
            self.tray_icon.show_notification(
                f"🆕 새 상품 - {item.platform}",
                f"{item.title}\n{item.price}"
            )
        
        self._mark_live_data_dirty(reason="new_item")
    
    def on_price_change(self, item, old_price: str, new_price: str):
        if hasattr(self.engine, 'is_first_run') and self.engine.is_first_run:
            self._mark_live_data_dirty(reason="price_change")
            return
        self.tray_icon.show_notification(
            "💰 가격 변동",
            f"{item.title}\n{old_price} → {new_price}"
        )
        self._mark_live_data_dirty(reason="price_change")
    
    def on_error(self, error: str):
        self.status_bar.showMessage(f"⚠️ 오류: {error}")
        self.status_text.setText("오류 발생")
        self.status_dot.setStyleSheet("color: #f38ba8; font-size: 10pt; background: transparent;")
    
    def open_settings(self):
        dialog = SettingsDialog(self.settings_manager, self)
        if dialog.exec():
            # SettingsDialog.save_settings() already persists via SettingsManager.save().
            self.settings_manager.save()
            
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
        update_theme = getattr(getattr(self, "stats_widget", None), "update_theme", None)
        if callable(update_theme):
            update_theme(is_dark)
    
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
        self._is_quitting = True
        self.stop_monitoring()
        try:
            if hasattr(self, "db") and self.db:
                self.db.close()
        except Exception:
            pass
        self.tray_icon.hide()
        QApplication.quit()
    
    def closeEvent(self, a0: QCloseEvent | None):
        if a0 is None:
            return
        if self.settings_manager.settings.minimize_to_tray:
            a0.ignore()
            self.hide()
            self.tray_icon.show_notification(
                "중고거래 알리미",
                "시스템 트레이에서 실행 중입니다."
            )
        else:
            self.quit_app()
