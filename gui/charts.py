from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
import warnings

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


class PlatformChart(QWidget):
    """Platform distribution pie chart"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if HAS_MATPLOTLIB:
            self.figure = Figure(figsize=(4, 3), facecolor='#1e1e2e')
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
        ax.set_facecolor('#1e1e2e')
        ax.axis('off')
        self.figure.patch.set_facecolor('#1e1e2e')
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
            wedgeprops={'linewidth': 2, 'edgecolor': '#1e1e2e'}
        )
        
        for autotext in autotexts:
            autotext.set_fontweight('bold')
        
        ax.axis('equal')
        self.figure.patch.set_facecolor('#1e1e2e')
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
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
            self.figure = Figure(figsize=(6, 3), facecolor='#1e1e2e')
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
        ax.set_facecolor('#1e1e2e')
        ax.axis('off')
        self.figure.patch.set_facecolor('#1e1e2e')
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
        
        ax.set_facecolor('#1e1e2e')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#3b4261')
        ax.spines['bottom'].set_color('#3b4261')
        
        self.figure.patch.set_facecolor('#1e1e2e')
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            self.figure.tight_layout()
        
        self.canvas.draw()
