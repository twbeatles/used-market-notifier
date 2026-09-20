"""Labels, tooltips, status bar, menus."""

OVERLAYS_QSS = """/* ===== Labels ===== */
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

"""
