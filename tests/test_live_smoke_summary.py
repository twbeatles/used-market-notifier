import json
import tempfile
import unittest
from pathlib import Path

from scripts.live_smoke import write_summary_file


class TestLiveSmokeSummary(unittest.TestCase):
    def test_write_summary_file_writes_json(self):
        results = [
            {
                "platform": "danggeun",
                "ok": True,
                "artifact_base": "debug_output/live_smoke_danggeun_test",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "summary.json"
            write_summary_file(results, path)

            loaded = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(loaded, results)


if __name__ == "__main__":
    unittest.main()
