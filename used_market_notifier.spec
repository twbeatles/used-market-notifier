# -*- mode: python ; coding: utf-8 -*-
"""
UsedMarketNotifier - Optimized OneFile Build
경량화된 단일 실행 파일 빌드 설정

빌드 명령:
    pyinstaller used_market_notifier.spec

특징:
    - 단일 EXE 파일 생성
    - UPX 압축으로 파일 크기 최소화
    - 불필요한 패키지/모듈 제외
    - Selenium/PyQt6 최적화
"""

import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Selenium webdriver-manager 데이터 수집
datas = []
try:
    datas += collect_data_files('webdriver_manager')
except Exception:
    pass

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # === PyQt6 Core ===
        'PyQt6.sip',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        
        # === Selenium ===
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'webdriver_manager.chrome',
        
        # === Database ===
        'sqlite3',
        
        # === Async/HTTP ===
        'asyncio',
        'aiohttp',
        
        # === Data Export ===
        'openpyxl',
        'openpyxl.workbook',
        'openpyxl.worksheet',
        
        # === Utilities ===
        'difflib',
        'json',
        'logging',
        're',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # === Test Frameworks ===
        'pytest', 'unittest', 'nose', '_pytest',
        'hypothesis', 'coverage', 'mock',
        
        # === Development Tools ===
        'setuptools', 'pip', 'wheel', 'pkg_resources',
        'distutils', 'ensurepip',
        
        # === Unused Qt Modules (대폭 제외) ===
        'PyQt6.QtBluetooth',
        'PyQt6.QtDBus',
        'PyQt6.QtDesigner',
        'PyQt6.QtHelp',
        'PyQt6.QtMultimedia',
        'PyQt6.QtMultimediaWidgets',
        'PyQt6.QtNetwork3D',
        'PyQt6.QtNfc',
        'PyQt6.QtOpenGL',
        'PyQt6.QtOpenGLWidgets',
        'PyQt6.QtPdf',
        'PyQt6.QtPdfWidgets',
        'PyQt6.QtPositioning',
        'PyQt6.QtPrintSupport',
        'PyQt6.QtQml',
        'PyQt6.QtQuick',
        'PyQt6.QtQuickWidgets',
        'PyQt6.QtQuick3D',
        'PyQt6.QtRemoteObjects',
        'PyQt6.QtSensors',
        'PyQt6.QtSerialPort',
        'PyQt6.QtSpatialAudio',
        'PyQt6.QtSql',
        'PyQt6.QtSvg',
        'PyQt6.QtSvgWidgets',
        'PyQt6.QtTest',
        'PyQt6.QtTextToSpeech',
        'PyQt6.QtWebChannel',
        'PyQt6.QtWebEngine',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebSockets',
        'PyQt6.QtXml',
        
        # === Heavy Unused Packages ===
        'numpy',
        'pandas',
        'scipy',
        'matplotlib',
        'PIL',
        'cv2',
        'tensorflow',
        'torch',
        'sklearn',
        
        # === GUI Toolkits (사용 안함) ===
        'tkinter',
        'wx',
        'PySide6',
        'PySide2',
        
        # === Development/Debugging ===
        'IPython',
        'jupyter',
        'notebook',
        'debugpy',
        
        # === Playwright (Selenium 사용) ===
        'playwright',
    ],
    noarchive=False,
    optimize=2,  # 최적화 레벨 2 (더 강한 최적화)
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# === OneFile EXE Build ===
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
    strip=False,  # Windows에서 strip 비활성화 (호환성)
    upx=True,     # UPX 압축 활성화
    upx_exclude=[
        # UPX 압축 제외 (호환성 문제 방지)
        'vcruntime140.dll',
        'vcruntime140_1.dll',
        'msvcp140.dll',
        'python*.dll',
        'Qt6Core.dll',
        'Qt6Gui.dll', 
        'Qt6Widgets.dll',
        'api-ms-*.dll',
    ],
    runtime_tmpdir=None,
    console=False,  # GUI 앱 (콘솔 창 없음)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 아이콘 파일 경로 (예: 'icon.ico')
    version=None,  # 버전 정보 파일 (예: 'version.txt')
)
