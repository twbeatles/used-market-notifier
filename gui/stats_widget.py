# gui/stats_widget.py
"""Enhanced statistics dashboard with modern card design"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QGridLayout, QScrollArea, QFrame, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
import sys
sys.path.insert(0, '..')

try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    
    # Configure Korean font
    plt.rcParams['font.family'] = ['Malgun Gothic', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


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
        icon_label.setStyleSheet(f"font-size: 20pt; background: transparent;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {self.color}; font-size: 11pt; background: transparent;")
        header.addWidget(title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            font-size: 28pt; 
            font-weight: bold; 
            color: #c0caf5;
            background: transparent;
        """)
        layout.addWidget(self.value_label)
        
        layout.addStretch()
    
    def update_value(self, value: str):
        self.value_label.setText(value)


class PlatformChart(QWidget):
    """Platform distribution pie chart"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if HAS_MATPLOTLIB:
            self.figure = Figure(figsize=(4, 3), facecolor='#1f2335')
            self.canvas = FigureCanvas(self.figure)
            self.canvas.setStyleSheet("background-color: transparent;")
            layout.addWidget(self.canvas)
            self._draw_empty()
        else:
            label = QLabel("📊 matplotlib 필요\n\npip install matplotlib")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #565f89; font-size: 11pt;")
            layout.addWidget(label)
    
    def _draw_empty(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center', 
                color='#565f89', fontsize=12)
        ax.set_facecolor('#1f2335')
        ax.axis('off')
        self.figure.patch.set_facecolor('#1f2335')
        self.canvas.draw()
    
    def update_chart(self, data: dict):
        if not HAS_MATPLOTLIB:
            return
        
        if not data or all(v == 0 for v in data.values()):
            self._draw_empty()
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Filter out zero values
        filtered = {k: v for k, v in data.items() if v > 0}
        
        if not filtered:
            self._draw_empty()
            return
        
        labels = list(filtered.keys())
        values = list(filtered.values())
        colors = ['#ff9e64', '#bb9af7', '#9ece6a'][:len(labels)]
        
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, autopct='%1.1f%%',
            colors=colors, 
            textprops={'color': '#c0caf5', 'fontsize': 10},
            wedgeprops={'linewidth': 2, 'edgecolor': '#1f2335'}
        )
        
        for autotext in autotexts:
            autotext.set_fontweight('bold')
        
        ax.axis('equal')
        self.figure.patch.set_facecolor('#1f2335')
        self.figure.tight_layout()
        
        self.canvas.draw()


class DailyChart(QWidget):
    """Daily stats line/bar chart"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if HAS_MATPLOTLIB:
            self.figure = Figure(figsize=(6, 3), facecolor='#1f2335')
            self.canvas = FigureCanvas(self.figure)
            self.canvas.setStyleSheet("background-color: transparent;")
            layout.addWidget(self.canvas)
            self._draw_empty()
        else:
            label = QLabel("📊 matplotlib 필요")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #565f89;")
            layout.addWidget(label)
    
    def _draw_empty(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center', 
                color='#565f89', fontsize=12)
        ax.set_facecolor('#1f2335')
        ax.axis('off')
        self.figure.patch.set_facecolor('#1f2335')
        self.canvas.draw()
    
    def update_chart(self, data: list):
        if not HAS_MATPLOTLIB or not data:
            if HAS_MATPLOTLIB:
                self._draw_empty()
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        dates = [d['date'][-5:] for d in data]  # MM-DD format
        items_found = [d['items_found'] or 0 for d in data]
        new_items = [d['new_items'] or 0 for d in data]
        
        x = range(len(dates))
        width = 0.35
        
        bars1 = ax.bar([i - width/2 for i in x], items_found, width, 
                       label='검색됨', color='#7aa2f7', alpha=0.8)
        bars2 = ax.bar([i + width/2 for i in x], new_items, width, 
                       label='새 상품', color='#9ece6a', alpha=0.8)
        
        ax.set_xticks(x)
        ax.set_xticklabels(dates, color='#7982a9', fontsize=9)
        ax.tick_params(axis='y', colors='#7982a9')
        ax.legend(facecolor='#24283b', labelcolor='#c0caf5', fontsize=9)
        ax.set_facecolor('#1f2335')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#3b4261')
        ax.spines['bottom'].set_color('#3b4261')
        
        self.figure.patch.set_facecolor('#1f2335')
        self.figure.tight_layout()
        
        self.canvas.draw()


class StatsWidget(QWidget):
    """Modern statistics dashboard"""
    
    def __init__(self, engine=None, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setup_ui()
        
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_stats)
        self.refresh_timer.start(30000)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📊 통계 대시보드")
        title.setObjectName("title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.setObjectName("secondary")
        refresh_btn.clicked.connect(self.refresh_stats)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Stat cards row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        
        self.total_card = StatCard("전체 상품", "0", "📦", "#7aa2f7")
        cards_layout.addWidget(self.total_card)
        
        self.danggeun_card = StatCard("당근마켓", "0", "🥕", "#ff9e64")
        cards_layout.addWidget(self.danggeun_card)
        
        self.bunjang_card = StatCard("번개장터", "0", "⚡", "#bb9af7")
        cards_layout.addWidget(self.bunjang_card)
        
        self.joonggonara_card = StatCard("중고나라", "0", "🛒", "#9ece6a")
        cards_layout.addWidget(self.joonggonara_card)
        
        layout.addLayout(cards_layout)
        
        # Charts row
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(16)
        
        # Platform pie chart
        platform_group = QGroupBox("플랫폼별 분포")
        platform_layout = QVBoxLayout(platform_group)
        platform_layout.setContentsMargins(12, 20, 12, 12)
        self.platform_chart = PlatformChart()
        platform_layout.addWidget(self.platform_chart)
        charts_layout.addWidget(platform_group, 1)
        
        # Daily chart
        daily_group = QGroupBox("일별 추이 (최근 7일)")
        daily_layout = QVBoxLayout(daily_group)
        daily_layout.setContentsMargins(12, 20, 12, 12)
        self.daily_chart = DailyChart()
        daily_layout.addWidget(self.daily_chart)
        charts_layout.addWidget(daily_group, 2)
        
        layout.addLayout(charts_layout)
        
        # Tables row
        tables_layout = QHBoxLayout()
        tables_layout.setSpacing(16)
        
        # Recent items table
        recent_group = QGroupBox("최근 발견된 상품")
        recent_layout = QVBoxLayout(recent_group)
        recent_layout.setContentsMargins(12, 20, 12, 12)
        
        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(5)
        self.recent_table.setHorizontalHeaderLabels(["플랫폼", "제목", "가격", "키워드", "시간"])
        self.recent_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.recent_table.setAlternatingRowColors(True)
        self.recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.recent_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.recent_table.verticalHeader().setVisible(False)
        recent_layout.addWidget(self.recent_table)
        
        tables_layout.addWidget(recent_group, 2)
        
        # Price changes table  
        price_group = QGroupBox("가격 변동")
        price_layout = QVBoxLayout(price_group)
        price_layout.setContentsMargins(12, 20, 12, 12)
        
        self.price_table = QTableWidget()
        self.price_table.setColumnCount(4)
        self.price_table.setHorizontalHeaderLabels(["제목", "이전", "현재", "시간"])
        self.price_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.price_table.setAlternatingRowColors(True)
        self.price_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.price_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.price_table.verticalHeader().setVisible(False)
        price_layout.addWidget(self.price_table)
        
        tables_layout.addWidget(price_group, 1)
        
        layout.addLayout(tables_layout)
    
    def set_engine(self, engine):
        self.engine = engine
        self.refresh_stats()
    
    def refresh_stats(self):
        if not self.engine:
            return
        
        try:
            stats = self.engine.get_stats()
            
            # Update cards
            self.total_card.update_value(f"{stats.get('total_listings', 0):,}")
            
            by_platform = stats.get('by_platform', {})
            self.danggeun_card.update_value(f"{by_platform.get('danggeun', 0):,}")
            self.bunjang_card.update_value(f"{by_platform.get('bunjang', 0):,}")
            self.joonggonara_card.update_value(f"{by_platform.get('joonggonara', 0):,}")
            
            # Update charts
            self.platform_chart.update_chart(by_platform)
            self.daily_chart.update_chart(stats.get('daily_stats', []))
            
            # Update recent items table
            recent = stats.get('recent_listings', [])
            self.recent_table.setRowCount(min(len(recent), 10))
            for i, item in enumerate(recent[:10]):
                self.recent_table.setItem(i, 0, QTableWidgetItem(item.get('platform', '')[:8]))
                self.recent_table.setItem(i, 1, QTableWidgetItem(item.get('title', '')[:40]))
                self.recent_table.setItem(i, 2, QTableWidgetItem(item.get('price', '')))
                self.recent_table.setItem(i, 3, QTableWidgetItem(item.get('keyword', '')[:15]))
                self.recent_table.setItem(i, 4, QTableWidgetItem(item.get('created_at', '')[11:16]))
            
            # Update price changes table
            changes = stats.get('price_changes', [])
            self.price_table.setRowCount(min(len(changes), 5))
            for i, change in enumerate(changes[:5]):
                self.price_table.setItem(i, 0, QTableWidgetItem(change.get('title', '')[:30]))
                self.price_table.setItem(i, 1, QTableWidgetItem(change.get('old_price', '')))
                self.price_table.setItem(i, 2, QTableWidgetItem(change.get('new_price', '')))
                self.price_table.setItem(i, 3, QTableWidgetItem(change.get('changed_at', '')[11:16]))
                
        except Exception as e:
            print(f"Error refreshing stats: {e}")
