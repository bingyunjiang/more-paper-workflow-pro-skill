import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from export_outline_mapping import build_mapping_records  # noqa: E402
from workflow_contracts import SearchResultRecord, write_workflow_json, load_search_records  # noqa: E402


class MultiChapterMappingTest(unittest.TestCase):
    def test_workflow_roundtrip_preserves_secondary_chapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow.json"
            record = SearchResultRecord.from_search_result({
                "title": "Demo",
                "source": "openalex",
                "doi": "10.1/demo",
                "chapter_id": "2.1",
                "chapter_title": "方法",
                "secondary_chapter_ids": ["2.2", "2.3"],
                "secondary_chapter_titles": ["性能", "应用"],
            })
            write_workflow_json(path, [record], {})
            loaded = load_search_records(path)

        self.assertEqual(loaded[0].chapter_id, "2.1")
        self.assertEqual(loaded[0].secondary_chapter_ids, ["2.2", "2.3"])
        self.assertEqual(loaded[0].secondary_chapter_titles, ["性能", "应用"])

    def test_outline_mapping_exports_secondary_columns(self):
        payload = {
            "records": [
                {
                    "title": "Paper A",
                    "source": "openalex",
                    "doi": "10.1/a",
                    "chapter_id": "2.1",
                    "chapter_title": "方法",
                    "search_task_id": "S1",
                    "secondary_chapter_ids": ["2.2"],
                    "secondary_chapter_titles": ["性能"],
                    "paper_tier": "T2",
                    "score": "18",
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            rows = build_mapping_records(path)

        self.assertEqual(rows[0]["secondary_chapter_ids"], ["2.2"])
        self.assertEqual(rows[0]["secondary_chapter_titles"], ["性能"])


if __name__ == "__main__":
    unittest.main()
