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
        step7_entry = read_rel("agents/step_7_entry.md")

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

        for internal_role in ["generator", "synthesizer", "reviewer", "auditor"]:
            self.assertNotIn(internal_role, step7_entry)

    def test_step7_internal_pipeline_and_light_readability_rules_exist(self):
        text = read_rel("agents/step_7_writing.md")
        self.assertIn("### 7.7: 内部写作流水线（用户不可见）", text)
        self.assertIn("生成", text)
        self.assertIn("整合", text)
        self.assertIn("审阅", text)
        self.assertIn("校验", text)
        self.assertIn("#### 7.7.1 轻润色内建规则", text)
        self.assertIn("连贯性", text)
        self.assertIn("术语统一", text)
        self.assertIn("过渡句", text)
        self.assertIn("重复句压缩", text)
        self.assertIn("基础 AI 痕迹清理", text)
        self.assertIn("不做全文终稿 polish", text)
        self.assertIn("不得作为用户选项、命令、按钮或对话模式暴露", text)

    def test_step8_is_final_polishing_not_writing_or_audit_owner(self):
        step8 = read_rel("agents/step_8_polishing.md")
        step8_entry = read_rel("agents/step_8_entry.md")
        architecture = read_rel("docs/workflow-architecture.md")

        self.assertIn("成稿级精修", step8)
        self.assertIn("不负责正文生成、证据合成、引用审计或修稿路线图", step8)
        self.assertIn("不接管 Step 7 的生成、整合、审阅、校验流水线", step8)
        self.assertIn("只消费已有正文", step8_entry)
        self.assertIn("不接管 Step 7 的正文生成、证据合成、引用审计或修稿路线图", step8_entry)
        self.assertIn("Step 7 是写作生产层", architecture)
        self.assertIn("Step 8 是成稿级精修层", architecture)

    def test_step7_revision_coach_contract_exists(self):
        text = read_rel("agents/step_7_writing.md")
        self.assertIn("#### 7.11.1 修稿教练", text)
        self.assertIn("revision_roadmap.md", text)
        self.assertIn("response_letter_skeleton.md", text)
        self.assertIn("evidence_gap_list.md", text)
        self.assertIn("rollback_target", text)

    def test_step7_argument_plan_and_rereview_contracts_exist(self):
        text = read_rel("agents/step_7_writing.md")
        self.assertIn("#### 7.6.3 章节级论证计划", text)
        self.assertIn("argument_plan.md", text)
        self.assertIn("rollback_if_missing", text)
        self.assertIn("### 7.13: 复评", text)
        self.assertIn("rereview_report.md", text)
        self.assertIn("new_issue", text)

    def test_step7_heading_numbers_are_ordered_and_clean(self):
        text = read_rel("agents/step_7_writing.md")
        forbidden_numbering = ["7.W", "7.2b", "7.5b", "7.9b", "7.9c"]
        for marker in forbidden_numbering:
            self.assertNotIn(marker, text)

        heading_lines = [
            line
            for line in text.splitlines()
            if line.startswith("### 7.") and ":" in line
        ]
        expected = [f"### 7.{index}:" for index in range(17)]
        actual = [line.split(":", 1)[0] + ":" for line in heading_lines]
        self.assertEqual(expected, actual)

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
