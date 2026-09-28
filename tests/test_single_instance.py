"""Regression: only one GUI instance may run per data folder."""

import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _pyside_available() -> bool:
    try:
        from PySide6.QtCore import QLockFile  # noqa: F401
    except Exception:
        return False
    return True


@unittest.skipUnless(_pyside_available(), "requires PySide6")
class SingleInstanceGuardTest(unittest.TestCase):
    def test_second_guard_cannot_acquire_while_first_holds_lock(self):
        from gui.single_instance import LOCK_FILE_NAME, SingleInstanceGuard

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, LOCK_FILE_NAME)
            first = SingleInstanceGuard(path)
            second = SingleInstanceGuard(path)
            self.assertTrue(first.acquire())
            self.assertFalse(second.acquire(timeout_ms=50))
            first.release()
            self.assertTrue(second.acquire())
            second.release()

    def test_multi_instance_override(self):
        from unittest import mock

        from gui import app as gui_app

        with mock.patch.dict(os.environ, {"USED_NOTIFIER_ALLOW_MULTI": "1"}):
            self.assertIsNotNone(gui_app._acquire_single_instance())


if __name__ == "__main__":
    unittest.main()
