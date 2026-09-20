"""Base window/header/card primitives."""

BASE_QSS = """
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

"""
