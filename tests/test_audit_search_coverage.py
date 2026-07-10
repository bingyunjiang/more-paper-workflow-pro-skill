import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_search_coverage import audit_search_coverage  # noqa: E402


class AuditSearchCoverageTest(unittest.TestCase):
    def test_detects_stratified_saturation_and_source_bias(self):
        plan = {"search_tasks": [{"id": "S1", "rq_id": "RQ1", "chapter_id": "ch1", "evidence_type": "method", "minimum_t1_t2": 2}]}
        records = []
        for index in range(12):
            records.append({
                "search_task_id": "S1", "source": "openalex", "language": "en", "venue": "Venue A",
                "year": 2024, "doi": f"10.1/{index}", "verification_status": "VERIFIED",
                "paper_tier": "T1" if index < 2 else "T3", "discovery_round": 1 if index < 11 else 2,
            })
        payload = audit_search_coverage(plan, {"records": records})
        flags = {item["flag"] for item in payload["bias_flags"]}

        self.assertEqual(payload["task_saturation"]["S1"]["status"], "not_saturated")
        self.assertIn("single_source_dependency", flags)
        self.assertIn("language_concentration", flags)
        self.assertIn("no_contradictory_evidence_identified", flags)
        self.assertEqual(payload["summary"]["readiness"], "blocked")


if __name__ == "__main__":
    unittest.main()
