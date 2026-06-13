from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read_rel(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class Step1Step2ContractsTest(unittest.TestCase):
    def test_step1_outputs_problem_structure_not_outline(self):
        step1 = read_rel("agents/step_1_topic.md")
        self.assertIn("Step 1 只生成问题结构，不生成章节结构", step1)
        for token in [
            "research_intent_type",
            "research_question_candidates",
            "primary_rq",
            "secondary_rqs",
            "scope_boundaries",
            "methodology_blueprint",
            "devils_advocate_challenge",
        ]:
            self.assertIn(token, step1)

    def test_step2_declares_unique_outline_generation_boundary(self):
        step2 = read_rel("agents/step_2_outline.md")
        self.assertIn("Step 2 是完整研究大纲 / 论文大纲的唯一生成层", step2)
        self.assertIn("Step 1 提供问题结构，Step 2 负责把问题结构展开为完整论文结构", step2)

    def test_step2_reads_step1_structured_fields(self):
        step2 = read_rel("agents/step_2_outline.md")
        for token in [
            "primary_rq",
            "secondary_rqs",
            "scope_boundaries",
            "research_intent_type",
            "methodology_blueprint",
        ]:
            self.assertIn(token, step2)

    def test_step2c_keeps_existing_outline_as_primary(self):
        step2 = read_rel("agents/step_2_outline.md")
        self.assertIn("Step 1 始终只是**约束源**", step2)
        self.assertIn("不得因为存在结构化 Step 1 输出就跳过已有大纲直接改走 `2a`", step2)
        self.assertIn("primary_rq", step2)
        self.assertIn("scope_boundaries", step2)
        self.assertIn("fatal_risks", step2)


if __name__ == "__main__":
    unittest.main()
