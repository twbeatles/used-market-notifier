# gui/styles.py
"""Stylesheet definitions for the application - Catppuccin Mocha Theme"""

# Catppuccin Mocha Color Palette
CATPPUCCIN_MOCHA = {
    # Base colors
    'base': '#1e1e2e',
    'mantle': '#181825',
    'crust': '#11111b',
    'surface0': '#313244',
    'surface1': '#45475a',
    'surface2': '#585b70',
    'overlay0': '#8087a2',
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
DARK_STYLE = """
/* ===== Main Windows ===== */
QMainWindow {
    background-color: #1e1e2e;
    color: #cdd6f4;
}

QDialog {
    background-color: #1e1e2e;
    color: #cdd6f4;
}

/* ===== Base Widget Defaults ===== */
QWidget {
    color: #cdd6f4;
    font-family: "Segoe UI", "Malgun Gothic", sans-serif;
    font-size: 10pt;
}

/* ===== Tab Widget ===== */
QTabWidget::pane {
    border: 1px solid #45475a;
    background-color: #1e1e2e;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: #313244;
    color: #cdd6f4;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #89b4fa;
    color: #1e1e2e;
    font-weight: bold;
}

QTabBar::tab:hover:!selected {
    background-color: #45475a;
}

/* ===== Buttons ===== */
QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: bold;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #b4befe;
}

QPushButton:pressed {
    background-color: #74c7ec;
}

QPushButton:disabled {
    background-color: #45475a;
    color: #8087a2;
}

QPushButton#danger {
    background-color: #f38ba8;
    color: #1e1e2e;
}

QPushButton#danger:hover {
    background-color: #eba0ac;
}

QPushButton#success {
    background-color: #a6e3a1;
    color: #1e1e2e;
}

QPushButton#success:hover {
    background-color: #94e2d5;
}

QPushButton#warning {
    background-color: #f9e2af;
    color: #1e1e2e;
}

QPushButton#secondary {
    background-color: #45475a;
    color: #cdd6f4;
}

QPushButton#secondary:hover {
    background-color: #585b70;
}

/* ===== Inputs ===== */
QLineEdit, QSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px;
    color: #cdd6f4;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {
    border: 2px solid #89b4fa;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox::down-arrow {
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #cdd6f4;
}

QComboBox QAbstractItemView {
    background-color: #313244;
    border: 1px solid #45475a;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
}

/* ===== Lists & Tables ===== */
QListWidget, QTableWidget, QTreeWidget {
    background-color: #1e1e2e;
    alternate-background-color: #252535;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 4px;
    gridline-color: #3b4261;
}

QListWidget::item, QTableWidget::item {
    padding: 12px;
    border-radius: 4px;
}

QListWidget::item:selected, QTableWidget::item:selected {
    background-color: #89b4fa;
    color: #1e1e2e;
}

QListWidget::item:hover:!selected, QTableWidget::item:hover:!selected {
    background-color: #3b4261;
}

QHeaderView::section {
    background-color: #313244;
    color: #cdd6f4;
    padding: 10px 8px;
    border: none;
    border-bottom: 2px solid #89b4fa;
    font-weight: bold;
}

/* ===== Scrollbars ===== */
QScrollBar:vertical {
    background-color: #313244;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #585b70;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #313244;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #45475a;
    border-radius: 6px;
    min-width: 20px;
}

/* ===== Group Box ===== */
QGroupBox {
    background-color: #1e1e2e;
    border: 1px solid #45475a;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #89b4fa;
}

/* ===== Checkbox & Radio ===== */
QCheckBox, QRadioButton {
    spacing: 8px;
    color: #cdd6f4;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
}

QCheckBox::indicator:unchecked {
    border: 2px solid #45475a;
    border-radius: 4px;
    background-color: #313244;
}

QCheckBox::indicator:checked {
    border: 2px solid #89b4fa;
    border-radius: 4px;
    background-color: #89b4fa;
}

/* ===== Progress Bar ===== */
QProgressBar {
    background-color: #313244;
    border: none;
    border-radius: 6px;
    height: 20px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #89b4fa;
    border-radius: 6px;
}

/* ===== Labels ===== */
QLabel#title {
    font-size: 16pt;
    font-weight: bold;
    color: #89b4fa;
}

QLabel#subtitle {
    font-size: 11pt;
    color: #a6adc8;
}

QLabel#muted {
    color: #8087a2;
}

/* ===== Tooltips ===== */
QToolTip {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px;
}

/* ===== Status Bar ===== */
QStatusBar {
    background-color: #181825;
    color: #a6adc8;
}

/* ===== Menu ===== */
QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
}

QMenuBar::item:selected {
    background-color: #45475a;
}

QMenu {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #89b4fa;
    color: #1e1e2e;
}

/* ===== Frame ===== */
QFrame#header {
    background-color: #181825;
}

QFrame#card {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 12px;
}

QFrame#statCard {
    background-color: #313244;
    border-radius: 12px;
    padding: 16px;
}

/* ===== Message Box ===== */
QMessageBox {
    background-color: #1e1e2e;
}
"""

LIGHT_STYLE = """
/* ===== Main Windows ===== */
QMainWindow, QDialog {
    background-color: #f2f2f7;
    color: #1c1c1e;
}

QWidget {
    color: #1c1c1e;
    font-family: "Segoe UI", "Malgun Gothic", sans-serif;
    font-size: 10pt;
}

/* ===== Tab Widget ===== */
QTabWidget::pane {
    border: 1px solid #d1d1d6;
    background-color: #ffffff;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: #e5e5ea;
    color: #8e8e93;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #007aff;
    color: #ffffff;
    font-weight: bold;
}

QTabBar::tab:hover:!selected {
    background-color: #d1d1d6;
}

/* ===== Buttons ===== */
QPushButton {
    background-color: #007aff;
    color: #ffffff;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: bold;
}
QPushButton:hover { background-color: #0056b3; }
QPushButton:disabled { background-color: #d1d1d6; color: #8e8e93; }

QPushButton#danger { background-color: #ff3b30; }
QPushButton#danger:hover { background-color: #d70015; }

QPushButton#success { background-color: #34c759; }
QPushButton#success:hover { background-color: #248a3d; }

QPushButton#secondary { background-color: #e5e5ea; color: #1c1c1e; }
QPushButton#secondary:hover { background-color: #d1d1d6; }

/* ===== Input Fields ===== */
QLineEdit, QSpinBox, QTextEdit, QComboBox {
    background-color: #ffffff;
    color: #1c1c1e;
    border: 1px solid #d1d1d6;
    border-radius: 4px;
    padding: 6px;
}
QLineEdit:focus, QSpinBox:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #007aff;
}

/* ===== Tables ===== */
QTableWidget, QTableView {
    background-color: #ffffff;
    alternate-background-color: #f2f2f7;
    gridline-color: #e5e5ea;
    border: 1px solid #d1d1d6;
    color: #1c1c1e;
}
QHeaderView::section {
    background-color: #f2f2f7;
    color: #636366;
    border: none;
    border-bottom: 1px solid #d1d1d6;
    padding: 8px;
}
QTableWidget::item:selected {
    background-color: #007aff;
    color: #ffffff;
}
"""

# Platform colors with Korean names
PLATFORM_INFO = {
    'danggeun': {'color': '#FF6F00', 'emoji': '🥕', 'name': '당근마켓'},
    'bunjang': {'color': '#7B68EE', 'emoji': '⚡', 'name': '번개장터'},
    'joonggonara': {'color': '#00C853', 'emoji': '🛒', 'name': '중고나라'}
}
