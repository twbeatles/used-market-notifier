"""CLI --smoke, --version, 헬퍼 부모 대기."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from updater.apply import handle_apply_update
from updater.installer import consume_update_result
from updater.smoke import SMOKE_MODULES, run_smoke_check
from version import __version__

ROOT = Path(__file__).resolve().parent.parent


class TestUpdaterCli(unittest.TestCase):
    def test_run_smoke_check_loads_core_modules(self):
        self.assertIn("monitor_engine", SMOKE_MODULES)
        self.assertIn("updater.service", SMOKE_MODULES)
        self.assertNotIn("gui.main_window", SMOKE_MODULES)
        self.assertEqual(run_smoke_check(), 0)

    def test_cli_smoke(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "main.py"), "--smoke"],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(ROOT),
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("smoke check OK", completed.stdout)

    def test_cli_version(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "main.py"), "--version"],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(ROOT),
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(f"v{__version__}", completed.stdout)

    def test_handle_apply_update_parent_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result_file = root / "result.json"
            args = argparse.Namespace(
                update_target=str(root / "target.exe"),
                update_staged=str(root / "staged.exe"),
                update_backup=str(root / "backup.exe"),
                update_parent_pid=999999,
                update_expected_sha256="0" * 64,
                update_expected_size=100,
                update_result_file=str(result_file),
            )
            with patch("updater.apply.is_process_running", return_value=True), patch(
                "updater.apply.time.sleep",
                return_value=None,
            ):
                code = handle_apply_update(args)
            self.assertEqual(code, 1)
            result = consume_update_result(result_file)
            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result["status"], "failed")
            self.assertIn("초과", str(result["error"]))


if __name__ == "__main__":
    unittest.main()
