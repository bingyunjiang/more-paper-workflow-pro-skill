import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_early_step_output import validate_step1, validate_step2, validate_step3  # noqa: E402


class ValidateEarlyStepsTest(unittest.TestCase):
    def test_step1_rejects_inconsistent_score_and_missing_falsifiability(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "研究主题.md"
            path.write_text("""---
topic:
  focused_topic: demo
  primary_rq: rq
  scope_boundaries: {in_scope: [a], out_of_scope: [b]}
  evaluation_metrics: [a, b, c]
pre_review:
  originality: {score: 4, reason: ok}
  importance: {score: 4, reason: ok}
  feasibility: {score: 4, reason: ok}
  literature_support: {score: 4, reason: ok}
  method_readiness: {score: 4, reason: ok}
  total_score: 25
  decision: green
---
""", encoding="utf-8")
            errors = validate_step1(path)
        self.assertIn("pre_review.total_score must equal 20", errors)
        self.assertTrue(any("falsification_condition" in error for error in errors))

    def test_step2_validates_rq_traceability(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "section_blueprints.json"
            path.write_text(json.dumps({
                "core_research_question_ids": ["RQ1", "RQ2"],
                "sections": [{
                    "section_id": "ch1", "section_title": "方法", "section_function": "method-definition",
                    "key_claims": ["C1"], "evidence_needed": ["method"], "do_not_write": ["results"], "rq_ids": ["RQ1"],
                }],
            }), encoding="utf-8")
            errors = validate_step2(path)
        self.assertIn("research question is not mapped to any section: RQ2", errors)

    def test_step3_validates_query_blocks_and_bindings(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "检索方案.json"
            path.write_text(json.dumps({"search_tasks": [{
                "id": "S1", "rq_id": "RQ1", "chapter_id": "ch1", "evidence_type": "method",
                "question_to_answer": "q", "tier": "standard", "route": {"l1": ["openalex"]},
                "query_blocks": [{"name": "object", "terms": ["only-one"]}],
            }]}), encoding="utf-8")
            errors = validate_step3(path)
        self.assertTrue(any("needs at least 2 unique terms" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
