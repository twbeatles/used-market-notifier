# -*- mode: python ; coding: utf-8 -*-
"""
UsedMarketNotifier - PyInstaller Spec (OneFile)
Fixed for numpy/matplotlib compatibility
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # PyQt6
        'PyQt6.sip',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        # Numpy - all required submodules
        'numpy',
        'numpy.core',
        'numpy.core._multiarray_umath',
        'numpy._core',
        'numpy._core._multiarray_umath', 
        'numpy._core.multiarray',
        'numpy._core._dtype_ctypes',
        'numpy._pytesttester',
        'numpy.random',
        'numpy.linalg',
        'numpy.fft',
        # Matplotlib
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends.backend_qtagg',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.figure',
        # Database
        'sqlite3',
        # Async
        'asyncio',
        'aiohttp',
        # Excel
        'openpyxl',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Test frameworks
        'pytest', 'unittest', 'nose', '_pytest',
        # Development tools
        'setuptools', 'pip', 'wheel',
        # Unused Qt modules
        'PyQt6.QtBluetooth', 'PyQt6.QtDBus', 'PyQt6.QtDesigner',
        'PyQt6.QtHelp', 'PyQt6.QtMultimedia', 'PyQt6.QtMultimediaWidgets',
        'PyQt6.QtNfc', 'PyQt6.QtOpenGL',
        'PyQt6.QtPositioning', 'PyQt6.QtQml',
        'PyQt6.QtQuick', 'PyQt6.QtQuickWidgets', 'PyQt6.QtRemoteObjects',
        'PyQt6.QtSensors', 'PyQt6.QtSerialPort', 'PyQt6.QtSql',
        'PyQt6.QtTest', 'PyQt6.QtWebChannel',
        'PyQt6.QtWebEngine', 'PyQt6.QtWebEngineCore', 'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebSockets', 'PyQt6.QtXml',
        # Unused matplotlib backends
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends.backend_wxagg',
        'tkinter', 'wx',
        # Large unused packages
        'pandas', 'scipy', 'IPython', 'jupyter', 'notebook',
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# OneFile EXE
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
    strip=False,  # Don't strip - can cause numpy issues
    upx=True,
    upx_exclude=[
        'vcruntime140.dll',
        'python*.dll',
        'Qt6Core.dll',
        'Qt6Gui.dll',
        'Qt6Widgets.dll',
        'numpy*',
    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
