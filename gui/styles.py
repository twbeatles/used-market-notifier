# gui/styles.py
"""
Modern stylesheet definitions for the application.
Theme: Enhanced Catppuccin Mocha with Glassmorphism and animations.
"""

# ============================================================
# Catppuccin Mocha Color Palette
# ============================================================
CATPPUCCIN_MOCHA = {
    # Base colors
    'base': '#1e1e2e',
    'mantle': '#181825',
    'crust': '#11111b',
    'surface0': '#313244',
    'surface1': '#45475a',
    'surface2': '#585b70',
    'overlay0': '#6c7086',
    'overlay1': '#7f849c',
    'overlay2': '#9399b2',
    # Text colors
    'text': '#cdd6f4',
    'subtext0': '#a6adc8',
    'subtext1': '#bac2de',
    # Accent colors
    'blue': '#89b4fa',
    'lavender': '#b4befe',
    'sapphire': '#74c7ec',
    'sky': '#89dceb',
    'teal': '#94e2d5',
    'green': '#a6e3a1',
    'yellow': '#f9e2af',
    'peach': '#fab387',
    'maroon': '#eba0ac',
    'red': '#f38ba8',
    'mauve': '#cba6f7',
    'pink': '#f5c2e7',
    'flamingo': '#f2cdcd',
    'rosewater': '#f5e0dc',
}

# ============================================================
# Platform styling info
# ============================================================
PLATFORM_INFO = {
    'danggeun': {
        'color': '#FF6F00', 
        'gradient': 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF6F00, stop:1 #FF9800)',
        'emoji': '🥕', 
        'name': '당근마켓'
    },
    'bunjang': {
        'color': '#7B68EE', 
        'gradient': 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7B68EE, stop:1 #9575CD)',
        'emoji': '⚡', 
        'name': '번개장터'
    },
    'joonggonara': {
        'color': '#00C853', 
        'gradient': 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00C853, stop:1 #69F0AE)',
        'emoji': '🛒', 
        'name': '중고나라'
    }
}

# ============================================================
# DARK THEME - Enhanced Catppuccin Mocha with Glassmorphism
# ============================================================
DARK_STYLE = """
/* ===== Global Styles ===== */
* {
    font-family: "Segoe UI", "Malgun Gothic", -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ===== Main Windows ===== */
QMainWindow {
    background-color: #1e1e2e;
    color: #cdd6f4;
}

QDialog {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border-radius: 12px;
}

/* ===== Base Widget Defaults ===== */
QWidget {
    color: #cdd6f4;
    font-size: 10pt;
}

/* ===== Header with Gradient ===== */
QFrame#header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
        stop:0 #181825, stop:0.5 #1e1e2e, stop:1 #181825);
    border-bottom: 1px solid rgba(137, 180, 250, 0.3);
}

/* ===== Glass Card Effect ===== */
QFrame#glassCard {
    background-color: rgba(49, 50, 68, 0.7);
    border: 1px solid rgba(137, 180, 250, 0.2);
    border-radius: 16px;
}

QFrame#glassCard:hover {
    background-color: rgba(49, 50, 68, 0.85);
    border: 1px solid rgba(137, 180, 250, 0.4);
}

/* ===== Enhanced Tab Widget ===== */
QTabWidget::pane {
    border: 1px solid rgba(69, 71, 90, 0.5);
    background-color: rgba(30, 30, 46, 0.95);
    border-radius: 12px;
    top: -1px;
}

QTabBar::tab {
    background-color: transparent;
    color: #6c7086;
    padding: 12px 24px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-size: 10pt;
    min-width: 80px;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #89b4fa, stop:1 #74c7ec);
    color: #1e1e2e;
    font-weight: bold;
}

QTabBar::tab:hover:!selected {
    background-color: rgba(69, 71, 90, 0.5);
    color: #cdd6f4;
}

QTabBar::tab:first {
    margin-left: 8px;
}

/* ===== Gradient Buttons ===== */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #89b4fa, stop:1 #74c7ec);
    color: #1e1e2e;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 10pt;
    min-height: 20px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #b4befe, stop:1 #89b4fa);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #74c7ec, stop:1 #89dceb);
}

QPushButton:disabled {
    background-color: #45475a;
    color: #6c7086;
}

/* Success Button (Green) */
QPushButton#success {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #45475a, stop:1 #313244);
    color: #cdd6f4;
    border: 1px solid #94e2d5;
}

QPushButton#success:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #585b70, stop:1 #45475a);
    border: 1px solid #89dceb;
}

/* Danger Button (Red) */
QPushButton#danger {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #45475a, stop:1 #313244);
    color: #cdd6f4;
    border: 1px solid #eba0ac;
}

QPushButton#danger:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #585b70, stop:1 #45475a);
    border: 1px solid #f5c2e7;
}

/* Warning Button (Yellow) */
QPushButton#warning {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #45475a, stop:1 #313244);
    color: #cdd6f4;
    border: 1px solid #fab387;
}

/* Secondary Button (Muted) */
QPushButton#secondary {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #45475a, stop:1 #313244);
    color: #cdd6f4;
    border: 1px solid #585b70;
}

QPushButton#secondary:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #585b70, stop:1 #45475a);
    border: 1px solid #6c7086;
}

/* Icon Button (Minimal) */
QPushButton#iconButton {
    background-color: transparent;
    border: none;
    padding: 8px;
    border-radius: 8px;
}

QPushButton#iconButton:hover {
    background-color: rgba(137, 180, 250, 0.2);
}

/* ===== Enhanced Input Fields ===== */
QLineEdit, QSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
    background-color: rgba(49, 50, 68, 0.8);
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 10px 12px;
    color: #cdd6f4;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {
    border: 2px solid #89b4fa;
    background-color: rgba(49, 50, 68, 1);
}

QLineEdit:hover, QSpinBox:hover, QComboBox:hover {
    border: 1px solid #585b70;
}

QComboBox::drop-down {
    border: none;
    padding-right: 12px;
}

QComboBox::down-arrow {
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #89b4fa;
}

QComboBox QAbstractItemView {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 8px;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
    padding: 4px;
}

QComboBox QAbstractItemView::item {
    padding: 8px 12px;
    border-radius: 4px;
}

/* ===== Enhanced Lists & Tables ===== */
QListWidget, QTableWidget, QTreeWidget {
    background-color: rgba(30, 30, 46, 0.95);
    alternate-background-color: rgba(49, 50, 68, 0.6);
    border: 1px solid rgba(69, 71, 90, 0.5);
    border-radius: 12px;
    padding: 8px;
    gridline-color: rgba(69, 71, 90, 0.2);
    outline: none;
}

QListWidget::item, QTableWidget::item {
    padding: 10px 12px;
    border-radius: 6px;
    border-bottom: 1px solid rgba(69, 71, 90, 0.15);
}

QListWidget::item:selected, QTableWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
        stop:0 rgba(137, 180, 250, 0.9), stop:1 rgba(116, 199, 236, 0.9));
    color: #1e1e2e;
    border-radius: 8px;
}

QListWidget::item:hover:!selected, QTableWidget::item:hover:!selected {
    background-color: rgba(137, 180, 250, 0.15);
    border-radius: 6px;
}

QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #313244, stop:1 #252535);
    color: #89b4fa;
    padding: 14px 12px;
    border: none;
    border-bottom: 2px solid rgba(137, 180, 250, 0.4);
    font-weight: bold;
    font-size: 10pt;
}

QHeaderView::section:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #45475a, stop:1 #313244);
}


/* ===== Enhanced Scrollbars ===== */
QScrollBar:vertical {
    background-color: transparent;
    width: 10px;
    margin: 4px;
}

QScrollBar::handle:vertical {
    background-color: rgba(69, 71, 90, 0.6);
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: rgba(137, 180, 250, 0.6);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    height: 0px;
    background: transparent;
}

QScrollBar:horizontal {
    background-color: transparent;
    height: 10px;
    margin: 4px;
}

QScrollBar::handle:horizontal {
    background-color: rgba(69, 71, 90, 0.6);
    border-radius: 5px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: rgba(137, 180, 250, 0.6);
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    width: 0px;
    background: transparent;
}

/* ===== Enhanced Group Box ===== */
QGroupBox {
    background-color: rgba(30, 30, 46, 0.8);
    border: 1px solid rgba(69, 71, 90, 0.5);
    border-radius: 12px;
    margin-top: 16px;
    padding: 16px;
    padding-top: 24px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: #89b4fa;
    font-weight: bold;
}

/* ===== Enhanced Checkbox & Radio ===== */
QCheckBox, QRadioButton {
    spacing: 10px;
    color: #cdd6f4;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 20px;
    height: 20px;
}

QCheckBox::indicator:unchecked {
    border: 2px solid #45475a;
    border-radius: 6px;
    background-color: #313244;
}

QCheckBox::indicator:unchecked:hover {
    border: 2px solid #89b4fa;
}

QCheckBox::indicator:checked {
    border: 2px solid #89b4fa;
    border-radius: 6px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
        stop:0 #89b4fa, stop:1 #74c7ec);
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMiIgaGVpZ2h0PSIxMiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMxZTFlMmUiIHN0cm9rZS13aWR0aD0iMyIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cG9seWxpbmUgcG9pbnRzPSIyMCA2IDkgMTcgNCAxMiI+PC9wb2x5bGluZT48L3N2Zz4=);
}

QRadioButton::indicator:unchecked {
    border: 2px solid #45475a;
    border-radius: 10px;
    background-color: #313244;
}

QRadioButton::indicator:checked {
    border: 2px solid #89b4fa;
    border-radius: 10px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
        stop:0 #89b4fa, stop:1 #74c7ec);
}

/* ===== Enhanced Progress Bar ===== */
QProgressBar {
    background-color: rgba(49, 50, 68, 0.8);
    border: none;
    border-radius: 8px;
    height: 12px;
    text-align: center;
    color: #cdd6f4;
    font-size: 9pt;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
        stop:0 #89b4fa, stop:0.5 #74c7ec, stop:1 #89dceb);
    border-radius: 8px;
}

/* ===== Labels ===== */
QLabel#title {
    font-size: 18pt;
    font-weight: bold;
    color: #cdd6f4;
}

QLabel#subtitle {
    font-size: 11pt;
    color: #a6adc8;
}

QLabel#muted {
    color: #6c7086;
}

QLabel#accent {
    color: #89b4fa;
    font-weight: bold;
}

/* ===== Enhanced Tooltips ===== */
QToolTip {
    background-color: rgba(49, 50, 68, 0.95);
    color: #cdd6f4;
    border: 1px solid rgba(137, 180, 250, 0.3);
    border-radius: 8px;
    padding: 8px 12px;
}

/* ===== Status Bar ===== */
QStatusBar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
        stop:0 #181825, stop:1 #1e1e2e);
    color: #a6adc8;
    border-top: 1px solid rgba(69, 71, 90, 0.5);
    padding: 4px;
}

/* ===== Enhanced Menu ===== */
QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
    padding: 4px;
}

QMenuBar::item {
    padding: 8px 12px;
    border-radius: 6px;
}

QMenuBar::item:selected {
    background-color: rgba(137, 180, 250, 0.2);
}

QMenu {
    background-color: rgba(49, 50, 68, 0.95);
    border: 1px solid rgba(69, 71, 90, 0.5);
    border-radius: 12px;
    padding: 8px;
}

QMenu::item {
    padding: 10px 24px;
    border-radius: 6px;
}

QMenu::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
        stop:0 #89b4fa, stop:1 #74c7ec);
    color: #1e1e2e;
}

QMenu::separator {
    height: 1px;
    background-color: rgba(69, 71, 90, 0.5);
    margin: 4px 8px;
}

/* ===== Card Styles ===== */
QFrame#card {
    background-color: rgba(49, 50, 68, 0.8);
    border: 1px solid rgba(69, 71, 90, 0.5);
    border-radius: 16px;
}

QFrame#card:hover {
    border: 1px solid rgba(137, 180, 250, 0.4);
    background-color: rgba(49, 50, 68, 0.95);
}

QFrame#statCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
        stop:0 rgba(49, 50, 68, 0.9), stop:1 rgba(69, 71, 90, 0.6));
    border: 1px solid rgba(137, 180, 250, 0.2);
    border-radius: 16px;
    padding: 16px;
}

/* ===== Status Indicator ===== */
QFrame#statusIndicator {
    background-color: rgba(49, 50, 68, 0.8);
    border: 1px solid rgba(69, 71, 90, 0.5);
    border-radius: 20px;
}

/* ===== Message Box ===== */
QMessageBox {
    background-color: #1e1e2e;
}

QMessageBox QLabel {
    color: #cdd6f4;
}

QMessageBox QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #89b4fa, stop:1 #74c7ec);
    color: #1e1e2e;
    border: none;
    padding: 6px 20px;
    border-radius: 6px;
    font-weight: bold;
    min-width: 80px;
    min-height: 25px;
}

QMessageBox QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #b4befe, stop:1 #89b4fa);
}

/* ===== Slider ===== */
QSlider::groove:horizontal {
    background-color: #313244;
    height: 6px;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #89b4fa, stop:1 #74c7ec);
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #b4befe, stop:1 #89b4fa);
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
        stop:0 #89b4fa, stop:1 #74c7ec);
    border-radius: 3px;
}

/* ===== Spin Box ===== */
QSpinBox::up-button, QSpinBox::down-button {
    background-color: #45475a;
    border: none;
    border-radius: 4px;
    width: 20px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #89b4fa;
}

QSpinBox::up-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #cdd6f4;
}

QSpinBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #cdd6f4;
}
"""

# ============================================================
# LIGHT THEME - Apple-inspired clean design
# ============================================================
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
