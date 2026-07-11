import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_early_step_output import (  # noqa: E402
    _validate_calibration,
    _validate_keyword_audit,
    validate_step1,
    validate_step2,
    validate_step3,
)


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
evidence_calibration:
  status: unavailable
  sources_attempted: [openalex]
  queries: [demo query]
  limitations: [network unavailable]
interaction_record:
  answer_burden: minimal
  user_supplied: [research direction]
  inferred: []
  assumed: [target venue unknown]
  unresolved_blocking: []
  unresolved_nonblocking: [target venue]
---
""", encoding="utf-8")
            errors = validate_step1(path)
        self.assertIn("pre_review.total_score must equal 20", errors)
        self.assertTrue(any("falsification_condition" in error for error in errors))

    def test_step1_requires_minimal_interaction_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "研究主题.md"
            path.write_text("""---
interaction_record:
  answer_burden: questionnaire
  user_supplied: not-a-list
evidence_calibration:
  status: unavailable
  sources_attempted: [openalex]
  queries: [demo]
  limitations: [offline]
---
""", encoding="utf-8")
            errors = validate_step1(path)
        self.assertIn("interaction_record.answer_burden must be minimal", errors)
        self.assertIn("interaction_record.user_supplied must be a list", errors)

    def test_step2_validates_rq_traceability(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "section_blueprints.json"
            path.write_text(json.dumps({
                "outline_state": "outline_baseline",
                "core_research_question_ids": ["RQ1", "RQ2"],
                "evidence_calibration": {
                    "status": "unavailable", "sources_attempted": ["openalex"],
                    "queries": ["demo query"], "limitations": ["network unavailable"],
                },
                "keyword_audit": [{
                    "term": "demo", "origin": "topic", "observed_in_records": 0,
                    "ambiguity": "low", "action": "expand",
                }],
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
            path.write_text(json.dumps({
                "plan_mode": "standard", "execution_context": "step3_planning",
                "retrieval_language": "en", "source_scope": ["openalex"],
                "publication_year_range": {"from": 2016, "to": 2026},
                "document_types": ["journal-article"],
                "inclusion_criteria": ["topic relevant"], "exclusion_criteria": ["off topic"],
                "deduplication_plan": {"primary_key": "doi", "fallback_key": "title_author_year"},
                "query_versions": [{"version": "v1", "status": "draft"}],
            "search_update_policy": {"rerun_before_submission": True},
                "search_tasks": [{
                "id": "S1", "rq_id": "RQ1", "chapter_id": "ch1", "evidence_type": "method",
                "question_to_answer": "q", "tier": "standard", "framework": "concept_block",
                "route": {"l1": ["openalex"]},
                "query_blocks": [{"name": "object", "terms": ["only-one"]}],
            }]}), encoding="utf-8")
            errors = validate_step3(path)
        self.assertTrue(any("needs at least 2 unique terms" in error for error in errors))

    def test_step3_accepts_single_canonical_term_with_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "检索方案.json"
            payload = {
                "plan_mode": "standard", "execution_context": "step3_planning",
                "retrieval_language": "en", "source_scope": ["openalex"],
                "publication_year_range": {"from": 2016, "to": 2026},
                "document_types": ["journal-article"],
                "inclusion_criteria": ["topic relevant"], "exclusion_criteria": ["off topic"],
                "deduplication_plan": {"primary_key": "doi"},
                "query_versions": [{"version": "v1"}], "search_update_policy": {"rerun_before_submission": True},
                "search_tasks": [{
                    "id": "S1", "rq_id": "RQ1", "chapter_id": "ch1", "evidence_type": "method",
                    "question_to_answer": "q", "tier": "standard", "framework": "concept_block",
                    "route": {"l1": ["openalex"]},
                    "query_blocks": [{"name": "standard", "terms": ["ISO 15118"], "single_canonical_term_reason": "official standard identifier"}],
                }],
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            errors = validate_step3(path)
        self.assertEqual(errors, [])

    def test_systematic_mode_requires_prisma_s_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "检索方案.json"
            payload = {
                "plan_mode": "systematic", "execution_context": "step3_planning",
                "retrieval_language": "en", "source_scope": ["pubmed"],
                "publication_year_range": {"from": 2000, "to": 2026}, "document_types": ["journal-article"],
                "inclusion_criteria": ["eligible"], "exclusion_criteria": ["ineligible"],
                "deduplication_plan": {"primary_key": "doi"}, "query_versions": [{"version": "v1"}],
                "search_update_policy": {"rerun_before_submission": True}, "review_protocol": {},
                "search_tasks": [{
                    "id": "S1", "rq_id": "RQ1", "chapter_id": "ch1", "evidence_type": "review",
                    "question_to_answer": "q", "tier": "deep", "framework": "pico",
                    "route": {"l1": ["pubmed"]},
                    "query_blocks": [{"name": "population", "terms": ["battery", "energy storage"]}],
                }],
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            errors = validate_step3(path)
        self.assertTrue(any("review_protocol.press_review" in error for error in errors))

    def test_step1_requires_traceable_records_for_executed_calibration(self):
        errors = _validate_calibration({
            "status": "executed", "sources_attempted": ["openalex"], "queries": ["demo"],
            "representative_records": [{"title": "Only one", "doi": "10.1/demo"}],
        }, "evidence_calibration")
        self.assertIn("evidence_calibration.representative_records must contain at least 2 records", errors)

    def test_calibration_accepts_two_traceable_records(self):
        errors = _validate_calibration({
            "status": "executed", "sources_attempted": ["openalex", "crossref"], "queries": ["demo"],
            "representative_records": [
                {"title": "Paper one", "doi": "10.1/one"},
                {"title": "Paper two", "source_id": "openalex:W2"},
            ],
        }, "evidence_calibration")
        self.assertEqual(errors, [])

    def test_keyword_audit_rejects_untraceable_term(self):
        errors = _validate_keyword_audit([{
            "term": "demo", "origin": "invented", "observed_in_records": -1,
            "ambiguity": "unknown", "action": "accept",
        }])
        self.assertTrue(any("origin is invalid" in error for error in errors))
        self.assertTrue(any("observed_in_records" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
