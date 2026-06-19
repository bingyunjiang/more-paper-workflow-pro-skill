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

        self.assertNotIn("- `draft`", step7_entry)
        self.assertNotIn("- `citation-audit`", step7_entry)
        self.assertNotIn("- `figure`", step7_entry)
        self.assertNotIn("- `pre-review`", step7_entry)

    def test_step7_internal_pipeline_and_light_readability_guidance_exist(self):
        text = read_rel("agents/step_7_writing.md")
        self.assertIn("### 7.8. 内部写作流水线（用户不可见）", text)
        self.assertIn("生成", text)
        self.assertIn("整合", text)
        self.assertIn("审阅", text)
        self.assertIn("校验", text)
        self.assertIn("#### 7.8.1. 轻量可读性整理", text)
        self.assertIn("不应预设用户的写作策略、论证风格或表达审美", text)
        self.assertIn("最小术语统一", text)
        self.assertIn("标记需要后续补证据", text)
        self.assertIn("Step 7 的职责是维持 workflow 与证据边界", text)
        self.assertIn("不得作为用户选项、命令、按钮或对话模式暴露", text)

    def test_step8_is_constrained_revision_not_primary_writing_or_audit_owner(self):
        step8 = read_rel("agents/step_8_polishing.md")
        step8_entry = read_rel("agents/step_8_entry.md")
        architecture = read_rel("docs/workflow-architecture.md")

        self.assertIn("受约束补写", step8)
        self.assertIn("局部补写", step8)
        self.assertIn("不负责主体写作", step8)
        self.assertIn("修订后验证", step8)
        self.assertIn("Step 7 负责主体写作与主论证展开", step8)
        self.assertIn("Step 8 负责局部增强、风险收敛、终稿修订闭环", step8)
        self.assertIn("不负责主体写作", step8_entry)
        self.assertIn("执行受约束补写、直接修改与修订后验证", step8_entry)
        self.assertIn("Step 7 是写作生产层", architecture)
        self.assertIn("Step 8 是成稿级精修与保守修订层", architecture)

    def test_step7_revision_coach_contract_exists(self):
        text = read_rel("agents/step_7_writing.md")
        self.assertIn("#### 7.12.1. 修稿教练", text)
        self.assertIn("revision_roadmap.md", text)
        self.assertIn("response_letter_skeleton.md", text)
        self.assertIn("evidence_gap_list.md", text)
        self.assertIn("rollback_target", text)
        self.assertIn("问题识别、修订动作、证据状态、验证结果、下一步动作", text)

    def test_step7_argument_plan_and_rereview_contracts_exist(self):
        text = read_rel("agents/step_7_writing.md")
        self.assertIn("#### 7.7.3. 章节级论证计划", text)
        self.assertIn("argument_plan.md", text)
        self.assertIn("rollback_if_missing", text)
        self.assertIn("### 7.14. 复评", text)
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
            if line.startswith("### 7.")
        ]
        expected = [f"7.{index}." for index in range(1, 18)]
        actual = [line.split(maxsplit=2)[1] for line in heading_lines]
        self.assertEqual(expected, actual)
        self.assertNotIn("### 7.0", text)
        self.assertNotIn("### 7.1:", text)

    def test_step7_citation_audit_exposes_three_layers(self):
        text = read_rel("agents/step_7_writing.md")
        self.assertIn("format_status", text)
        self.assertIn("mapping_status", text)
        self.assertIn("evidence_status", text)
        self.assertIn("replace_or_remove", text)
        self.assertIn("recommended_action", text)
        self.assertIn("repair_mapping", text)

    def test_step7_multi_entry_evidence_pack_and_docx_policy_exist(self):
        text = read_rel("agents/step_7_writing.md")
        skill = read_rel("SKILL.md")
        policy = read_rel("references/pdf-processing-policy.md")

        for token in [
            "Zotero/MinerU 是推荐资产层，不是 Step 7 的硬依赖",
            "多入口证据 intake",
            "`zotero_full`",
            "`zotero_mineru`",
            "`evidence_pack`",
            "`draft_only`",
            "`mixed`",
            "evidence_pack.json",
            "场景只决定读取路径，证据等级决定能写多强",
            "llm-for-zotero",
            "仍可继续读取 Zotero fulltext",
            "当前写作范围完成后，才提示用户是否导出 DOCX",
            "不得在每个写作增量后自动导出 DOCX",
        ]:
            self.assertIn(token, text)

        self.assertIn("LLM-for-Zotero-MinerU-cache-*.zip", text)
        self.assertIn("manifest.json", text)
        self.assertIn("full.md", text)
        self.assertIn("images/", text)
        self.assertIn("evidence_pack", skill)
        self.assertIn("推荐 Zotero 用户安装 `llm-for-zotero` 插件", skill)
        self.assertIn("parser_confidence: low", policy)

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

    def test_step8_ai_trace_diagnostics_contract_exists(self):
        text = read_rel("agents/step_8_polishing.md")
        command = read_rel("commands/polish.md")
        readme = read_rel("README.md")
        reference = read_rel("references/deterministic-writing-diagnostics.md")

        self.assertIn("AI 味确定性检查", text)
        self.assertIn("language_mechanical", text)
        self.assertIn("diagnostic_summary.md", text)
        self.assertIn("revision_ledger.json", text)
        self.assertIn("revision_ledger.md", text)
        self.assertIn("润色质量报告.md", text)
        self.assertIn("单纯词表或模式命中不得直接升格为 `evidence_gap / structure_drift / contribution_overclaim`", text)
        self.assertIn("风格类命中默认不触发 rollback", text)
        self.assertIn("Step 8 不因“AI 味”要求用户回跑主写作", text)
        self.assertIn("AI 味确定性检查", command)
        self.assertIn("AI 味确定性检查", readme)
        self.assertIn("载体清洁度检查", readme)

        for token in [
            "套话短语规则",
            "机械连接词堆积规则",
            "伪洞见与悬垂表达规则",
            "空泛归因规则",
            "句长节奏过匀规则",
            "冗余破折号与插入语规则",
            "可在 Step 8 直接修订",
            "可修但需轻量含义审计",
            "只提醒，不在 Step 8 内硬修",
        ]:
            self.assertIn(token, text)
            self.assertIn(token, reference)

    def test_step8_revision_ledger_and_minimum_validation_contracts_exist(self):
        text = read_rel("agents/step_8_polishing.md")
        command = read_rel("commands/polish.md")
        output_contract = read_rel("static/core/output-contract.md")

        self.assertIn("revision_ledger.json", text)
        self.assertIn("revision_ledger.md", text)
        self.assertIn("issue_id", text)
        self.assertIn("category", text)
        self.assertIn("issue_type", text)
        self.assertIn("severity", text)
        self.assertIn("location", text)
        self.assertIn("problem", text)
        self.assertIn("evidence_basis", text)
        self.assertIn("allowed_action", text)
        self.assertIn("proposed_revision", text)
        self.assertIn("verification", text)
        self.assertIn("final_status", text)
        self.assertIn("next_action", text)

        self.assertIn("术语一致性验证", text)
        self.assertIn("核心含义漂移验证", text)
        self.assertIn("论断强度验证", text)
        self.assertIn("引用/指代/衔接验证", text)
        self.assertIn("PASS / WARN / FAIL", text)
        self.assertIn("含义漂移", text)
        self.assertIn("论断意外增强", text)
        self.assertIn("硬门槛", text)

        self.assertIn("revision_ledger.json/md", command)
        self.assertIn("revision_ledger", output_contract)

    def test_step8_heading_numbers_are_ordered_and_clean(self):
        text = read_rel("agents/step_8_polishing.md")

        self.assertIn("### 8.3. 最小验证规程", text)
        self.assertIn("### 8.4. revision_ledger 双层工件契约", text)
        self.assertIn("#### 8.4.1. 轻量含义审计触发", text)
        self.assertIn("### 8.9. 日志回写", text)
        self.assertNotIn("### 8.0", text)
        self.assertNotIn("### 4.1 PDF 提取结果", text)
        self.assertNotIn("## 7. 最小验证规程", text)
        self.assertNotIn("## 8. revision_ledger 双层工件契约", text)
        self.assertNotIn("### 8.2.1. 轻量含义审计触发", text)

    def test_step7_step8_methodology_details_are_referenced_not_hardcoded(self):
        step7 = read_rel("agents/step_7_writing.md")
        step8 = read_rel("agents/step_8_polishing.md")

        self.assertIn("统一放到 `references/writing-modes.md`", step7)
        self.assertIn("`references/citation-audit-guide.md`", step7)
        self.assertIn("`references/reviewer-protocol.md`", step7)
        self.assertIn("`references/ai-trace-taxonomy.md`", step8)
        self.assertIn("`references/polish-modes.md`", step8)
        self.assertIn("`references/writing-antipatterns.md`", step8)

    def test_step7_figure_assets_use_project_figures_dir(self):
        step7 = read_rel("agents/step_7_writing.md")
        self.assertIn("只有被选入正文的图片才复制到项目 `figures/`", read_rel("references/pdf-processing-policy.md"))
        self.assertIn("确保正文图片引用的是项目内 `figures/` 的相对路径", step7)

    def test_revision_artifacts_share_minimum_lifecycle_fields(self):
        step7 = read_rel("agents/step_7_writing.md")
        step8 = read_rel("agents/step_8_polishing.md")
        command = read_rel("commands/revision-roadmap.md")

        for field in [
            "issue_id",
            "chapter_binding",
            "claim_binding",
            "problem_summary",
            "action_type",
            "evidence_status",
            "verification_result",
            "next_action",
            "issue_state",
            "state_reason",
        ]:
            self.assertIn(field, step7)
            self.assertIn(field, step8)
            self.assertIn(field, command)

        for state in [
            "identified",
            "routed",
            "in_revision",
            "verification_pending",
            "closed",
            "blocked_author_decision",
            "blocked_evidence",
            "invalid_or_not_applied",
        ]:
            self.assertIn(state, step7)
            self.assertIn(state, step8)
            self.assertIn(state, command)

        self.assertIn("只约束问题生命周期", step7)
        self.assertIn("不规定具体写作策略", step7)
        self.assertIn("不约束作者的写作策略", read_rel("static/core/output-contract.md"))

    def test_step8_chinese_three_way_categories_and_action_boundaries_exist(self):
        text = read_rel("agents/step_8_polishing.md")
        readme = read_rel("README.md")

        for label in ["可直接修订", "需作者决定", "当前依据不足"]:
            self.assertIn(label, text)
            self.assertIn(label, readme)

        self.assertIn("直接修改", text)
        self.assertIn("局部补写", text)
        self.assertIn("桥接句", text)
        self.assertIn("限定句", text)
        self.assertIn("解释句", text)
        self.assertIn("引证配套句", text)
        self.assertIn("局部支撑句", text)

        self.assertIn("新增外部证据或引用来源", text)
        self.assertIn("重写章节主体", text)
        self.assertIn("重定义贡献点/研究问题", text)
        self.assertIn("新增实验", text)

    def test_step7_step8_do_not_hardcode_writing_style_preferences(self):
        step7 = read_rel("agents/step_7_writing.md")
        step8 = read_rel("agents/step_8_polishing.md")
        readme = read_rel("README.md")

        self.assertIn("不应限制用户的创造性组织方式", step7)
        self.assertIn("强行统一用户风格", step8)
        self.assertIn("用户仍保留自己的写作策略和表达风格", step8)
        self.assertIn("用户仍保留自己的写作策略和表达风格", readme)

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
        self.assertIn("references/reviewer-protocol.md", step7)

    def test_rag_candidate_layer_is_documented_as_non_authoritative(self):
        step7 = read_rel("agents/step_7_writing.md")
        step8 = read_rel("agents/step_8_polishing.md")
        readme = read_rel("README.md")

        self.assertIn("retrieval_index_manifest.json", step7)
        self.assertIn("retrieval_candidates.json", step7)
        self.assertIn("retrieved_candidate", step7)
        self.assertIn("按章节→claim 组织", step7)
        self.assertIn("章节级候选证据层", step7)
        self.assertIn("claim_id", step7)
        self.assertIn("claim_text", step7)
        self.assertIn("evidence_question_id", step7)
        self.assertIn("query_variant", step7)
        self.assertIn("source_page_hint", step7)
        self.assertIn("negative_or_conflicting_evidence", step7)
        self.assertIn("不得直接升级为 `VERIFIED` / `VERIFIED_LOCAL`", step7)
        self.assertIn("必要时可读取 `retrieval_candidates.json`", step8)
        self.assertIn("不得把候选层内容直接当作正文证据", step8)
        self.assertIn("候选定位加速层", readme)

    def test_argument_plan_evidence_confirmation_block_exists(self):
        step7 = read_rel("agents/step_7_writing.md")
        self.assertIn("`argument_plan` 证据确认区块", step7)
        self.assertIn("confirmed_evidence", step7)
        self.assertIn("unresolved_evidence", step7)
        self.assertIn("candidate_evidence_used", step7)
        self.assertIn("confirmation_status", step7)
        self.assertIn("rollback_if_unconfirmed", step7)

    def test_step7_existing_draft_three_entry_paths_are_explicit(self):
        step7 = read_rel("agents/step_7_writing.md")
        step7_entry = read_rel("agents/step_7_entry.md")
        write_cmd = read_rel("commands/write.md")
        readme = read_rel("README.md")

        for label in ["continue-existing", "chapter-only", "revision-only"]:
            self.assertIn(label, step7)
            self.assertIn(label, step7_entry)
            self.assertIn(label, write_cmd)
            self.assertIn(label, readme)

        self.assertIn("existing-draft 可以跳过前链，但不能跳过证据确认", step7)
        self.assertIn("三者都允许 direct-entry，但都不能跳过证据确认", write_cmd)

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
        self.assertIn("figure_intent", step7)
        self.assertIn("evidence_basis", step7)
        self.assertIn("candidate_specs", step7)
        self.assertIn("human_selected_candidate", step7)
        self.assertIn("figure_risk_note", step7)
        self.assertIn("图表意图与证据约束", step7)
        self.assertIn("图表证据子链", readme)

    def test_step8_light_meaning_audit_trigger_exists(self):
        step8 = read_rel("agents/step_8_polishing.md")

        self.assertIn("meaning_audit_required", step8)
        self.assertIn("meaning_audit_reason", step8)
        self.assertIn("轻量含义审计触发", step8)
        self.assertIn("claim、引用、限定词、比较词", step8)
        self.assertIn("不把普通润色升级成重审稿", step8)
        self.assertIn("转人工复核", step8)


if __name__ == "__main__":
    unittest.main()
