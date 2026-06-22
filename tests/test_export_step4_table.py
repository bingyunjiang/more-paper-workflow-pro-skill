import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from export_step4_table import build_manifest, build_markdown_table, main  # noqa: E402
from workflow_contracts import SearchResultRecord, write_workflow_json  # noqa: E402


class ExportStep4TableTest(unittest.TestCase):
    def test_build_markdown_table_filters_t4_and_keeps_required_sections(self):
        records = [
            SearchResultRecord.from_search_result({
                "title": "Topology optimization of cold plate for battery thermal management",
                "authors": ["Wang Lei", "Li Ming"],
                "year": "2025",
                "source": "openalex",
                "doi": "10.1016/j.demo.2025.0001",
                "_score": "20",
                "_tier": "T1",
                "tier": "standard",
                "abstract": "Directly relevant abstract.",
                "paper_card": {"evidence_role": "method", "content_fit": "direct", "reading_depth": "abstract_only"},
            }),
            SearchResultRecord.from_search_result({
                "title": "Off-topic paper",
                "source": "crossref",
                "doi": "10.1016/j.demo.2024.0002",
                "_score": "10",
                "_tier": "T4",
            }),
        ]

        markdown = build_markdown_table(records, {"query": "冷板拓扑优化", "t1": "openalex", "t2": "crossref"})

        self.assertIn("## 检索概况", markdown)
        self.assertIn("## 筛选依据", markdown)
        self.assertIn("record_id", markdown)
        self.assertIn("citekey", markdown)
        self.assertIn("Topology optimization of cold plate", markdown)
        self.assertNotIn("Off-topic paper", markdown)

    def test_build_manifest_uses_filtered_counts_and_sources(self):
        records = [
            SearchResultRecord.from_search_result({
                "title": "A",
                "source": "openalex",
                "doi": "10.1/a",
                "_tier": "T1",
                "search_task_id": "S1",
                "abstract": "x",
            }),
            SearchResultRecord.from_search_result({
                "title": "B",
                "source": "crossref",
                "doi": "10.1/b",
                "_tier": "T3",
                "search_task_id": "S1",
            }),
            SearchResultRecord.from_search_result({
                "title": "C",
                "source": "crossref",
                "doi": "10.1/c",
                "_tier": "T4",
                "search_task_id": "S2",
            }),
        ]

        manifest = build_manifest(records, Path("workflow_search_results.json"), Path("检索文献表.md"))
        payload = json.loads(json.dumps(manifest.__dict__, ensure_ascii=False))

        self.assertEqual(payload["schema_version"], "retrieval-index.v1")
        self.assertEqual(payload["record_count"], 2)
        self.assertEqual(payload["source_count"], 2)
        self.assertIn("workflow_search_results.json", payload["source_artifacts"])
        self.assertIn("检索文献表.xlsx", payload["source_artifacts"])
        self.assertIn("t4_records_excluded_from_display_layer", payload["warnings"])

    def test_cli_exports_dashboard_by_default(self):
        records = [
            SearchResultRecord.from_search_result({
                "title": "V2G charging control",
                "source": "openalex",
                "doi": "10.1/v2g",
                "_tier": "T1",
                "search_task_id": "S1",
            }),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = root / "workflow_search_results.json"
            output_md = root / "检索文献表.md"
            manifest = root / "retrieval_index_manifest.json"
            write_workflow_json(workflow, records, {"query": "V2G"})

            old_argv = sys.argv
            try:
                sys.argv = [
                    "export_step4_table.py",
                    "--workflow-inputs",
                    str(workflow),
                    "--output-md",
                    str(output_md),
                    "--output-manifest",
                    str(manifest),
                ]
                main()
            finally:
                sys.argv = old_argv

            self.assertTrue(output_md.exists())
            self.assertTrue(manifest.exists())
            self.assertTrue((root / "step4-dashboard" / "index.html").exists())
            self.assertTrue((root / "step4-dashboard" / "data" / "search-results.js").exists())


if __name__ == "__main__":
    unittest.main()
