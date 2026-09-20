"""Tab widget styling."""

TABS_QSS = """/* ===== Enhanced Tab Widget ===== */
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

"""
