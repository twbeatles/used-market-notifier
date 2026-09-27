"""qfluentwidgets / qframelesswindow가 PySide6 바인딩인지 검증.

user site에 PyQt6-Fluent-Widgets가 설치되면 PySide6-Fluent-Widgets를
가려 frozen GUI가 ``No module named 'PyQt6'``로 죽는다.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
from dataclasses import dataclass
from pathlib import Path

CONFLICTING_DIST_NAMES: frozenset[str] = frozenset(
    {
        "pyqt6-fluent-widgets",
        "pyqt5-fluent-widgets",
        "pyqt-fluent-widgets",
        "pyqt6-frameless-window",
        "pyqt5-frameless-window",
    }
)

_FIX_HINT = (
    "해결:\n"
    "  pip uninstall PyQt6-Fluent-Widgets PyQt6-Frameless-Window "
    "PyQt5-Fluent-Widgets PyQt5-Frameless-Window\n"
    '  pip install -e ".[gui,build]"'
)


def binding_from_source(text: str) -> str:
    """소스에서 Qt 바인딩 이름을 식별한다."""
    if "from PyQt6" in text or "import PyQt6" in text:
        return "PyQt6"
    if "from PyQt5" in text or "import PyQt5" in text:
        return "PyQt5"
    if "from PySide6" in text or "import PySide6" in text:
        return "PySide6"
    if "from PySide2" in text or "import PySide2" in text:
        return "PySide2"
    return "unknown"


def is_pyside6_binding(name: str) -> bool:
    return name == "PySide6"


def fluent_binding_accepted(report: QtBindingReport) -> bool:
    """MainWindow 진입 가드 판정.

    frozen onefile(PYZ 아카이브)에서는 소스 파일 판독이 불가해 report가
    ``ok=True, skipped=True, fluent_binding=None`` 으로 돌아온다. 이 경우
    ``import qfluentwidgets`` 자체가 이미 성공한 상태이므로 허용한다.
    (PyQt 바인딩 트리가 번들됐다면 import 단계에서 먼저 ImportError가 난다.)
    소스 실행 환경에서는 fluent_binding이 반드시 판독되므로 PySide6만 허용.
    """
    if not report.ok:
        return False
    if report.fluent_binding is None:
        return True
    return is_pyside6_binding(report.fluent_binding)


@dataclass(frozen=True)
class QtBindingReport:
    ok: bool
    skipped: bool
    errors: tuple[str, ...]
    fluent_path: str | None
    fluent_binding: str | None
    frameless_path: str | None
    frameless_binding: str | None
    conflicting_dists: tuple[str, ...]


def non_user_site_packages() -> list[Path]:
    """PYTHONNOUSERSITE=1 때처럼 user site를 제외한 site-packages."""
    import site

    user = Path(site.getusersitepackages()).resolve()
    roots: list[Path] = []
    seen: set[Path] = set()
    for base in site.getsitepackages():
        root = Path(base).resolve()
        if root == user or user in root.parents:
            continue
        if root not in seen and root.is_dir():
            seen.add(root)
            roots.append(root)
    return roots


def _pkg_file(root: Path, *parts: str) -> Path | None:
    path = root.joinpath(*parts)
    return path if path.is_file() else None


def _resolved_source(module_name: str, *, ignore_user_site: bool) -> Path | None:
    if ignore_user_site:
        rel = {
            "qfluentwidgets": ("qfluentwidgets", "common", "config.py"),
            "qframelesswindow": ("qframelesswindow", "__init__.py"),
        }.get(module_name)
        if rel is None:
            return None
        for root in non_user_site_packages():
            found = _pkg_file(root, *rel)
            if found is not None:
                return found
        return None

    spec = importlib.util.find_spec(module_name)
    if spec is None or not spec.origin:
        return None
    origin = Path(spec.origin)
    # PyInstaller onefile: origin이 _MEI... 가상경로일 수 있다.
    if module_name == "qfluentwidgets":
        cfg = origin.parent / "common" / "config.py"
        if cfg.is_file():
            return cfg
    return origin if origin.is_file() else None


def installed_conflicting_dists() -> tuple[str, ...]:
    names: list[str] = []
    seen: set[str] = set()
    for dist in importlib.metadata.distributions():
        raw = str(dist.metadata["Name"] or "")
        if not raw:
            continue
        key = raw.lower()
        if key in CONFLICTING_DIST_NAMES and key not in seen:
            seen.add(key)
            names.append(raw)
    return tuple(sorted(names, key=str.lower))


def inspect_gui_qt_bindings(
    *,
    ignore_user_site: bool = False,
    check_conflicting_dists: bool = True,
) -> QtBindingReport:
    """현재 해석되는 Fluent/Frameless 패키지가 PySide6용인지 검사."""
    fluent_path = _resolved_source("qfluentwidgets", ignore_user_site=ignore_user_site)
    frameless_path = _resolved_source("qframelesswindow", ignore_user_site=ignore_user_site)
    conflicts = installed_conflicting_dists() if check_conflicting_dists else ()

    if fluent_path is None and frameless_path is None and not conflicts:
        return QtBindingReport(
            ok=True,
            skipped=True,
            errors=(),
            fluent_path=None,
            fluent_binding=None,
            frameless_path=None,
            frameless_binding=None,
            conflicting_dists=(),
        )

    errors: list[str] = []
    fluent_binding: str | None = None
    frameless_binding: str | None = None

    if fluent_path is not None:
        fluent_binding = binding_from_source(
            fluent_path.read_text(encoding="utf-8", errors="replace")
        )
        if not is_pyside6_binding(fluent_binding):
            errors.append(
                f"qfluentwidgets가 {fluent_binding} 바인딩입니다: {fluent_path}"
            )
    elif not ignore_user_site:
        errors.append("qfluentwidgets를 찾을 수 없습니다 (PySide6-Fluent-Widgets 필요).")

    if frameless_path is not None:
        frameless_binding = binding_from_source(
            frameless_path.read_text(encoding="utf-8", errors="replace")
        )
        if not is_pyside6_binding(frameless_binding):
            errors.append(
                f"qframelesswindow가 {frameless_binding} 바인딩입니다: {frameless_path}"
            )

    if conflicts:
        errors.append("충돌 패키지 설치됨: " + ", ".join(conflicts))

    return QtBindingReport(
        ok=not errors,
        skipped=False,
        errors=tuple(errors),
        fluent_path=str(fluent_path) if fluent_path else None,
        fluent_binding=fluent_binding,
        frameless_path=str(frameless_path) if frameless_path else None,
        frameless_binding=frameless_binding,
        conflicting_dists=conflicts,
    )


def format_gui_qt_binding_error(report: QtBindingReport) -> str:
    lines = [
        "중고거래 알리미 GUI는 PySide6-Fluent-Widgets가 필요합니다.",
        ("PyQt6-Fluent-Widgets가 같은 환경에 있으면 "
        "``No module named 'PyQt6'``로 실행·빌드가 실패합니다."),
        "",
        *report.errors,
        "",
        _FIX_HINT,
    ]
    return "\n".join(lines)


__all__ = [
    "CONFLICTING_DIST_NAMES",
    "QtBindingReport",
    "binding_from_source",
    "fluent_binding_accepted",
    "format_gui_qt_binding_error",
    "inspect_gui_qt_bindings",
    "installed_conflicting_dists",
    "is_pyside6_binding",
]
