import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from export_chinese_metadata import export_chinese_records  # noqa: E402


class ExportChineseMetadataTest(unittest.TestCase):
    def test_export_chinese_records_prefers_full_fields(self):
        payload = {
            "records": [
                {
                    "title": "液冷板在电池侧面换热中的应用",
                    "source": "cnki",
                    "source_id": "cnki.abc123",
                    "article_url": "https://kns.cnki.net/kcms2/article/abstract?v=demo",
                    "authors": ["张三", "李四"],
                    "year": "2026",
                    "abstract": "完整中文摘要",
                    "paper_tier": "T3",
                    "score": "14",
                    "raw": {"publication_title": "汽车工程", "record_id": "rec-1", "citekey": "CNKI2026_cnkiabc123"},
                },
                {
                    "title": "English paper",
                    "source": "openalex",
                    "doi": "10.1/demo",
                },
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            exported = export_chinese_records(path)

        self.assertEqual(len(exported), 1)
        row = exported[0]
        self.assertEqual(row["source"], "cnki")
        self.assertEqual(row["publication_title"], "汽车工程")
        self.assertEqual(row["abstract"], "完整中文摘要")
        self.assertEqual(row["language"], "zh-CN")
        self.assertEqual(row["citekey"], "CNKI2026_cnkiabc123")


if __name__ == "__main__":
    unittest.main()
