import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from export_outline_mapping import build_mapping_records  # noqa: E402


class ExportOutlineMappingTest(unittest.TestCase):
    def test_build_mapping_records_keeps_chapter_trace_and_skips_t4(self):
        payload = {
            "records": [
                {
                    "title": "Paper A",
                    "source": "openalex",
                    "doi": "10.1/a",
                    "search_task_id": "S1",
                    "chapter_id": "2.1",
                    "chapter_title": "冷板优化方法",
                    "evidence_type": "method",
                    "paper_tier": "T2",
                    "score": "18",
                },
                {
                    "title": "Paper B",
                    "source": "crossref",
                    "doi": "10.1/b",
                    "paper_tier": "T4",
                },
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            rows = build_mapping_records(path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["search_task_id"], "S1")
        self.assertEqual(rows[0]["chapter_id"], "2.1")
        self.assertEqual(rows[0]["chapter_title"], "冷板优化方法")

