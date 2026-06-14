from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read_rel(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class Step3Step6AssetContractsTest(unittest.TestCase):
    def test_step6_capability_index_contract_exists(self):
        step6 = read_rel("agents/step_6_zotero.md")
        command = read_rel("commands/zotero.md")
        architecture = read_rel("docs/workflow-architecture.md")

        for token in [
            "capability_index.json",
            "capability_index.md",
            "asset_summary",
            "capabilities",
            "recommended_entry_points",
            "blocking_gaps",
            "source_artifact",
            "supports_steps",
            "supports_actions",
            "evidence_boundary",
        ]:
            self.assertIn(token, step6)

        self.assertIn("不是新的流程锁", step6)
        self.assertIn("不替代 `文献-Zotero架构对照.json`", step6)
        self.assertIn("不允许把摘要、候选召回或 PDF 文件名匹配直接升级为正文证据", step6)
        self.assertIn("capability_index.json/md", command)
        self.assertIn("capability_index.json/md", architecture)

    def test_step3_step4_retrieval_index_manifest_reuse_contract_exists(self):
        step3 = read_rel("agents/step_3_search_plan.md")
        step4 = read_rel("agents/step_4_search_score.md")

        for text in [step3, step4]:
            self.assertIn("retrieval_index_manifest.json", text)
            self.assertIn("retrieval-index.v1", text)
            self.assertIn("source_artifacts", text)
            self.assertIn("search_task_ids", text)
            self.assertIn("reusable_for", text)
            self.assertIn("authority", text)
            self.assertIn("rebuild_triggers", text)
            self.assertIn("不直接进入正文", text)
            self.assertIn("不替代", text)

        self.assertIn("不触发全文 RAG", step3)
        self.assertIn("不能把检索命中、摘要、metadata cache 或候选 chunk 直接升级为正文证据", step4)
        self.assertIn("Step 6 capability index", step4)

    def test_step4_screening_basis_is_user_visible_before_scoring(self):
        step4 = read_rel("agents/step_4_search_score.md")

        for token in [
            "4.3 筛选依据确认",
            "CP-SCREENING-BASIS",
            "筛选依据来源",
            "默认评分维度",
            "默认 Tier 阈值",
            "向用户展示评分维度、权重、阈值和排除规则",
            "用户确认或调整后的筛选依据",
            "正式评分和剔除前",
            "确认使用默认筛选依据",
            "调整权重、阈值、年份范围、语言范围或排除规则",
            "暂不剔除，只生成候选清单和风险说明",
            "筛选依据必须写入 `检索文献表.md` 顶部",
            "不得声称已经完成最终 T1-T3 文献库",
        ]:
            self.assertIn(token, step4)

        self.assertLess(step4.index("4.3 筛选依据确认"), step4.index("4.4 五维评分"))
        self.assertLess(step4.index("4.4 五维评分"), step4.index("4.5 Tier 分级"))
        self.assertLess(step4.index("4.5 Tier 分级"), step4.index("4.6 引文扩展"))
        self.assertLess(step4.index("4.6 引文扩展"), step4.index("4.7 饱和度估算"))
        self.assertLess(step4.index("4.7 饱和度估算"), step4.index("4.8 报告生成与完成检查"))

    def test_step4_output_contract_separates_core_and_conditional_artifacts(self):
        step4 = read_rel("agents/step_4_search_score.md")

        for token in [
            "核心交付物",
            "条件性交付物",
            "workflow_search_results.json",
            "retrieval_index_manifest.json",
            "saturation_snapshot.json",
            "中文论文元数据.json",
            "文件存在性和字段完整性由 4.8.5 统一处理",
        ]:
            self.assertIn(token, step4)

        self.assertNotIn("7 件套强制交付", step4)
        self.assertNotIn("5 个文件 + 1 个饱和度快照 + 1 个中文 JSON", step4)
        self.assertNotIn("以下 **6 个交付物**", step4)

    def test_step4_public_summaries_match_new_screening_sequence(self):
        skill = read_rel("SKILL.md")
        readme = read_rel("README.md")
        readme_current = readme.split("## 📋 版本历史", 1)[0]
        architecture = read_rel("docs/workflow-architecture.md")

        for text in [skill, readme_current]:
            self.assertIn("4.3 筛选依据", text)
            self.assertIn("4.4 五维", text)
            self.assertIn("4.5 T1-T4", text)
            self.assertIn("4.6 引文扩展", text)
            self.assertIn("4.7 饱和", text)
            self.assertIn("4.8", text)

        self.assertIn("核心交付", architecture)
        self.assertIn("条件交付", architecture)
        self.assertIn("workflow_search_results.json", architecture)
        self.assertIn("retrieval_index_manifest.json", architecture)
        self.assertNotIn("7 件套", architecture)
        self.assertNotIn("4c 五维评分 → 4d T1-T4", readme_current)
        self.assertNotIn("4c 相关性评分", skill)
        self.assertNotIn("4c 筛选依据", skill)
        self.assertNotIn("4a→4h", readme_current)
        self.assertNotIn("7 件套检索报告", skill)

    def test_step1_step2_are_not_changed_by_asset_contract_round(self):
        step1 = read_rel("agents/step_1_topic.md")
        step2 = read_rel("agents/step_2_outline.md")

        self.assertNotIn("capability_index", step1)
        self.assertNotIn("capability_index", step2)
        self.assertNotIn("retrieval_index_manifest", step1)
        self.assertNotIn("retrieval_index_manifest", step2)


if __name__ == "__main__":
    unittest.main()
