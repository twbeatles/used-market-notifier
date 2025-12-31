from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
)

class StatCard(QFrame):
    """Modern statistic card with gradient background"""
    
    def __init__(self, title: str, value: str, icon: str = "", 
                 color: str = "#7aa2f7", gradient_end: str = None, parent=None):
        super().__init__(parent)
        self.color = color
        self.gradient_end = gradient_end or self._darken_color(color)
        self.setup_ui(title, value, icon)
    
    def _darken_color(self, hex_color: str) -> str:
        """Darken a hex color"""
        c = hex_color.lstrip('#')
        rgb = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(max(0, int(v * 0.7)) for v in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
    
    def setup_ui(self, title: str, value: str, icon: str):
        self.setMinimumSize(180, 110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {self.color}33, stop:1 {self.gradient_end}22);
                border: 2px solid {self.color}44;
                border-radius: 16px;
                padding: 16px;
            }}
            QFrame:hover {{
                border: 2px solid {self.color}88;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Icon and title row
        header = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20pt; background: transparent;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {self.color}; font-size: 11pt; background: transparent;")
        header.addWidget(title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("""
            font-size: 28pt; 
            font-weight: bold; 
            color: #c0caf5;
            background: transparent;
        """)
        layout.addWidget(self.value_label)
        
        layout.addStretch()
    
    def update_value(self, value: str):
        self.value_label.setText(value)
    
    def set_value(self, value: str):
        self.update_value(value)
