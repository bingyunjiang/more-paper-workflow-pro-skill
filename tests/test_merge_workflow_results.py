import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from merge_workflow_results import merge_workflow_results  # noqa: E402


class MergeWorkflowResultsTest(unittest.TestCase):
    def test_incremental_merge_reapplies_deduplication(self):
        base = {
            "schema_version": "workflow-contracts.v1",
            "artifact_type": "search_results",
            "metadata": {},
            "records": [
                {"source": "openalex", "doi": "10.1/a", "title": "A", "authors": ["Smith, John"]},
                {"source": "cnki", "doi": "cnki.1", "title": "液冷板设计", "authors": ["张三"]},
            ],
        }
        incoming = {
            "records": [
                {"source": "crossref", "doi": "https://doi.org/10.1/a", "title": "A", "authors": ["Smith, John", "Li, Ming"], "abstract": "x"},
                {"source": "wanfang", "doi": "wanfang.2", "title": "液冷板设计", "authors": ["张三"], "abstract": "摘要"},
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            base_path = tmp_path / "base.json"
            incoming_path = tmp_path / "incoming.json"
            base_path.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
            incoming_path.write_text(json.dumps(incoming, ensure_ascii=False), encoding="utf-8")
            merged = merge_workflow_results(base_path, [incoming_path])

        self.assertEqual(len(merged["records"]), 2)
        self.assertEqual(merged["metadata"]["incoming_record_count"], 2)
        self.assertEqual(merged["metadata"]["merged_record_count_before_dedup"], 4)
        self.assertEqual(merged["metadata"]["merged_record_count_after_dedup"], 2)

