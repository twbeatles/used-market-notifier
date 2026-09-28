"""Regression: data paths independent of the launch directory, resilient logging (ISSUE-010)."""

import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import app_paths
import main as app_main


class AppPathsTest(unittest.TestCase):
    def test_source_root_is_repository_folder(self):
        self.assertEqual(app_paths.app_root(), Path(app_main.__file__).resolve().parent)

    def test_frozen_root_is_executable_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "UsedMarketNotifier.exe"
            with mock.patch.object(sys, "frozen", True, create=True), \
                    mock.patch.object(sys, "executable", str(exe)):
                self.assertEqual(app_paths.app_root(), exe.resolve().parent)

    def test_ensure_app_root_cwd_switches_directory(self):
        old = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            try:
                os.chdir(tmp)
                root = app_paths.ensure_app_root_cwd()
                self.assertEqual(Path(os.getcwd()).resolve(), root.resolve())
            finally:
                os.chdir(old)


class SetupLoggingTest(unittest.TestCase):
    def setUp(self):
        self._root_handlers = list(logging.getLogger().handlers)
        self._excepthook = sys.excepthook

    def tearDown(self):
        root = logging.getLogger()
        for handler in list(root.handlers):
            root.removeHandler(handler)
            try:
                handler.close()
            except Exception:
                pass
        for handler in self._root_handlers:
            root.addHandler(handler)
        sys.excepthook = self._excepthook

    def test_unwritable_log_path_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad_path = os.path.join(tmp, "missing-dir", "notifier.log")  # parent does not exist
            app_main.setup_logging(bad_path)  # must not raise
            self.assertFalse(
                any(isinstance(h, logging.FileHandler) for h in logging.getLogger().handlers)
            )

    def test_no_console_in_windowed_build(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(sys, "stdout", None):
            app_main.setup_logging(os.path.join(tmp, "notifier.log"))
            handlers = logging.getLogger().handlers
            self.assertTrue(any(isinstance(h, logging.FileHandler) for h in handlers))
            self.assertFalse(any(type(h) is logging.StreamHandler for h in handlers))
            for handler in list(handlers):
                handler.close()


if __name__ == "__main__":
    unittest.main()
