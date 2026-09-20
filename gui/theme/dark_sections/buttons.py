"""Push-button variants."""

BUTTONS_QSS = """/* ===== Gradient Buttons ===== */
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

"""
