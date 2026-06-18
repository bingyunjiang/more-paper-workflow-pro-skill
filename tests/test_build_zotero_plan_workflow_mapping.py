import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from build_zotero_plan import merge_workflow_mapping  # noqa: E402


class BuildZoteroPlanWorkflowMappingTest(unittest.TestCase):
    def test_merge_workflow_mapping_prefers_workflow_chapter_fields(self):
        record = {
            "title": "Topology optimization of cooling plates for battery thermal management",
            "doi": "10.1016/j.ijheatmasstransfer.2021.121612",
            "chapter_id": "",
            "chapter_title": "",
        }
        workflow_index = {
            "10.1016/j.ijheatmasstransfer.2021.121612": {
                "search_task_id": "S3",
                "chapter_id": "2.3",
                "chapter_title": "电池热管理应用与系统集成",
                "secondary_search_task_ids": ["S2"],
                "secondary_chapter_ids": ["2.2"],
                "secondary_chapter_titles": ["多目标优化与性能评价指标"],
                "evidence_type": "application",
            }
        }
        merged = merge_workflow_mapping(record, workflow_index)
        self.assertEqual(merged["chapter_id"], "2.3")
        self.assertEqual(merged["chapter_title"], "电池热管理应用与系统集成")
        self.assertEqual(merged["secondary_chapter_ids"], ["2.2"])


if __name__ == "__main__":
    unittest.main()
