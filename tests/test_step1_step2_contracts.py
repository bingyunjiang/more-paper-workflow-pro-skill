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
        for token in [
            "发散层 / 收敛层",
            "当前轮的执行范围",
            "候选池",
            "侧边聊天",
            "候选池内容记录",
            "不锁死研究想象",
        ]:
            self.assertIn(token, step1)

    def test_step2_declares_unique_outline_generation_boundary(self):
        step2 = read_rel("agents/step_2_outline.md")
        self.assertIn("Step 1 负责问题结构收敛，但不压死研究发散", step2)
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

    def test_step23_keeps_existing_outline_as_primary(self):
        step2 = read_rel("agents/step_2_outline.md")
        self.assertIn("Step 1 始终只是**约束源**", step2)
        self.assertIn("不得因为存在结构化 Step 1 输出就跳过已有大纲直接改走 `2.2`", step2)
        self.assertIn("primary_rq", step2)
        self.assertIn("scope_boundaries", step2)
        self.assertIn("fatal_risks", step2)

    def test_step2_distinguishes_material_roles_for_existing_inputs(self):
        step2 = read_rel("agents/step_2_outline.md")
        for token in [
            "资料角色路由表",
            "结构源",
            "内容源",
            "工程约束源",
            "混合资料包",
            "只抽取结构、关键词、证据需求和缺口；正文改写交给 Step 7/8",
            "保密边界、数据是否已验证、哪些内容可写成论文 claim",
            "候选任务 / 备选论证区",
            "候选任务区只用于保留发散结果和后续切换空间",
            "只收口当前轮的执行范围",
        ]:
            self.assertIn(token, step2)

    def test_step2_interaction_trigger_is_general_and_risk_based(self):
        step2 = read_rel("agents/step_2_outline.md")
        for token in [
            "#### 2.1.1. 大纲优化交互触发判定",
            "Step 2 要覆盖全部已有资料入口的交互判定，但不是所有优化都需要询问用户",
            "自动处理",
            "轻量确认",
            "必须确认",
            "术语规范、格式整理、关键词补齐、章节证据需求表",
            "是否保留原大纲为主",
            "改变研究对象、贡献点、论文类型、核心方法路线",
            "使用工程敏感内容",
            "混合资料出现优先级冲突",
            "资料清点、反推主题、风险标注、初步评审和待确认版建议不需要等待确认",
            "确认状态必须写入 `大纲评审报告.md` 或 `大纲关键词.md`",
            "发散模式的目标是扩大候选池，不是提前替代定题",
        ]:
            self.assertIn(token, step2)

    def test_step25_requires_soft_engineering_context_confirmation(self):
        step2 = read_rel("agents/step_2_outline.md")
        for token in [
            "CP-ENGINEERING-CONTEXT",
            "默认 soft checkpoint",
            "工程对象/系统边界",
            "不可披露或需脱敏内容",
            "未确认内容清单",
            "不把工程文档中的未验证结论直接写成论文 claim",
            "未确认工程内容未被写成论文 claim",
        ]:
            self.assertIn(token, step2)

    def test_step2_uses_decimal_stage_numbering(self):
        step2 = read_rel("agents/step_2_outline.md")
        for token in [
            "### 2.1. 入口路由判定",
            "### 2.2. 标准大纲生成",
            "### 2.3. 大纲评审",
            "### 2.4. 已有大纲评估与优化模式",
            "### 2.5. 基于工程文档的大纲优化",
            "### 2.6. 术语映射表生成",
            "### 2.7. Step 3/6/7 交接",
        ]:
            self.assertIn(token, step2)
        for old_token in [
            "### 2.0.",
            "#### 2.0.",
            "### 2-0.",
            "### 2a.",
            "### 2b.",
            "### 2c.",
            "### 2d.",
            "### 2e.",
            "### 2f.",
            "#### 2d-0.",
        ]:
            self.assertNotIn(old_token, step2)


if __name__ == "__main__":
    unittest.main()
