"""Shared external-link opening helpers for GUI widgets."""

from __future__ import annotations

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QMessageBox, QWidget


def _confirm_link_open_enabled(engine) -> bool:
    try:
        return bool(engine.settings.settings.confirm_link_open)
    except Exception:
        return True


def open_external_url(parent: QWidget | None, engine, url, label: str | None = None) -> bool:
    """Open an http(s) URL with shared confirmation and scheme checks."""
    url_text = str(url or "").strip()
    if not url_text:
        return False

    qurl = QUrl(url_text)
    scheme = qurl.scheme().lower()
    if scheme not in {"http", "https"}:
        QMessageBox.warning(parent, "링크 차단", f"지원하지 않는 링크 형식입니다.\n{url_text}")
        return False

    if _confirm_link_open_enabled(engine):
        display = label or url_text
        confirm = QMessageBox.question(
            parent,
            "링크 열기",
            f"다음 링크로 이동할까요?\n{display}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return False

    return bool(QDesktopServices.openUrl(qurl))
