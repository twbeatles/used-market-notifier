"""Light theme stylesheet."""

LIGHT_STYLE = """
/* ===== Global Styles ===== */
* {
    font-family: "Segoe UI", "Malgun Gothic", -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ===== Main Windows ===== */
QMainWindow, QDialog {
    background-color: #f5f5f7;
    color: #1d1d1f;
}

QWidget {
    color: #1d1d1f;
    font-size: 10pt;
}

/* ===== Header ===== */
QFrame#header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
        stop:0 #ffffff, stop:1 #f5f5f7);
    border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

/* ===== Tab Widget ===== */
QTabWidget::pane {
    border: 1px solid rgba(0, 0, 0, 0.1);
    background-color: #ffffff;
    border-radius: 12px;
}

QTabBar::tab {
    background-color: transparent;
    color: #86868b;
    padding: 12px 24px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #007aff, stop:1 #0056b3);
    color: #ffffff;
    font-weight: bold;
}

QTabBar::tab:hover:!selected {
    background-color: rgba(0, 0, 0, 0.05);
    color: #1d1d1f;
}

/* ===== Buttons ===== */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #007aff, stop:1 #0056b3);
    color: #ffffff;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: bold;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #0077ed, stop:1 #004bb5);
}

QPushButton:disabled {
    background-color: #d1d1d6;
    color: #86868b;
}

QPushButton#success {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #34c759, stop:1 #248a3d);
}

QPushButton#danger {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #ff3b30, stop:1 #d70015);
}

QPushButton#secondary {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #e5e5ea, stop:1 #d1d1d6);
    color: #1d1d1f;
}

/* ===== Input Fields ===== */
QLineEdit, QSpinBox, QTextEdit, QComboBox {
    background-color: #ffffff;
    color: #1d1d1f;
    border: 1px solid #d1d1d6;
    border-radius: 8px;
    padding: 10px 12px;
}

QLineEdit:focus, QSpinBox:focus, QTextEdit:focus, QComboBox:focus {
    border: 2px solid #007aff;
}

/* ===== Tables ===== */
QTableWidget, QTableView, QListWidget {
    background-color: #ffffff;
    alternate-background-color: #f5f5f7;
    gridline-color: #e5e5ea;
    border: 1px solid #d1d1d6;
    border-radius: 12px;
    color: #1d1d1f;
}

QHeaderView::section {
    background-color: #f5f5f7;
    color: #86868b;
    border: none;
    border-bottom: 1px solid #d1d1d6;
    padding: 12px 8px;
    font-weight: bold;
}

QTableWidget::item:selected, QListWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
        stop:0 #007aff, stop:1 #0056b3);
    color: #ffffff;
}

/* ===== Scrollbars ===== */
QScrollBar:vertical {
    background-color: transparent;
    width: 10px;
}

QScrollBar::handle:vertical {
    background-color: rgba(0, 0, 0, 0.2);
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: rgba(0, 0, 0, 0.4);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    height: 0px;
    background: transparent;
}

/* ===== Card Styles ===== */
QFrame#card {
    background-color: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 16px;
}

QFrame#card:hover {
    border: 1px solid rgba(0, 122, 255, 0.3);
}

QFrame#statCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
        stop:0 #ffffff, stop:1 #f5f5f7);
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 16px;
    padding: 16px;
}

/* ===== Status Bar ===== */
QStatusBar {
    background-color: #f5f5f7;
    color: #86868b;
    border-top: 1px solid #d1d1d6;
}

/* ===== Group Box ===== */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #d1d1d6;
    border-radius: 12px;
    margin-top: 16px;
    padding: 16px;
    padding-top: 24px;
}

QGroupBox::title {
    color: #007aff;
    font-weight: bold;
}

/* ===== Checkbox ===== */
QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
        stop:0 #007aff, stop:1 #0056b3);
    border: 2px solid #007aff;
    border-radius: 6px;
}

QCheckBox::indicator:unchecked {
    border: 2px solid #d1d1d6;
    border-radius: 6px;
    background-color: #ffffff;
}
"""
