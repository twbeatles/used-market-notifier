"""Lists, tables, and headers."""

LISTS_QSS = """/* ===== Enhanced Lists & Tables ===== */
QListWidget, QTableWidget, QTreeWidget {
    background-color: rgba(30, 30, 46, 0.95);
    alternate-background-color: rgba(49, 50, 68, 0.8);
    border: 1px solid rgba(69, 71, 90, 0.5);
    border-radius: 12px;
    padding: 8px;
    gridline-color: rgba(69, 71, 90, 0.3);
    outline: none;
}

QListWidget::item, QTableWidget::item {
    padding: 14px 16px;
    border-radius: 6px;
    border-bottom: 1px solid rgba(69, 71, 90, 0.2);
    margin: 1px 0;
}

QListWidget::item:selected, QTableWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
        stop:0 rgba(137, 180, 250, 0.95), stop:1 rgba(116, 199, 236, 0.95));
    color: #1e1e2e;
    border-radius: 8px;
    font-weight: 500;
}

QListWidget::item:hover:!selected, QTableWidget::item:hover:!selected {
    background-color: rgba(137, 180, 250, 0.2);
    border-radius: 6px;
}

/* Row highlight on focus */
QTableWidget::item:focus {
    background-color: rgba(137, 180, 250, 0.25);
    border: 1px solid rgba(137, 180, 250, 0.5);
}

QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #313244, stop:1 #252535);
    color: #89b4fa;
    padding: 16px 14px;
    border: none;
    border-bottom: 2px solid rgba(137, 180, 250, 0.5);
    font-weight: bold;
    font-size: 10pt;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QHeaderView::section:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #45475a, stop:1 #313244);
    color: #b4befe;
}


"""
