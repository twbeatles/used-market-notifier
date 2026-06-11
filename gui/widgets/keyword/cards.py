"""Keyword card widgets."""

from .common import *


class KeywordCard(QFrame):
    """Individual keyword card with modern glassmorphism design and hover effects"""

    clicked = pyqtSignal(int)
    double_clicked = pyqtSignal(int)

    def __init__(self, index: int, keyword: SearchKeyword, parent=None):
        super().__init__(parent)
        self.index = index
        self.keyword = keyword
        self.selected = False
        self._setup_shadow()
        self.setup_ui()

    def _setup_shadow(self):
        """Setup drop shadow effect for card lift"""
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 50))
        self.shadow.setOffset(0, 4)
        self.setGraphicsEffect(self.shadow)

    def setup_ui(self):
        self.setObjectName("keywordCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style()

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(18, 14, 18, 14)

        # Header row
        header = QHBoxLayout()

        # Status indicator with animation-ready style
        status = "🟢" if self.keyword.enabled else "⏸️"
        status_label = QLabel(status)
        status_label.setStyleSheet("font-size: 16pt; background: transparent;")
        header.addWidget(status_label)

        # Keyword name with accent color
        name_label = QLabel(self.keyword.keyword)
        name_label.setStyleSheet("""
            font-size: 14pt;
            font-weight: bold;
            color: #cdd6f4;
            background: transparent;
        """)
        header.addWidget(name_label)

        header.addStretch()

        # Platform badges with gradient
        for platform in self.keyword.platforms:
            badge = self.create_platform_badge(platform)
            header.addWidget(badge)

        layout.addLayout(header)

        # Details row
        details = QHBoxLayout()
        details.setSpacing(16)

        # Price range with icon
        if self.keyword.min_price or self.keyword.max_price:
            min_str = f"{self.keyword.min_price:,}" if self.keyword.min_price else "0"
            max_str = f"{self.keyword.max_price:,}" if self.keyword.max_price else "∞"
            price_label = QLabel(f"💰 {min_str} ~ {max_str}원")
            price_label.setStyleSheet("""
                color: #a6e3a1;
                font-size: 9pt;
                background: transparent;
            """)
            details.addWidget(price_label)

        # Location
        if self.keyword.location:
            loc_label = QLabel(f"📍 {self.keyword.location}")
            loc_label.setStyleSheet("""
                color: #fab387;
                font-size: 9pt;
                background: transparent;
            """)
            details.addWidget(loc_label)

        # Excludes
        if self.keyword.exclude_keywords:
            ex_label = QLabel(f"🚫 {len(self.keyword.exclude_keywords)}개 제외")
            ex_label.setStyleSheet("""
                color: #f38ba8;
                font-size: 9pt;
                background: transparent;
            """)
            details.addWidget(ex_label)

        # Notification status
        notify_enabled = getattr(self.keyword, 'notify_enabled', True)
        notify_icon = "🔔" if notify_enabled else "🔕"
        notify_label = QLabel(notify_icon)
        notify_label.setStyleSheet("""
            font-size: 9pt;
            background: transparent;
        """)
        notify_label.setToolTip("알림 " + ("켜짐" if notify_enabled else "꺼짐"))
        details.addWidget(notify_label)

        details.addStretch()
        layout.addLayout(details)

    def create_platform_badge(self, platform: str) -> QLabel:
        """Create gradient platform badge"""
        colors = {
            'danggeun': ('#FF6F00', '#FF9800', '🥕'),
            'bunjang': ('#7B68EE', '#9575CD', '⚡'),
            'joonggonara': ('#00C853', '#69F0AE', '🛒')
        }
        base_color, light_color, emoji = colors.get(platform, ('#89b4fa', '#b4befe', '📦'))

        badge = QLabel(emoji)
        badge.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {base_color}, stop:1 {light_color});
            color: white;
            padding: 5px 10px;
            border-radius: 12px;
            font-size: 12pt;
        """)
        return badge

    def update_style(self):
        if self.selected:
            self.setStyleSheet("""
                QFrame#keywordCard {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(49, 50, 68, 0.95), stop:1 rgba(69, 71, 90, 0.8));
                    border: 2px solid #89b4fa;
                    border-radius: 16px;
                }
            """)
            self.shadow.setBlurRadius(25)
            self.shadow.setOffset(0, 6)
        else:
            self.setStyleSheet("""
                QFrame#keywordCard {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(30, 30, 46, 0.9), stop:1 rgba(49, 50, 68, 0.7));
                    border: 1px solid rgba(69, 71, 90, 0.5);
                    border-radius: 16px;
                }
                QFrame#keywordCard:hover {
                    border: 1px solid rgba(137, 180, 250, 0.5);
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(37, 37, 53, 0.95), stop:1 rgba(49, 50, 68, 0.85));
                }
            """)
            self.shadow.setBlurRadius(15)
            self.shadow.setOffset(0, 4)

    def set_selected(self, selected: bool):
        self.selected = selected
        self.update_style()

    def enterEvent(self, event):
        """Lift card on hover"""
        if not self.selected:
            self.shadow.setBlurRadius(22)
            self.shadow.setOffset(0, 6)
        super().enterEvent(event)

    def leaveEvent(self, a0):
        """Reset card on leave"""
        if not self.selected:
            self.shadow.setBlurRadius(15)
            self.shadow.setOffset(0, 4)
        super().leaveEvent(a0)

    def mousePressEvent(self, a0):
        self.clicked.emit(self.index)
        super().mousePressEvent(a0)

    def mouseDoubleClickEvent(self, a0):
        self.double_clicked.emit(self.index)
        super().mouseDoubleClickEvent(a0)
