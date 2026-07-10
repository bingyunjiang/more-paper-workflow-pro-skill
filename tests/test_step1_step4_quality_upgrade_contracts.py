from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read_rel(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class Step1Step4QualityUpgradeContractsTest(unittest.TestCase):
    def test_step1_to_step4_quality_tools_are_wired(self):
        step1 = read_rel("agents/step_1_topic.md")
        step2 = read_rel("agents/step_2_outline.md")
        step3 = read_rel("agents/step_3_search_plan.md")
        step4 = read_rel("agents/step_4_search_score.md")
        completion = read_rel("references/completion-gates.md")

        for token in ["falsification_condition", "minimum_viable_study", "validate_early_step_output.py step1"]:
            self.assertIn(token, step1 + completion)
        for token in ["rq_ids", "validate_early_step_output.py step2"]:
            self.assertIn(token, step2 + completion)
        for token in ["compiled_queries.json", "pilot_search_results.json", "suspected_query_drift"]:
            self.assertIn(token, step3 + completion)
        for token in [
            "research_traceability_matrix.json", "stratified_search_audit.json",
            "_score_dimensions", "_uncertainty_flags", "主题匹配 35%",
        ]:
            self.assertIn(token, step4 + completion)


if __name__ == "__main__":
    unittest.main()
