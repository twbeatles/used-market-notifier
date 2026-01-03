# -*- mode: python ; coding: utf-8 -*-
"""
Used Market Notifier v2.0 - PyInstaller Spec File
Optimized for lightweight build (~50-60MB)

Build: pyinstaller used_market_notifier.spec
Output: dist/중고거래알리미.exe
"""

import sys
from PyInstaller.utils.hooks import collect_submodules

APP_NAME = "중고거래알리미"
MAIN_SCRIPT = "main.py"

# Required hidden imports
hiddenimports = [
    # PyQt6 core
    'PyQt6.QtWidgets',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    
    # Async
    'asyncio',
    'aiohttp',
    
    # Playwright
    'playwright',
    'playwright.async_api',
    
    # Data
    'json',
    'sqlite3',
    'dataclasses',
    
    # Charts
    'matplotlib',
    'matplotlib.backends.backend_qtagg',
    
    # Export
    'openpyxl',
    
    # App modules
    'scrapers',
    'scrapers.playwright_base',
    'scrapers.stealth',
    'scrapers.debug',
    'scrapers.danggeun',
    'scrapers.bunjang',
    'scrapers.joonggonara',
    'notifiers',
    'notifiers.telegram_notifier',
    'notifiers.discord_notifier',
    'notifiers.slack_notifier',
    'gui',
    'gui.main_window',
    'gui.styles',
    'gui.components',
    'gui.keyword_manager',
]

# Exclude for smaller build
excludes = [
    # Test
    'pytest', 'unittest', 'test', 'tests',
    
    # Dev tools
    'pip', 'setuptools', 'wheel', 'pkg_resources', 'distutils',
    
    # Unused heavy
    'tkinter', 'tk', '_tkinter',
    'scipy', 'pandas', 'numpy.testing',
    'PIL', 'cv2',
    
    # Unused network
    'ftplib', 'imaplib', 'smtplib', 'telnetlib', 'xmlrpc',
    
    # Unused Qt
    'PyQt6.QtDesigner', 'PyQt6.QtHelp',
    'PyQt6.QtMultimedia', 'PyQt6.QtMultimediaWidgets',
    'PyQt6.QtNetwork', 'PyQt6.QtNetworkAuth',
    'PyQt6.QtOpenGL', 'PyQt6.QtOpenGLWidgets',
    'PyQt6.QtPositioning', 'PyQt6.QtPrintSupport',
    'PyQt6.QtQml', 'PyQt6.QtQuick', 'PyQt6.QtQuickWidgets',
    'PyQt6.QtRemoteObjects', 'PyQt6.QtSensors',
    'PyQt6.QtSerialPort', 'PyQt6.QtSpatialAudio',
    'PyQt6.QtSql', 'PyQt6.QtSvg', 'PyQt6.QtSvgWidgets',
    'PyQt6.QtTest', 'PyQt6.QtWebChannel',
    'PyQt6.QtWebEngineCore', 'PyQt6.QtWebEngineQuick',
    'PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebSockets',
    'PyQt6.QtXml',
    
    # Unused matplotlib
    'matplotlib.backends.backend_tkagg',
    'matplotlib.backends.backend_gtk3',
    'matplotlib.backends.backend_wx',
    
    # Old selenium
    'selenium', 'webdriver_manager',
    
    # Jupyter
    'IPython', 'jupyter', 'notebook',
]

# Binary patterns to exclude
binary_excludes = [
    'Qt6Designer*', 'Qt6Help*', 'Qt6Quick*',
    'Qt6Qml*', 'Qt6WebEngine*', 'Qt6Pdf*',
    'Qt6Multimedia*', 'Qt6Positioning*',
    'Qt6RemoteObjects*', 'Qt6Sensors*',
    'Qt6SerialPort*', 'Qt6Sql*', 'Qt6Svg*',
    'Qt6Test*', 'Qt6WebChannel*', 'Qt6WebSockets*',
    'opengl32sw*', 'd3dcompiler*',
]

a = Analysis(
    [MAIN_SCRIPT],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

# Filter binaries
import fnmatch
a.binaries = [b for b in a.binaries 
              if not any(fnmatch.fnmatch(b[0].lower(), p.lower()) for p in binary_excludes)]

# Filter data files
a.datas = [d for d in a.datas 
           if not any(x in d[0].lower() for x in ['test', 'example', 'sample', 'doc'])]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

import os
ICON_PATH = 'icon.ico' if os.path.exists('icon.ico') else None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # Disabled for Windows (no strip tool)
    upx=True,
    upx_exclude=['vcruntime140.dll', 'python*.dll', 'Qt6Core.dll', 'Qt6Gui.dll', 'Qt6Widgets.dll'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH,
)
