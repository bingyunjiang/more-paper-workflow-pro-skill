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


if __name__ == "__main__":
    unittest.main()
