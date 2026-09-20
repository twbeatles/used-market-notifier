"""Clipboard helper (Qt preferred, pyperclip fallback)."""


def copy_text_to_clipboard(text: str) -> bool:
    """
    Copy text to system clipboard.

    Returns:
        True if successful, False otherwise
    """
    try:
        from PyQt6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        if clipboard is None:
            return False
        clipboard.setText(text)
        return True
    except Exception:
        # Fallback for non-PyQt environments
        try:
            import importlib

            pyperclip = importlib.import_module("pyperclip")
            copy_fn = getattr(pyperclip, "copy", None)
            if not callable(copy_fn):
                return False
            copy_fn(text)
            return True
        except ImportError:
            pass
    return False


__all__ = ["copy_text_to_clipboard"]
