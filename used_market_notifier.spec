# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Used Market Notifier

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all necessary data files and submodules
datas = []
hiddenimports = [
    # Core
    'asyncio',
    'sqlite3',
    'json',
    'logging',
    'logging.handlers',
    'difflib',
    'dataclasses',
    
    # Selenium
    'selenium',
    'selenium.webdriver',
    'selenium.webdriver.common.by',
    'selenium.webdriver.support',
    'selenium.webdriver.support.ui',
    'selenium.webdriver.support.expected_conditions',
    'selenium.webdriver.chrome.service',
    'selenium.webdriver.chrome.options',
    
    # WebDriver Manager
    'webdriver_manager',
    'webdriver_manager.chrome',
    
    # aiohttp for async HTTP
    'aiohttp',
    'aiohttp.web',
    
    # PyQt6
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.sip',
    
    # Matplotlib (optional, for charts)
    'matplotlib',
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.figure',
    'matplotlib.pyplot',
    
    # openpyxl for Excel export
    'openpyxl',
    
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
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'test',
        'tests',
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
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True if you want console output for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one: icon='icon.ico'
)
