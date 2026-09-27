"""앱 아이콘 조회. 번들 아이콘이 없으면 빈 QIcon을 돌려준다."""

from __future__ import annotations

from PySide6.QtGui import QIcon


def get_app_icon() -> QIcon:
    return QIcon()


__all__ = ["get_app_icon"]
