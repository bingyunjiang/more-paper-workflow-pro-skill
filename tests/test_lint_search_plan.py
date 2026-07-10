import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lint_search_plan import lint_and_compile, run_pilot  # noqa: E402


class LintSearchPlanTest(unittest.TestCase):
    def test_compiles_queries_and_accepts_relevant_pilot(self):
        plan = {"search_tasks": [{
            "id": "S1", "route": {"l1": ["openalex"], "l2": ["cnki"]},
            "query_blocks": [
                {"name": "object", "terms": ["cold plate", "liquid cooling"]},
                {"name": "method", "terms": ["topology optimization", "shape optimization"]},
            ],
            "exclusion_terms": ["building"],
        }]}
        pilot = {"records": [
            {"search_task_id": "S1", "title": "Cold plate topology optimization"},
            {"search_task_id": "S1", "title": "Liquid cooling shape optimization"},
        ]}
        payload = lint_and_compile(plan, pilot)
        task = payload["tasks"][0]
        self.assertEqual(payload["summary"]["status"], "pass")
        self.assertIn("AND", task["compiled_queries"]["openalex"])
        self.assertIn(" * ", task["compiled_queries"]["cnki"])
        self.assertEqual(task["pilot"]["status"], "ok")

    def test_detects_exclusion_collision_and_zero_result(self):
        plan = {"search_tasks": [{
            "id": "S1", "route": {"l1": ["openalex"]},
            "query_blocks": [{"name": "object", "terms": ["battery", "battery"]}],
            "exclusion_terms": ["battery"],
        }]}
        payload = lint_and_compile(plan, {"records": []})
        errors = payload["tasks"][0]["lint_errors"]
        self.assertEqual(payload["summary"]["status"], "fail")
        self.assertTrue(any("collision" in error for error in errors))
        self.assertIn("pilot_zero-result", errors)

    def test_run_pilot_executes_first_routed_source_and_tags_results(self):
        calls = []

        def fake_search(query, limit, use_cache):
            calls.append((query, limit, use_cache))
            return [{"title": "Cold plate topology optimization"}]

        plan = {"search_tasks": [{
            "id": "S1", "route": {"l1": ["openalex"]},
            "query_blocks": [{"name": "object", "terms": ["cold plate", "liquid cooling"]}],
        }]}
        payload = run_pilot(plan, limit=5, search_functions={"openalex": fake_search})

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], 5)
        self.assertFalse(calls[0][2])
        self.assertEqual(payload["records"][0]["search_task_id"], "S1")
        self.assertEqual(payload["records"][0]["pilot_source"], "openalex")


if __name__ == "__main__":
    unittest.main()
