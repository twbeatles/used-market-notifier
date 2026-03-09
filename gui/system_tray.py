# gui/system_tray.py
"""System tray icon with context menu"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PyQt6.QtCore import pyqtSignal, QObject


def create_tray_icon() -> QIcon:
    """Create a simple tray icon programmatically"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Draw carrot emoji style icon
    painter.setBrush(QColor("#FF6F00"))
    painter.setPen(QColor("#FF6F00"))
    painter.drawEllipse(12, 20, 40, 40)
    
    # Green top
    painter.setBrush(QColor("#4CAF50"))
    painter.setPen(QColor("#4CAF50"))
    painter.drawRect(26, 5, 12, 20)
    
    painter.end()
    
    return QIcon(pixmap)


class SystemTrayIcon(QSystemTrayIcon):
    """System tray icon with quick actions"""
    
    show_window_requested = pyqtSignal()
    start_monitoring_requested = pyqtSignal()
    stop_monitoring_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(create_tray_icon())
        self.setToolTip("중고거래 알리미")
        
        self.is_monitoring = False
        self.setup_menu()
        
        # Double-click to show window
        self.activated.connect(self.on_activated)
    
    def setup_menu(self):
        """Setup context menu"""
        menu = QMenu()
        
        # Status indicator
        self.status_action = menu.addAction("⏹️ 대기 중")
        if self.status_action is not None:
            self.status_action.setEnabled(False)
        
        menu.addSeparator()
        
        # Show window
        show_action = menu.addAction("📱 창 열기")
        if show_action is not None:
            show_action.triggered.connect(self.show_window_requested.emit)
        
        menu.addSeparator()
        
        # Toggle monitoring
        self.toggle_action = menu.addAction("▶️ 모니터링 시작")
        if self.toggle_action is not None:
            self.toggle_action.triggered.connect(self.toggle_monitoring)
        
        menu.addSeparator()
        
        # Quit
        quit_action = menu.addAction("🚪 종료")
        if quit_action is not None:
            quit_action.triggered.connect(self.quit_requested.emit)
        
        self.setContextMenu(menu)
    
    def on_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_requested.emit()
    
    def toggle_monitoring(self):
        """Toggle monitoring state"""
        if self.is_monitoring:
            self.stop_monitoring_requested.emit()
        else:
            self.start_monitoring_requested.emit()
    
    def set_monitoring_state(self, is_running: bool):
        """Update UI based on monitoring state"""
        self.is_monitoring = is_running
        
        if is_running:
            if self.status_action is not None:
                self.status_action.setText("🟢 모니터링 중")
            if self.toggle_action is not None:
                self.toggle_action.setText("⏹️ 모니터링 중지")
            self.setToolTip("중고거래 알리미 - 모니터링 중")
        else:
            if self.status_action is not None:
                self.status_action.setText("⏹️ 대기 중")
            if self.toggle_action is not None:
                self.toggle_action.setText("▶️ 모니터링 시작")
            self.setToolTip("중고거래 알리미 - 대기 중")
    
    def show_notification(self, title: str, message: str, icon=None):
        """Show a balloon notification"""
        if icon is None:
            icon = QSystemTrayIcon.MessageIcon.Information
        
        self.showMessage(title, message, icon, 5000)
