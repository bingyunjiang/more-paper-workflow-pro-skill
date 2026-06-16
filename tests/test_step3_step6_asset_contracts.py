from pathlib import Path
import json
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read_rel(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class Step3Step6AssetContractsTest(unittest.TestCase):
    def test_step_agent_heading_numbers_are_step_local_and_one_based(self):
        for path in sorted((ROOT / "agents").glob("step_*.md")):
            text = path.read_text(encoding="utf-8").splitlines()
            match = re.search(r"step_(\d+)", path.name)
            self.assertIsNotNone(match, path.name)
            step = match.group(1)
            in_fence = False
            for line_no, line in enumerate(text, start=1):
                stripped = line.strip()
                if stripped.startswith("```") or stripped.startswith("````"):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                self.assertIsNone(
                    re.match(r"^##\s+\d+\.", line),
                    f"{path}:{line_no} uses numbered template heading: {line}",
                )
                self.assertIsNone(
                    re.match(rf"^###{{1,2}}\s+{step}\.0\b", line),
                    f"{path}:{line_no} uses zero-based Step subheading: {line}",
                )
                numbered = re.match(r"^###(?!#)|^####", line)
                if numbered:
                    local = re.match(r"^#{3,4}\s+([1-8])\.", line)
                    if local:
                        self.assertEqual(
                            local.group(1),
                            step,
                            f"{path}:{line_no} uses nonlocal Step heading: {line}",
                        )

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

    def test_step6_mineru_zip_and_zotero_non_hard_dependency_contract_exists(self):
        step6 = read_rel("agents/step_6_zotero.md")
        for token in [
            "Zotero 是 Step 7 的推荐资产管理层，不是唯一写作入口",
            "evidence_pack",
            "attachment_role",
            "`pdf`",
            "`mineru_zip`",
            "`supplement`",
            "可选增强提示",
            "llm-for-zotero",
            "建议在 Zotero 中安装",
            "不构成入口门槛",
            "LLM-for-Zotero-MinerU-cache-*.zip",
            "parentItemKey",
            "attachmentKey",
            "sourceFilename",
        ]:
            self.assertIn(token, step6)

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
            "4.4 筛选依据确认",
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

        self.assertLess(step4.index("4.4 筛选依据确认"), step4.index("4.5 五维评分"))
        self.assertLess(step4.index("4.5 五维评分"), step4.index("4.6 Tier 分级"))
        self.assertLess(step4.index("4.6 Tier 分级"), step4.index("4.7 引文扩展"))
        self.assertLess(step4.index("4.7 引文扩展"), step4.index("4.8 饱和度估算"))
        self.assertLess(step4.index("4.8 饱和度估算"), step4.index("4.9 报告生成与完成检查"))

    def test_step4_output_contract_separates_core_and_conditional_artifacts(self):
        step4 = read_rel("agents/step_4_search_score.md")

        for token in [
            "核心交付物",
            "条件性交付物",
            "workflow_search_results.json",
            "retrieval_index_manifest.json",
            "saturation_snapshot.json",
            "中文论文元数据.json",
            "文件存在性和字段完整性由 4.9.5 统一处理",
        ]:
            self.assertIn(token, step4)

        self.assertNotIn("7 件套强制交付", step4)
        self.assertNotIn("5 个文件 + 1 个饱和度快照 + 1 个中文 JSON", step4)
        self.assertNotIn("以下 **6 个交付物**", step4)

    def test_step4_step6_heading_number_order_contract(self):
        step4 = read_rel("agents/step_4_search_score.md")
        step6 = read_rel("agents/step_6_zotero.md")
        readme = read_rel("README.md")

        step4_order = [
            "### 4.1. 检索执行总览",
            "### 4.1.1. 阶段输入输出表",
            "### 4.1.2. 防截断与机器工件完整性",
            "### 4.1.3. 英文源执行规则",
            "### 4.1.4. 中文源 preflight",
            "### 4.1.5. L2 Crossref",
            "### 4.1.6. L1 CNKI",
            "### 4.1.7. L2 Wanfang Data",
            "### 4.1.8. Tier-driven 检索参数",
            "### 4.1.9. L2 arXiv 条件触发",
            "### 4.2. 文献可信度三态机制",
            "### 4.2.1. 引文验证执行细则",
            "### 4.3. DOI 去重",
            "### 4.4. 筛选依据确认",
            "### 4.5. 相关性评分",
            "### 4.6. 筛选标准",
            "### 4.7. 引文网络扩展",
            "### 4.8. 饱和度曲线估算",
            "### 4.9. 报告生成",
        ]
        last = -1
        for token in step4_order:
            pos = step4.index(token)
            self.assertGreater(pos, last, token)
            last = pos
        self.assertNotIn("4.0.1a", step4)

        step6_order = [
            "### 6.1.",
            "### 6.2.",
            "### 6.3.",
            "### 6.4.",
            "### 6.5.",
            "### 6.6.",
        ]
        last = -1
        for token in step6_order:
            pos = step6.index(token)
            self.assertGreater(pos, last, token)
            last = pos
        self.assertIn("#### 6.6: 生成能力索引", readme)
        self.assertIn("#### 6.6: Generate Capability Index", readme)

    def test_step4_step6_antitruncation_contract_exists(self):
        step4 = read_rel("agents/step_4_search_score.md")
        step6 = read_rel("agents/step_6_zotero.md")
        skill = read_rel("SKILL.md")

        for token in [
            "防截断与机器工件完整性",
            "机器主工件禁止截断",
            "workflow_search_results.json",
            "文献库.bib",
            "中文论文元数据.json",
            "retrieval_index_manifest.json",
            "不得从已截断的 Markdown/XLSX/PDF 展示行反向生成",
            "展示层可截断但必须可回查",
            "source_integrity=display_truncated",
            "禁止从已截断的 `检索文献表.md/.xlsx` 或 `检索报告.md/.pdf`",
            "`record_id`",
            "`citekey`",
            "`source_id`",
            "`DOI`",
            "`article_url`",
        ]:
            self.assertIn(token, step4)

        for token in [
            "所有用于机器执行的字段禁止截断",
            "Markdown 中的截断不得反向污染 JSON",
            "`record_id`",
            "`citekey`",
            "`source_id`",
            "`DOI`",
            "`article_url`",
            "`zotero_item_key`",
        ]:
            self.assertIn(token, step6)

        self.assertIn("防截断原则", skill)
        self.assertIn("机器工件禁止截断", skill)
        self.assertIn("Markdown/XLSX/PDF 仅作为展示层可截断", skill)

    def test_build_zotero_plan_keeps_json_full_text_while_review_can_truncate(self):
        long_title = "A" * 140 + " 完整标题尾部"
        long_abstract = "B" * 220 + " 完整摘要尾部"

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bib = tmp_path / "文献库.bib"
            output_json = tmp_path / "文献-Zotero架构对照.json"
            review_md = tmp_path / "文献-Zotero架构对照.md"
            pdf_index = tmp_path / "pdf-附件池索引.json"

            bib.write_text(
                "@article{long2026,\n"
                f"  title = {{{long_title}}},\n"
                "  author = {Zhang, San},\n"
                "  year = {2026},\n"
                "  journal = {Journal of Full Fields},\n"
                f"  abstract = {{{long_abstract}}},\n"
                "  doi = {10.1234/full-fields},\n"
                "  note = {tier=T1; score=23; subtopic=S1; verification_status=VERIFIED}\n"
                "}\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "python3",
                    str(ROOT / "scripts/build_zotero_plan.py"),
                    "--bib",
                    str(bib),
                    "--output",
                    str(output_json),
                    "--review",
                    str(review_md),
                    "--pdf-index",
                    str(pdf_index),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertIn(result.returncode, {0, 2}, result.stderr + result.stdout)

            plan = json.loads(output_json.read_text(encoding="utf-8"))
            record = plan["records"][0]
            self.assertEqual(record["title"], long_title)
            self.assertEqual(record["abstract"], long_abstract)
            self.assertEqual(record["doi"], "10.1234/full-fields")

            review = review_md.read_text(encoding="utf-8")
            self.assertIn("long2026", review)
            self.assertIn("…", review)
            self.assertNotIn("完整标题尾部", review)

    def test_step4_public_summaries_match_new_screening_sequence(self):
        skill = read_rel("SKILL.md")
        readme = read_rel("README.md")
        readme_current = readme.split("## 📋 版本历史", 1)[0]
        architecture = read_rel("docs/workflow-architecture.md")

        for text in [skill, readme_current]:
            self.assertIn("4.4 筛选依据", text)
            self.assertIn("4.5 五维", text)
            self.assertIn("4.6 T1-T4", text)
            self.assertIn("4.7 引文扩展", text)
            self.assertIn("4.8 饱和", text)
            self.assertIn("4.9", text)

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
