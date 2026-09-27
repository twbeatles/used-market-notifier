from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from qfluentwidgets import CaptionLabel, isDarkTheme
from typing import Any
import warnings

FigureCanvas: Any = None
Figure: Any = None

try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    
    # Configure Korean font
    plt.rcParams['font.family'] = ['Malgun Gothic', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def _chart_palette() -> dict:
    """Theme-aware chart chrome colors (series colors stay fixed)."""
    if isDarkTheme():
        return {
            "bg": "#1e1e2e",
            "text": "#cdd6f4",
            "muted": "#7982a9",
            "edge": "#3b4261",
            "legend_bg": "#24283b",
        }
    return {
        "bg": "#ffffff",
        "text": "#1e1e2e",
        "muted": "#6c7086",
        "edge": "#d0d0d0",
        "legend_bg": "#f5f5f5",
    }


class PlatformChart(QWidget):
    """Platform distribution pie chart"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if HAS_MATPLOTLIB and Figure is not None and FigureCanvas is not None:
            self.figure = Figure(figsize=(4, 3), facecolor=_chart_palette()["bg"])
            self.canvas = FigureCanvas(self.figure)
            layout.addWidget(self.canvas)
            self._draw_empty()
        else:
            label = CaptionLabel("matplotlib 필요\n\npip install matplotlib")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(True)
            layout.addWidget(label)
    
    def _draw_empty(self):
        if not hasattr(self, "figure") or not hasattr(self, "canvas"):
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        pal = _chart_palette()
        ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center', 
                color=pal["muted"], fontsize=12)
        ax.set_facecolor(_chart_palette()["bg"])
        ax.axis('off')
        self.figure.patch.set_facecolor(_chart_palette()["bg"])
        self.canvas.draw()
    
    def update_chart(self, data: dict):
        if not HAS_MATPLOTLIB or not hasattr(self, "figure") or not hasattr(self, "canvas"):
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
        
        pie_result = ax.pie(
            values, labels=labels, autopct='%1.1f%%',
            colors=colors, 
            textprops={'color': _chart_palette()["text"], 'fontsize': 10},
            wedgeprops={'linewidth': 2, 'edgecolor': _chart_palette()["bg"]}
        )
        autotexts = pie_result[2] if len(pie_result) > 2 else []
        
        for autotext in autotexts:
            autotext.set_fontweight('bold')
        
        ax.axis('equal')
        self.figure.patch.set_facecolor(_chart_palette()["bg"])
        
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
        
        if HAS_MATPLOTLIB and Figure is not None and FigureCanvas is not None:
            self.figure = Figure(figsize=(6, 3), facecolor=_chart_palette()["bg"])
            self.canvas = FigureCanvas(self.figure)
            layout.addWidget(self.canvas)
            self._draw_empty()
        else:
            label = CaptionLabel("matplotlib 필요", self)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
    
    def _draw_empty(self):
        if not hasattr(self, "figure") or not hasattr(self, "canvas"):
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        pal = _chart_palette()
        ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center', 
                color=pal["muted"], fontsize=12)
        ax.set_facecolor(_chart_palette()["bg"])
        ax.axis('off')
        self.figure.patch.set_facecolor(_chart_palette()["bg"])
        self.canvas.draw()
    
    def update_chart(self, data: list):
        if not HAS_MATPLOTLIB or not hasattr(self, "figure") or not hasattr(self, "canvas") or not data:
            if HAS_MATPLOTLIB and hasattr(self, "figure") and hasattr(self, "canvas"):
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
        ax.set_xticklabels(dates, color=_chart_palette()["muted"], fontsize=9)
        ax.tick_params(axis='y', colors=_chart_palette()["muted"])
        pal = _chart_palette()
        ax.legend(facecolor=pal["legend_bg"], labelcolor=pal["text"], fontsize=9)
        
        ax.set_facecolor(_chart_palette()["bg"])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(_chart_palette()["edge"])
        ax.spines['bottom'].set_color(_chart_palette()["edge"])
        
        self.figure.patch.set_facecolor(_chart_palette()["bg"])
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            self.figure.tight_layout()
        
        self.canvas.draw()
