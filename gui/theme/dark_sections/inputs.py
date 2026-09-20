"""Text inputs, combos, and editors."""

INPUTS_QSS = """/* ===== Enhanced Input Fields ===== */
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

"""
