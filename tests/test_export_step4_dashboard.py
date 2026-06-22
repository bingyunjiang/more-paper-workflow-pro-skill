import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from export_step4_dashboard import export_dashboard  # noqa: E402
from workflow_contracts import SearchResultRecord, write_workflow_json  # noqa: E402


class ExportStep4DashboardTest(unittest.TestCase):
    def test_export_dashboard_generates_static_site_and_preserves_review_fields(self):
        records = [
            SearchResultRecord.from_search_result({
                "title": "Bidirectional converter for V2G fast charging",
                "authors": ["Jiang Bingyun"],
                "year": "2026",
                "source": "openalex",
                "doi": "https://doi.org/10.1016/j.demo.2026.001",
                "article_url": "https://doi.org/10.1016/j.demo.2026.001",
                "search_task_id": "S1",
                "chapter_id": "ch2",
                "evidence_type": "method",
                "_score": "22",
                "_tier": "T1",
                "abstract": "A directly relevant abstract.",
                "oa_pdf_url": "https://example.org/demo.pdf",
                "paper_card": {
                    "evidence_role": "method",
                    "reading_depth": "abstract_only",
                    "content_fit": "direct",
                    "primary_claim": "Converter topology supports V2G fast charging.",
                },
            }),
            SearchResultRecord.from_search_result({
                "title": "充电桩与储能协同控制研究",
                "authors": "张三; 李四",
                "year": "2025",
                "source": "cnki",
                "article_url": "https://kns.cnki.net/kcms2/article/abstract?v=demo",
                "search_task_id": "S2",
                "chapter_id": "ch3",
                "evidence_type": "case",
                "_score": "16",
                "_tier": "T2",
                "abstract": "中文摘要。",
            }),
            SearchResultRecord.from_search_result({
                "title": "Temporary background paper",
                "source": "crossref",
                "doi": "10.5555/background",
                "_tier": "T3",
            }),
            SearchResultRecord.from_search_result({
                "title": "Off-topic wireless charging note",
                "source": "crossref",
                "doi": "10.5555/offtopic",
                "_tier": "T4",
            }),
        ]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = root / "workflow_search_results.json"
            out_dir = root / "step4-dashboard"
            write_workflow_json(workflow, records, {"query": "V2G fast charging"})

            result = export_dashboard(workflow, out_dir)

            self.assertEqual(result["records"], 4)
            self.assertEqual(result["included_t1_t3"], 3)
            self.assertEqual(result["excluded_t4"], 1)
            for rel in [
                "index.html",
                "styles.css",
                "app.js",
                "data/search-results.js",
                "data/dashboard-meta.js",
            ]:
                self.assertTrue((out_dir / rel).exists(), rel)

            data_js = (out_dir / "data" / "search-results.js").read_text(encoding="utf-8")
            self.assertIn("window.STEP4_SEARCH_RESULTS", data_js)
            self.assertIn("Off-topic wireless charging note", data_js)
            self.assertIn('"is_excluded": true', data_js)
            self.assertIn("充电桩与储能协同控制研究", data_js)
            self.assertIn("cnki.", data_js)
            self.assertIn("https://kns.cnki.net/kcms2/article/abstract", data_js)
            self.assertIn('"reading_depth": "metadata_only"', data_js)

            meta_text = (out_dir / "data" / "dashboard-meta.js").read_text(encoding="utf-8")
            self.assertIn('"authority": "display_layer_only"', meta_text)
            self.assertIn('"excluded_t4": 1', meta_text)
            self.assertIn('"source_artifact": "workflow_search_results.json"', meta_text)

            combined = "\n".join(
                path.read_text(encoding="utf-8")
                for path in [
                    out_dir / "index.html",
                    out_dir / "styles.css",
                    out_dir / "app.js",
                    out_dir / "data" / "search-results.js",
                    out_dir / "data" / "dashboard-meta.js",
                ]
            )
            for marker in ["????", "锟", "鐮", "浼", "寤", "璁", "鎽", "涓", "娑", "閻", "閸", "瀵"]:
                self.assertNotIn(marker, combined)

            # Ensure generated JavaScript payload remains parseable after the assignment prefix.
            payload = data_js.split("=", 1)[1].strip().rstrip(";")
            parsed = json.loads(payload)
            cnki = next(item for item in parsed if item["source"] == "cnki")
            self.assertTrue(cnki["source_id"].startswith("cnki."))
            self.assertEqual(cnki["download_hint"], "chinese_article_url")


if __name__ == "__main__":
    unittest.main()
