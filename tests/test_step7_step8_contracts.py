from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read_rel(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class Step7Step8ContractsTest(unittest.TestCase):
    def test_step7_public_modes_are_consistent(self):
        step7 = read_rel("agents/step_7_writing.md")
        skill = read_rel("SKILL.md")
        readme = read_rel("README.md")

        expected_modes = [
            "full-document",
            "review-only",
            "abstract-only",
            "chapter-only",
            "continue-existing",
            "revision-only",
        ]

        for mode in expected_modes:
            self.assertIn(mode, step7)
            self.assertIn(mode, skill)
            self.assertIn(mode, readme)

        forbidden = ["outline-only", "argument-first"]
        for mode in forbidden:
            self.assertNotIn(f"写作模式（{mode}", skill)

    def test_step7_revision_coach_contract_exists(self):
        text = read_rel("agents/step_7_writing.md")
        self.assertIn("#### 7.9.1 修稿教练", text)
        self.assertIn("revision_roadmap.md", text)
        self.assertIn("response_letter_skeleton.md", text)
        self.assertIn("evidence_gap_list.md", text)
        self.assertIn("rollback_target", text)

    def test_step7_argument_plan_and_rereview_contracts_exist(self):
        text = read_rel("agents/step_7_writing.md")
        self.assertIn("#### 7.5.3 章节级论证计划", text)
        self.assertIn("argument_plan.md", text)
        self.assertIn("rollback_if_missing", text)
        self.assertIn("#### 7.9.3 复评", text)
        self.assertIn("rereview_report.md", text)
        self.assertIn("new_issue", text)

    def test_step7_citation_audit_exposes_three_layers(self):
        text = read_rel("agents/step_7_writing.md")
        self.assertIn("format_status", text)
        self.assertIn("mapping_status", text)
        self.assertIn("evidence_status", text)
        self.assertIn("replace_or_remove", text)
        self.assertIn("recommended_action", text)
        self.assertIn("repair_mapping", text)

    def test_step8_degraded_entry_rules_remain_non_blocking(self):
        text = read_rel("agents/step_8_polishing.md")
        self.assertIn("评审依据不足", text)
        self.assertIn("引用安全提醒", text)
        self.assertIn("不能要求用户回跑 Step 7", text)
        self.assertIn("默认以这些 JSON 为**约束源**", text)
        self.assertIn("diagnostic_summary.md", text)
        self.assertIn("evidence_gap", text)
        self.assertIn("structure_drift", text)
        self.assertIn("language_mechanical", text)
        self.assertIn("contribution_overclaim", text)
        self.assertIn("citation_misalignment", text)
        self.assertIn("ready_for_finalize", text)
        self.assertIn("ready_with_warnings", text)
        self.assertIn("not_ready_requires_rollback", text)
        self.assertIn("return_to_step_7_revision_only", text)
        self.assertIn("return_to_step_7_citation_audit", text)
        self.assertIn("return_to_step_7_argument_plan", text)
        self.assertIn("return_to_step_4_or_6", text)

    def test_abstract_only_subtypes_are_documented(self):
        text = read_rel("agents/step_7_writing.md")
        self.assertIn("journal-abstract", text)
        self.assertIn("thesis-abstract", text)
        self.assertIn("bilingual-abstract", text)

    def test_commands_and_showcase_exist(self):
        for rel in [
            "commands/topic.md",
            "commands/search.md",
            "commands/download.md",
            "commands/zotero.md",
            "commands/write.md",
            "commands/polish.md",
            "commands/citation-audit.md",
            "commands/revision-roadmap.md",
            "examples/showcase/README.md",
        ]:
            self.assertTrue((ROOT / rel).exists(), rel)

    def test_deep_research_borrowings_are_wired_into_steps(self):
        step1 = read_rel("agents/step_1_topic.md")
        step3 = read_rel("agents/step_3_search_plan.md")
        step4 = read_rel("agents/step_4_search_score.md")
        step7 = read_rel("agents/step_7_writing.md")

        self.assertIn("research_intent_type", step1)
        self.assertIn("research_question_candidates", step1)
        self.assertIn("primary_rq", step1)
        self.assertIn("scope_boundaries", step1)
        self.assertIn("methodology_blueprint", step1)
        self.assertIn("devils_advocate_challenge", step1)

        self.assertIn("review_protocol", step3)
        self.assertIn("inclusion_criteria", step3)
        self.assertIn("exclusion_criteria", step3)

        self.assertIn("证据层级提示", step4)
        self.assertIn("screening rationale", step4)
        self.assertIn("exclusion buckets", step4)

        self.assertIn("strongest_counterargument", step7)
        self.assertIn("alternative_explanations", step7)

    def test_rag_candidate_layer_is_documented_as_non_authoritative(self):
        step7 = read_rel("agents/step_7_writing.md")
        step8 = read_rel("agents/step_8_polishing.md")
        readme = read_rel("README.md")

        self.assertIn("retrieval_index_manifest.json", step7)
        self.assertIn("retrieval_candidates.json", step7)
        self.assertIn("retrieved_candidate", step7)
        self.assertIn("不得直接升级为 `VERIFIED` / `VERIFIED_LOCAL`", step7)
        self.assertIn("Step 8 不直接读取 `retrieval_candidates.json`", step8)
        self.assertIn("候选定位加速层", readme)

    def test_figure_evidence_subchain_is_documented(self):
        step7 = read_rel("agents/step_7_writing.md")
        readme = read_rel("README.md")

        self.assertIn("figure_index.json", step7)
        self.assertIn("figure_evidence_report.md/json", step7)
        self.assertIn("figure_claim", step7)
        self.assertIn("figure_overinterpretation", step7)
        self.assertIn("caption_only", step7)
        self.assertIn("text_caption_aligned", step7)
        self.assertIn("visual_confirmed", step7)
        self.assertIn("figure_not_supported", step7)
        self.assertIn("need_visual_check", step7)
        self.assertIn("supplement_text_evidence", step7)
        self.assertIn("图表证据子链", readme)


if __name__ == "__main__":
    unittest.main()
