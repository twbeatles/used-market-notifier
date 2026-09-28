"""Regression: no Selector-loop forcing on Windows, no deprecated policy API (ISSUE-009)."""

import asyncio
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
EXCLUDED = {"tests", "legacy", ".venv", "build", "dist", ".tmp", "__pycache__"}


class EventLoopPolicyTest(unittest.TestCase):
    def test_source_does_not_use_event_loop_policy_api(self):
        offenders = []
        for path in REPO.rglob("*.py"):
            if EXCLUDED.intersection(path.relative_to(REPO).parts):
                continue
            text = path.read_text(encoding="utf-8")
            if "set_event_loop_policy" in text or "SelectorEventLoopPolicy" in text:
                offenders.append(str(path.relative_to(REPO)))
        self.assertEqual(offenders, [])

    def test_cli_keeps_default_loop(self):
        import main as app_main

        class _Engine:
            def __init__(self, *_args, **_kwargs):
                self.loop_type = None

            async def start(self):
                self.loop_type = type(asyncio.get_running_loop()).__name__

            async def close(self):
                return None

        engine_holder = {}

        def _make_engine(*args, **kwargs):
            engine_holder["engine"] = _Engine()
            return engine_holder["engine"]

        with mock.patch("monitor_engine.MonitorEngine", _make_engine):
            app_main.run_cli(settings_manager=mock.Mock())
        loop_type = engine_holder["engine"].loop_type
        if sys.platform == "win32":
            self.assertEqual(loop_type, "ProactorEventLoop")
        else:
            self.assertIsNotNone(loop_type)

    def test_monitor_thread_loop_supports_subprocesses_on_windows(self):
        try:
            from gui.main.threads import new_engine_event_loop
        except Exception as exc:  # pragma: no cover - GUI deps missing
            self.skipTest(f"GUI unavailable: {exc}")
        loop = new_engine_event_loop()
        try:
            if sys.platform == "win32":
                self.assertEqual(type(loop).__name__, "ProactorEventLoop")
        finally:
            loop.close()


if __name__ == "__main__":
    unittest.main()
