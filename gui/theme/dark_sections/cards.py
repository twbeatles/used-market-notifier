"""Cards, dialogs, sliders, spin boxes."""

CARDS_QSS = """/* ===== Card Styles ===== */
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
    min-width: 300px;
}

QMessageBox QLabel {
    color: #cdd6f4;
    font-size: 11pt;
    padding: 10px;
}

QMessageBox QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #89b4fa, stop:1 #74c7ec);
    color: #1e1e2e;
    border: none;
    padding: 10px 24px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 10pt;
    min-width: 100px;
    min-height: 32px;
    margin: 4px;
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
