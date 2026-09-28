"""Protect notifier secrets (bot tokens, webhook URLs) in settings.json.

On Windows, values are encrypted with DPAPI (bound to the current Windows user)
and stored as ``dpapi:v1:<base64>``. Plain values from older settings files are
still read as-is and get encrypted on the next save. Other platforms keep the
previous plaintext behavior.
"""

from __future__ import annotations

import base64
import logging
import sys

PREFIX = "dpapi:v1:"
_ENTROPY = b"UsedMarketNotifier.v1"
_CRYPTPROTECT_UI_FORBIDDEN = 0x1

logger = logging.getLogger("SettingsSecrets")


def dpapi_available() -> bool:
    return sys.platform == "win32"


def _dpapi(data: bytes, protect: bool) -> bytes:
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    def _blob(raw: bytes) -> tuple[DATA_BLOB, ctypes.Array]:
        buffer = ctypes.create_string_buffer(raw, len(raw))
        return DATA_BLOB(len(raw), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))), buffer

    windll = getattr(ctypes, "windll")
    crypt32 = windll.crypt32
    kernel32 = windll.kernel32
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p

    in_blob, _in_buf = _blob(data)
    entropy_blob, _entropy_buf = _blob(_ENTROPY)
    out_blob = DATA_BLOB()
    func = crypt32.CryptProtectData if protect else crypt32.CryptUnprotectData
    ok = func(
        ctypes.byref(in_blob),
        None,
        ctypes.byref(entropy_blob),
        None,
        None,
        _CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(out_blob),
    )
    if not ok:
        raise OSError(ctypes.get_last_error() or "DPAPI call failed")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(out_blob.pbData, ctypes.c_void_p))


def is_protected(value: str | None) -> bool:
    return bool(value) and str(value).startswith(PREFIX)


def protect_secret(value: str | None) -> str:
    """Encrypt a secret for storage. Empty values and non-Windows stay plaintext."""
    text = str(value or "")
    if not text or is_protected(text) or not dpapi_available():
        return text
    try:
        return PREFIX + base64.b64encode(_dpapi(text.encode("utf-8"), protect=True)).decode("ascii")
    except Exception as exc:
        # Never lose the value because encryption failed; keep previous behavior.
        logger.warning(f"Secret encryption unavailable, storing as plain text: {exc}")
        return text


def unprotect_secret(value: str | None) -> tuple[str, bool]:
    """Return ``(plaintext, ok)``. ``ok`` is False when an encrypted value cannot be decrypted
    (e.g. settings copied from another Windows account or PC)."""
    text = str(value or "")
    if not is_protected(text):
        return text, True
    if not dpapi_available():
        return "", False
    try:
        raw = base64.b64decode(text[len(PREFIX):], validate=True)
        return _dpapi(raw, protect=False).decode("utf-8"), True
    except Exception as exc:
        logger.warning(f"Secret decryption failed: {exc}")
        return "", False


__all__ = ["PREFIX", "dpapi_available", "is_protected", "protect_secret", "unprotect_secret"]
