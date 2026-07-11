import unittest

from scripts.reconcile_step2_after_search import reconcile


class ReconcileStep2AfterSearchTest(unittest.TestCase):
    def test_marks_all_covered_sections_evidence_validated(self):
        outline = {"outline_state": "outline_baseline", "sections": [{
            "section_id": "ch1", "section_title": "方法", "rq_ids": ["RQ1"],
            "key_claims": ["claim"], "keywords": ["thermal management"],
        }]}
        results = {"records": [{
            "chapter_id": "ch1", "rq_id": "RQ1", "title": "Thermal management method",
            "abstract": "thermal management optimization optimization", "paper_tier": "Tier 1",
            "verification_status": "VERIFIED",
        }]}
        payload = reconcile(outline, results)
        self.assertEqual(payload["summary"]["reconciliation_status"], "evidence_validated")
        self.assertFalse(payload["summary"]["requires_user_confirmation"])
        self.assertEqual(payload["calibrated_outline"]["outline_state"], "evidence_validated")
        self.assertEqual(payload["calibrated_outline"]["sections"][0]["step4_evidence_status"], "covered")

    def test_warn_or_unverified_records_do_not_close_coverage(self):
        outline = {"sections": [{
            "section_id": "ch1", "section_title": "方法", "rq_ids": ["RQ1"],
            "key_claims": ["claim"], "keywords": ["thermal"],
        }]}
        results = {"records": [{
            "chapter_id": "ch1", "title": "Thermal method", "paper_tier": "Tier 1",
            "verification_status": "WARN",
        }]}
        payload = reconcile(outline, results)
        self.assertEqual(payload["sections"][0]["coverage_status"], "uncovered")
        self.assertEqual(payload["sections"][0]["warn_count"], 1)

    def test_uncovered_core_section_requires_confirmation_not_silent_rewrite(self):
        outline = {"sections": [{
            "section_id": "ch2", "section_title": "实验", "rq_ids": ["RQ2"],
            "key_claims": ["claim"], "keywords": ["experiment"],
        }]}
        payload = reconcile(outline, {"records": []})
        self.assertEqual(payload["summary"]["reconciliation_status"], "requires_revision")
        self.assertTrue(payload["summary"]["requires_user_confirmation"])
        self.assertIn("primary RQ", payload["automatic_change_boundary"]["requires_user_confirmation"])
        self.assertEqual(payload["calibrated_outline"]["outline_state"], "search_calibrated")
        self.assertIn("formal_search_evidence_gap", payload["calibrated_outline"]["sections"][0]["risk_flags"])


if __name__ == "__main__":
    unittest.main()
