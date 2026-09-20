"""Scrollbars, groups, checks, progress."""

CHROME_QSS = """/* ===== Enhanced Scrollbars ===== */
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

"""
