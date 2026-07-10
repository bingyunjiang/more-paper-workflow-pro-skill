import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_research_coverage_matrix import build_coverage_matrix  # noqa: E402


class ResearchCoverageMatrixTest(unittest.TestCase):
    def test_reports_coverage_per_rq_chapter_and_evidence_type(self):
        plan = {"search_tasks": [
            {"id": "S1", "rq_id": "RQ1", "chapter_id": "ch2", "evidence_type": "method", "minimum_t1_t2": 2},
            {"id": "S2", "rq_id": "RQ2", "chapter_id": "ch3", "evidence_type": "experiment"},
        ]}
        results = {"records": [
            {"search_task_id": "S1", "verification_status": "VERIFIED", "paper_tier": "T1"},
            {"search_task_id": "S1", "verification_status": "VERIFIED_LOCAL", "paper_tier": "Tier 2"},
            {"search_task_id": "S1", "verification_status": "WARN", "paper_tier": "T2", "support_grade": "contradictory_or_limiting"},
        ]}
        payload = build_coverage_matrix(plan, results)

        by_id = {row["search_task_id"]: row for row in payload["rows"]}
        self.assertEqual(by_id["S1"]["coverage_status"], "strong-ready")
        self.assertEqual(by_id["S1"]["contradictory_count"], 1)
        self.assertEqual(by_id["S2"]["coverage_status"], "uncovered")
        self.assertFalse(payload["summary"]["all_required_tasks_covered"])


if __name__ == "__main__":
    unittest.main()
