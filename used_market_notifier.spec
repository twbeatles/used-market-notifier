# -*- mode: python ; coding: utf-8 -*-
"""
UsedMarketNotifier - optimized onefile build configuration.

Build command:
    pyinstaller used_market_notifier.spec

Notes:
- This spec bundles Python modules for both Selenium and Playwright paths.
- Playwright Chromium runtime binaries are not bundled in the EXE.
  Install them on target machines with: `python -m playwright install chromium`.
- `matplotlib` is intentionally excluded to keep onefile size small.
  Chart widgets degrade gracefully to a fallback label when matplotlib is unavailable.
- Runtime-local recovery artifacts such as `settings.broken-*.json`, `backup/`,
  `notifier.log*`, and `debug_output/` are not bundled and remain local-only.
- Session-only CLI overrides such as `python main.py --headless` do not mutate
  packaged default settings; they only affect the current process.
- Scraper parser updates (2026-03) such as Danggeun slug/hash article IDs
  and Bunjang unknown-location normalization are runtime logic changes only
  and do not require additional PyInstaller hidden imports.
- Audit remediation updates (2026-04) keep Playwright-only environments
  import-safe when `selenium` is absent and add Bunjang detail-API enrichment
  through `aiohttp`, so async HTTP helper modules are collected explicitly.
- Static typing / encoding hygiene updates (2026-03) are source-level changes only
  and do not require PyInstaller hidden import adjustments.
- Data-integrity features added in 2026-03 (metadata enrichment, delivery logs,
  sale-status history, settings recovery) are source/database changes only and
  do not require extra PyInstaller hidden imports.
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Data files required by webdriver_manager and Playwright packages.
datas = []
try:
    datas += collect_data_files("webdriver_manager")
except Exception:
    pass

try:
    datas += collect_data_files("playwright")
except Exception:
    pass

hiddenimports = [
    # PyQt6 core
    "PyQt6.sip",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",

    # Selenium
    "selenium",
    "selenium.webdriver",
    "selenium.webdriver.chrome",
    "selenium.webdriver.chrome.service",
    "selenium.webdriver.chrome.options",
    "selenium.webdriver.common.by",
    "selenium.webdriver.support.ui",
    "selenium.webdriver.support.expected_conditions",
    "webdriver_manager.chrome",

    # Playwright
    "playwright",
    "playwright.async_api",
    "playwright.sync_api",
    "pyee",
    "greenlet",

    # Database
    "sqlite3",

    # Async / HTTP
    "asyncio",
    "aiohttp",
    "aiosignal",
    "frozenlist",
    "multidict",
    "yarl",
    "propcache",

    # Data export
    "openpyxl",
    "openpyxl.workbook",
    "openpyxl.worksheet",

    # Utilities
    "difflib",
    "json",
    "logging",
    "re",
]

# Playwright imports can be dynamic; collect submodules defensively.
try:
    hiddenimports += collect_submodules("playwright")
except Exception:
    pass

# aiohttp and its helper packages may resolve parts of the stack lazily.
for package_name in ("aiohttp", "aiosignal", "frozenlist", "multidict", "yarl", "propcache"):
    try:
        hiddenimports += collect_submodules(package_name)
    except Exception:
        pass

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Test frameworks
        "pytest", "unittest", "nose", "_pytest",
        "hypothesis", "coverage", "mock",

        # Development tools
        "setuptools", "pip", "wheel", "pkg_resources",
        "distutils", "ensurepip",

        # Unused Qt modules
        "PyQt6.QtBluetooth",
        "PyQt6.QtDBus",
        "PyQt6.QtDesigner",
        "PyQt6.QtHelp",
        "PyQt6.QtMultimedia",
        "PyQt6.QtMultimediaWidgets",
        "PyQt6.QtNetwork3D",
        "PyQt6.QtNfc",
        "PyQt6.QtOpenGL",
        "PyQt6.QtOpenGLWidgets",
        "PyQt6.QtPdf",
        "PyQt6.QtPdfWidgets",
        "PyQt6.QtPositioning",
        "PyQt6.QtPrintSupport",
        "PyQt6.QtQml",
        "PyQt6.QtQuick",
        "PyQt6.QtQuickWidgets",
        "PyQt6.QtQuick3D",
        "PyQt6.QtRemoteObjects",
        "PyQt6.QtSensors",
        "PyQt6.QtSerialPort",
        "PyQt6.QtSpatialAudio",
        "PyQt6.QtSql",
        "PyQt6.QtSvg",
        "PyQt6.QtSvgWidgets",
        "PyQt6.QtTest",
        "PyQt6.QtTextToSpeech",
        "PyQt6.QtWebChannel",
        "PyQt6.QtWebEngine",
        "PyQt6.QtWebEngineCore",
        "PyQt6.QtWebEngineWidgets",
        "PyQt6.QtWebSockets",
        "PyQt6.QtXml",

        # Heavy unused packages
        "numpy",
        "pandas",
        "scipy",
        "matplotlib",
        "PIL",
        "cv2",
        "tensorflow",
        "torch",
        "sklearn",

        # Other GUI toolkits
        "tkinter",
        "wx",
        "PySide6",
        "PySide2",

        # Dev/debug tools
        "IPython",
        "jupyter",
        "notebook",
        "debugpy",

        # Local-only source trees
        "tests",
        "legacy",
    ],
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="UsedMarketNotifier",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        "vcruntime140.dll",
        "vcruntime140_1.dll",
        "msvcp140.dll",
        "python*.dll",
        "Qt6Core.dll",
        "Qt6Gui.dll",
        "Qt6Widgets.dll",
        "api-ms-*.dll",
    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version=None,
)
