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
  `notifier.log*`, `debug_output/`, and workspace-local temp dirs such as `.tmp/`
  are not bundled and remain local-only.
- Session-only CLI overrides such as `python main.py --headless` do not mutate
  packaged default settings; they only affect the current process.
- Scraper parser updates (2026-03) such as Danggeun slug/hash article IDs
  and Bunjang unknown-location normalization are runtime logic changes only
  and do not require additional PyInstaller hidden imports.
- Audit remediation updates (2026-04) keep Playwright-only environments
  import-safe when `selenium` is absent and add Bunjang detail-API enrichment
  through `aiohttp`, so async HTTP helper modules are collected explicitly.
- Shared seller-candidate scanning and Danggeun best-effort location warnings
  added during the 2026-04 audit pass are source/runtime behavior changes only
  and do not require additional PyInstaller hidden imports.
- The 2026-04 stabilization pass moved Playwright scrapers to an async
  start/search/enrich/close lifecycle with retained browser contexts. This is
  a source-level lifecycle change; Chromium runtime binaries are still not
  bundled and must be installed on target machines.
- URL normalization, schema-version metadata, notification skip telemetry, and
  field-level settings normalization use only the standard library and existing
  SQLite tables, so no extra bundled data files are required.
- The 2026-05 live-site stabilization pass adds shared pure parser helpers for
  Bunjang current/legacy cards, strict Joonggonara host/path validation, scrape
  quality gates, conditional metadata enrichment, platform backoff, and an
  enrichment TTL cache. These are source/runtime behavior changes using already
  collected modules and standard-library helpers.
- The 2026-06 package split keeps legacy import facades (`db.py`,
  `monitor_engine.py`, `settings_manager.py`, `scrapers/marketplace_parsers.py`,
  `backup_manager.py`, `playwright_base.py`, `gui/export_dialog.py`,
  `gui/compare_dialog.py`, `gui/favorites_widget.py`, `gui/main_window.py`,
  `gui/styles.py`, and major `gui/*_widget.py` modules) while moving canonical
  implementations into `storage/`, `engine/`, `app_settings/`, `backup/`,
  `scrapers/parsers/`, `scrapers/playwright/`, `gui/settings_panels/`,
  `gui/widgets/`, `gui/main/`, `gui/theme/`, `gui/components/`, `gui/export/`,
  `gui/compare/`, and `gui/widgets/favorites/`. The local packages are collected
- Follow-up SOLID split keeps the same facade pattern for `models/`,
  `message_templates/`, `auto_tagger/`, `backup/mixins/`,
  `engine/notification_sections/`, `storage/stats_sections/`,
  `gui/main/window_mixins/`, and `gui/theme/dark_sections/`
  (behavior-preserving; collected below the same way).
  explicitly below so onefile builds do not depend on facade-only discovery.
- Runtime backup ZIP archives still live under `backup/backup_*.zip` on disk, but
  that directory is also the Python package root for `BackupManager`; only ZIP
  snapshots are gitignored, not the package source.
- `scripts/live_smoke.py` is an opt-in development diagnostic for live site
  structure checks. It is not imported by the app entrypoint and is intentionally
  not bundled into the onefile executable.
- The Fluent shell is PySide6-only: `PySide6`, `PySide6-Fluent-Widgets`,
  `darkdetect` are collected and the `PyQt6`/`PyQt5` bindings are excluded so
  PyInstaller does not abort on mixed-hook collection. Build environments must
  not have `PyQt6-Fluent-Widgets` installed (see `gui/qt_binding.py`).
- New Fluent foundation modules (`gui/app.py`, `gui/qt_binding.py`,
  `gui/fluent_theme.py`, `gui/icon.py`, `gui/design_tokens.py`, `gui/pages/`) are
  collected with the other local split packages below.
- Static typing / encoding hygiene updates (2026-03) are source-level changes only
  and do not require PyInstaller hidden import adjustments.
- The updater (Ed25519 manifest, staged exe replace, --smoke rollback) lives in
  `updater/` and `version.py`. `cryptography` is collected explicitly. Chromium
  binaries are still not bundled. `--smoke` and `--apply-update` must stay on
  the frozen entry point so the helper process can verify and swap the exe.
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
    # PySide6 core (Fluent shell)
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "shiboken6",
    "qfluentwidgets",
    "qframelesswindow",
    "darkdetect",

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

    # Signed auto-update
    "cryptography",
    "cryptography.hazmat.primitives.asymmetric.ed25519",
    "cryptography.hazmat.primitives.serialization",
    "version",
    "updater",
    "updater.constants",
    "updater.manifest",
    "updater.installer",
    "updater.service",
    "updater.apply",
    "updater.smoke",
    "updater.atomic_io",
    "updater.process",
    "gui.update_workers",
    "gui.settings_panels.mixins.updater",
    "gui.main.window_mixins.updater",

    # App data root / single-instance guard (2026-09 audit remediation)
    "app_paths",
    "gui.single_instance",
    "gui.settings_panels.host",
    "storage.baselines",
    "app_settings.secrets",

    # Utilities
    "difflib",
    "importlib",
    "json",
    "logging",
    "re",
    "urllib.parse",
]

# Playwright imports can be dynamic; collect submodules defensively.
try:
    hiddenimports += collect_submodules("playwright")
except Exception:
    pass

# aiohttp and its helper packages may resolve parts of the stack lazily.
# Fluent webengine/multimedia subpackages are excluded: nothing imports them
# and they drag QtWebEngine/QtMultimedia (~100MB+) into the bundle.
_SKIP_COLLECT_PREFIXES = (
    "qfluentwidgets.multimedia",
    "qframelesswindow.webengine",
)
for package_name in ("aiohttp", "aiosignal", "frozenlist", "multidict", "yarl", "propcache", "cryptography", "updater", "qfluentwidgets", "qframelesswindow", "darkdetect"):
    try:
        hiddenimports += [
            module
            for module in collect_submodules(package_name)
            if not module.startswith(_SKIP_COLLECT_PREFIXES)
        ]
    except Exception:
        pass

# Local split packages are imported through compatibility facades in normal
# source runs. Collect them explicitly for packaging resilience.
for package_name in (
    "app_settings",
    "app_settings.mixins",
    "auto_tagger",
    "backup",
    "backup.mixins",
    "engine",
    "engine.notification_sections",
    "message_templates",
    "models",
    "storage",
    "storage.stats_sections",
    "scrapers.parsers",
    "gui.pages",
    "gui.settings_panels",
    "gui.settings_panels.mixins",
    "gui.widgets",
    "gui.widgets.listings.mixins",
    "gui.widgets.stats.mixins",
    "gui.main",
    "gui.main.window_mixins",
    "gui.theme",
    "gui.theme.dark_sections",
    "gui.components",
    "gui.export",
    "gui.compare",
    "gui.widgets.favorites",
    "gui.widgets.favorites.mixins",
    "scrapers.playwright",
    "scrapers.playwright.mixins",
):
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

        # Unused Qt modules (PySide6 build: exclude PySide6 counterparts;
        # measured imports are QtCore/QtGui/QtWidgets/QtSvg/QtSvgWidgets/QtXml)
        "PySide6.Qt3DAnimation",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DExtras",
        "PySide6.Qt3DInput",
        "PySide6.Qt3DLogic",
        "PySide6.Qt3DRender",
        "PySide6.QtBluetooth",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtDesigner",
        "PySide6.QtGraphs",
        "PySide6.QtHelp",
        "PySide6.QtHttpServer",
        "PySide6.QtLocation",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
        "PySide6.QtNetwork",
        "PySide6.QtNetworkAuth",
        "PySide6.QtNfc",
        "PySide6.QtOpenGL",
        "PySide6.QtOpenGLWidgets",
        "PySide6.QtPdf",
        "PySide6.QtPdfWidgets",
        "PySide6.QtPositioning",
        "PySide6.QtPrintSupport",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtQuickWidgets",
        "PySide6.QtQuick3D",
        "PySide6.QtRemoteObjects",
        "PySide6.QtScxml",
        "PySide6.QtSensors",
        "PySide6.QtSerialBus",
        "PySide6.QtSerialPort",
        "PySide6.QtSpatialAudio",
        "PySide6.QtSql",
        "PySide6.QtStateMachine",
        "PySide6.QtTest",
        "PySide6.QtTextToSpeech",
        "PySide6.QtWebChannel",
        "PySide6.QtWebEngine",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebSockets",
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
        "PyQt5",
        "PyQt5.sip",
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",

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

        # Conflicting Qt bindings (this build is PySide6-only)
        "tkinter",
        "wx",
        "PyQt6",
        "PyQt6.sip",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt5",
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
