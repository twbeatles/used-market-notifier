"""Color palette and platform styling constants."""

# gui/styles.py
"""
Modern stylesheet definitions for the application.
Theme: Enhanced Catppuccin Mocha with Glassmorphism and animations.
"""

# ============================================================
# Catppuccin Mocha Color Palette
# ============================================================
CATPPUCCIN_MOCHA = {
    # Base colors
    'base': '#1e1e2e',
    'mantle': '#181825',
    'crust': '#11111b',
    'surface0': '#313244',
    'surface1': '#45475a',
    'surface2': '#585b70',
    'overlay0': '#6c7086',
    'overlay1': '#7f849c',
    'overlay2': '#9399b2',
    # Text colors
    'text': '#cdd6f4',
    'subtext0': '#a6adc8',
    'subtext1': '#bac2de',
    # Accent colors
    'blue': '#89b4fa',
    'lavender': '#b4befe',
    'sapphire': '#74c7ec',
    'sky': '#89dceb',
    'teal': '#94e2d5',
    'green': '#a6e3a1',
    'yellow': '#f9e2af',
    'peach': '#fab387',
    'maroon': '#eba0ac',
    'red': '#f38ba8',
    'mauve': '#cba6f7',
    'pink': '#f5c2e7',
    'flamingo': '#f2cdcd',
    'rosewater': '#f5e0dc',
}

# ============================================================
# Platform styling info
# ============================================================
PLATFORM_INFO = {
    'danggeun': {
        'color': '#FF6F00', 
        'gradient': 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF6F00, stop:1 #FF9800)',
        'emoji': '🥕', 
        'name': '당근마켓'
    },
    'bunjang': {
        'color': '#7B68EE', 
        'gradient': 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7B68EE, stop:1 #9575CD)',
        'emoji': '⚡', 
        'name': '번개장터'
    },
    'joonggonara': {
        'color': '#00C853', 
        'gradient': 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00C853, stop:1 #69F0AE)',
        'emoji': '🛒', 
        'name': '중고나라'
    }
}
