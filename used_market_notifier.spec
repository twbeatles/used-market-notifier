# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Used Market Notifier (Selenium version)
# Optimized for minimal build size

import sys
import os

block_cipher = None

# Hidden imports - only what's needed
hiddenimports = [
    # Core Python
    'asyncio',
    'asyncio.windows_events',
    'asyncio.windows_utils',
    'sqlite3',
    'json',
    'logging',
    'logging.handlers',
    'difflib',
    'dataclasses',
    'concurrent.futures',
    'winreg',  # For theme detection
    
    # Selenium & WebDriver
    'selenium',
    'selenium.webdriver',
    'selenium.webdriver.chrome',
    'selenium.webdriver.chrome.service',
    'selenium.webdriver.chrome.options',
    'selenium.webdriver.common.by',
    'selenium.webdriver.support.ui',
    'selenium.webdriver.support.expected_conditions',
    'webdriver_manager',
    'webdriver_manager.chrome',
    
    # PyQt6
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.sip',
    
    # Matplotlib (for charts)
    'matplotlib',
    'matplotlib.backends.backend_qtagg',
    'matplotlib.figure',
    
    # Optional exports
    'openpyxl',
    
    # HTTP for notifiers
    'aiohttp',
    
    # Our modules
    'scrapers',
    'scrapers.base',
    'scrapers.selenium_base',
    'scrapers.danggeun',
    'scrapers.bunjang',
    'scrapers.joonggonara',
    'notifiers',
    'notifiers.base',
    'notifiers.telegram_notifier',
    'notifiers.discord_notifier',
    'notifiers.slack_notifier',
    'gui',
    'gui.main_window',
    'gui.keyword_manager',
    'gui.stats_widget',
    'gui.favorites_widget',
    'gui.notification_history',
    'gui.settings_dialog',
    'gui.log_widget',
    'gui.system_tray',
    'gui.charts',
    'gui.components',
    'gui.styles',
    'gui.listings_widget',
    'gui.loading_spinner',
    'gui.note_dialog',
    'gui.compare_dialog',
    'models',
    'db',
    'settings_manager',
    'monitor_engine',
    'export_manager',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unused modules for smaller build
        'tkinter',
        '_tkinter',
        'unittest',
        'test',
        'tests',
        'pytest',
        'setuptools',
        'distutils',
        'pip',
        'wheel',
        'pkg_resources',
        
        # Unused Playwright modules
        'playwright',
        'greenlet',
        'pyee',
        
        # Development tools
        'IPython',
        'jupyter',
        'notebook',
        'sphinx',
        
        # Unused GUI backends
        'PyQt5',
        'PySide2',
        'PySide6',
        'wx',
        'gtk',
        
        # Unused matplotlib backends
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends.backend_wxagg',
        'matplotlib.backends.backend_gtk3agg',
        
        # Other unused
        'numpy.testing',
        'numpy.f2py',
        'scipy',
        'pandas',
        'PIL.ImageTk',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='UsedMarketNotifier',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip debug symbols
    upx=True,    # Enable UPX compression
    upx_exclude=[
        'vcruntime140.dll',
        'python*.dll',
        'Qt*.dll',
    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add: icon='icon.ico'
)
