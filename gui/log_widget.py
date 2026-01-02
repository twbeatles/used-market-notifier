# gui/log_widget.py
"""Enhanced real-time log viewer with modern styling"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QLabel, QComboBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat, QFont
import logging


class QTextEditHandler(logging.Handler):
    """Custom logging handler that writes to QPlainTextEdit"""
    
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        
        # Catppuccin Mocha colors for log levels
        self.colors = {
            logging.DEBUG: "#6c7086",    # overlay0
            logging.INFO: "#a6e3a1",     # green
            logging.WARNING: "#f9e2af",  # yellow
            logging.ERROR: "#f38ba8",    # red
            logging.CRITICAL: "#f38ba8", # red
        }
        
        self.level_icons = {
            logging.DEBUG: "🔍",
            logging.INFO: "ℹ️",
            logging.WARNING: "⚠️",
            logging.ERROR: "❌",
            logging.CRITICAL: "💀",
        }
    
    def emit(self, record):
        try:
            msg = self.format(record)
            color = self.colors.get(record.levelno, "#c0caf5")
            icon = self.level_icons.get(record.levelno, "📝")
            
            self.text_edit.appendHtml(
                f'<span style="color: {color};">{icon} {msg}</span>'
            )
            
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.text_edit.setTextCursor(cursor)
            
        except Exception:
            self.handleError(record)


class LogWidget(QWidget):
    """Modern log viewer widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.handler = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📋 실시간 로그")
        title.setObjectName("title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Log level filter
        level_frame = QFrame()
        level_frame.setStyleSheet("""
            QFrame {
                background-color: #313244;
                border-radius: 8px;
                padding: 4px;
            }
        """)
        level_layout = QHBoxLayout(level_frame)
        level_layout.setContentsMargins(8, 4, 8, 4)
        level_layout.setSpacing(8)
        
        level_label = QLabel("레벨:")
        level_label.setStyleSheet("color: #7982a9;")
        level_layout.addWidget(level_label)
        
        self.level_combo = QComboBox()
        self.level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.level_combo.setCurrentText("INFO")
        self.level_combo.setMinimumWidth(100)
        self.level_combo.currentTextChanged.connect(self.change_log_level)
        level_layout.addWidget(self.level_combo)
        
        header_layout.addWidget(level_frame)
        
        clear_btn = QPushButton("🗑️ 지우기")
        clear_btn.setObjectName("secondary")
        clear_btn.clicked.connect(self.clear_logs)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Log text area
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(1000)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("""
            QPlainTextEdit {
                font-family: 'Consolas', 'D2Coding', monospace;
                font-size: 9pt;
                background-color: #1e1e2e;
                border: 2px solid #45475a;
                border-radius: 12px;
                padding: 12px;
                line-height: 1.4;
            }
        """)
        layout.addWidget(self.log_text)
        
        # Footer with stats
        footer = QHBoxLayout()
        
        self.line_count = QLabel("0 줄")
        self.line_count.setStyleSheet("color: #565f89; font-size: 9pt;")
        footer.addWidget(self.line_count)
        
        footer.addStretch()
        
        auto_scroll_hint = QLabel("💡 자동 스크롤 활성화됨")
        auto_scroll_hint.setStyleSheet("color: #565f89; font-size: 9pt;")
        footer.addWidget(auto_scroll_hint)
        
        layout.addLayout(footer)
    
    def setup_logging(self):
        if self.handler:
            return
        
        self.handler = QTextEditHandler(self.log_text)
        self.handler.setFormatter(logging.Formatter(
            '%(asctime)s │ %(name)-15s │ %(message)s',
            datefmt='%H:%M:%S'
        ))
        self.handler.setLevel(logging.INFO)
        
        logging.getLogger().addHandler(self.handler)
        
        # Log initial message
        self.append_log("로그 시스템이 초기화되었습니다.", "INFO")
    
    def change_log_level(self, level_name: str):
        if self.handler:
            level = getattr(logging, level_name, logging.INFO)
            self.handler.setLevel(level)
            self.append_log(f"로그 레벨이 {level_name}(으)로 변경되었습니다.", "INFO")
    
    def clear_logs(self):
        self.log_text.clear()
        self.line_count.setText("0 줄")
        self.append_log("로그가 초기화되었습니다.", "INFO")
    
    def append_log(self, message: str, level: str = "INFO"):
        # Catppuccin Mocha colors
        colors = {
            "DEBUG": "#6c7086",    # overlay0
            "INFO": "#a6e3a1",     # green
            "WARNING": "#f9e2af",  # yellow
            "ERROR": "#f38ba8",    # red
        }
        icons = {
            "DEBUG": "🔍",
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
        }
        
        color = colors.get(level.upper(), "#cdd6f4")
        icon = icons.get(level.upper(), "📝")
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.log_text.appendHtml(
            f'<span style="color: {color};">{icon} {timestamp} │ System │ {message}</span>'
        )
        
        # Update line count
        count = self.log_text.document().blockCount()
        self.line_count.setText(f"{count:,} 줄")
