# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect dynamic modules and data
datas = []
binaries = []

# Core hidden imports
hiddenimports = [
    # Application modules
    'scrapers.danggeun',
    'scrapers.bunjang',
    'scrapers.joonggonara',
    'notifiers.telegram_notifier',
    'notifiers.discord_notifier',
    'notifiers.slack_notifier',
    'gui.styles',
    'gui.main_window',
    'gui.keyword_manager',
    'gui.stats_widget',
    'gui.settings_dialog',
    'gui.log_widget',
    'gui.system_tray',
    
    # Dependencies
    'selenium',
    'selenium.webdriver',
    'selenium.webdriver.chrome.service',
    'selenium.webdriver.common.keys',
    'selenium.webdriver.common.by',
    'webdriver_manager',
    'webdriver_manager.chrome',
    'aiohttp',
    'asyncio',
    'logging',
    'json',
    'sqlite3',
    
    # Matplotlib
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.pyplot',
    'pyside6',
]

# Collect matplotlib data and binaries
tmp_ret = collect_all('matplotlib')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Collect selenium data just in case
tmp_ret_sel = collect_all('selenium')
datas += tmp_ret_sel[0]
binaries += tmp_ret_sel[1]
hiddenimports += tmp_ret_sel[2]

# Add cleanup for duplicates
hiddenimports = list(set(hiddenimports))

a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],  # Explicitly include current directory
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    console=False,  # GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
